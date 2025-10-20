import os
import requests
import yaml
import time
import unicodedata
from urllib.parse import quote_plus
from pathlib import Path

# --- Configuration ---
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")
if not SERPAPI_KEY:
    raise RuntimeError("Missing SERPAPI_API_KEY environment variable.")

SCHOLAR_AUTHOR_ID = "m3rLfS4AAAAJ"
CROSSREF_BASE = "https://api.crossref.org/works/"
DATA_FILE = Path("_data/publications.yml")
REQUEST_PAUSE = 0.4


# --- Utility functions ---
def normalize_text(s):
    """Normalize Unicode and lowercase for comparison."""
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode("utf-8").lower()


def crossref_get(doi):
    """Fetch one Crossref record by DOI."""
    if not doi:
        return {}
    try:
        url = CROSSREF_BASE + doi
        print(f"🔍 Crossref DOI lookup: {url}")
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        return r.json().get("message", {}) or {}
    except Exception as e:
        print(f"⚠️ Crossref DOI fetch failed for {doi}: {e}")
        return {}


def crossref_search_title(title):
    """Search Crossref by title only (simple fallback)."""
    if not title:
        return {}
    try:
        url = f"https://api.crossref.org/works?query.title={quote_plus(title)}&rows=3"
        print(f"🔍 Crossref title search: {url}")
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        items = (r.json().get("message", {}).get("items", []) or [])
        if not items:
            return {}

        title_norm = normalize_text(title)
        for it in items:
            cand_title = normalize_text(it.get("title", [""])[0])
            if title_norm.split(":")[0] in cand_title or cand_title in title_norm:
                return it
        return items[0]
    except Exception as e:
        print(f"⚠️ Crossref title search failed for {title}: {e}")
        return {}


def crossref_search_scholar_metadata(pub):
    """Search Crossref using richer metadata from Google Scholar (title + author + journal + year)."""
    title = pub.get("title", "")
    journal = pub.get("journal", "")
    year = str(pub.get("year", "")) if pub.get("year") else ""
    first_author = pub.get("authors", [None])[0] or ""

    # Build composite query
    query = " ".join(filter(None, [title, first_author, journal, year]))
    url = f"https://api.crossref.org/works?query.bibliographic={quote_plus(query)}&rows=5"
    print(f"🔍 Crossref metadata search: {url}")

    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        items = (r.json().get("message", {}).get("items", []) or [])
        if not items:
            return {}

        title_norm = normalize_text(title)
        for it in items:
            cand_title = normalize_text(it.get("title", [""])[0])
            if title_norm.split(":")[0] in cand_title or cand_title in title_norm:
                return it
        return items[0]
    except Exception as e:
        print(f"⚠️ Crossref metadata search failed for {title}: {e}")
        return {}


def extract_from_crossref(msg):
    """Extract key metadata fields from a Crossref record."""
    if not msg:
        return {}

    # Determine publication year
    year = None
    for k in ("published-print", "published-online", "issued"):
        dp = ((msg.get(k) or {}).get("date-parts") or [[]])
        if dp and dp[0]:
            year = dp[0][0]
            break

    # Collect authors
    authors = []
    for a in msg.get("author", []):
        given = a.get("given", "").strip()
        family = a.get("family", "").strip()
        full = " ".join([given, family]).strip()
        if full:
            authors.append(full)

    return {
        "journal": (msg.get("container-title") or [""])[0],
        "volume": msg.get("volume") or "",
        "issue": msg.get("issue") or "",
        "pages": msg.get("page") or "",
        "year": year,
        "url": msg.get("URL") or "",
        "doi": msg.get("DOI") or "",
        "authors": authors,
    }


def enrich_with_crossref(pub):
    """Enrich a publication record with Crossref metadata."""
    out = dict(pub)
    doi = out.get("doi", "").strip()
    title = out.get("title", "").strip()
    msg = {}

    # Step 1: DOI lookup
    if doi:
        msg = crossref_get(doi)
        time.sleep(REQUEST_PAUSE)

    # Step 2: Title search fallback
    if not msg and title:
        msg = crossref_search_title(title)
        time.sleep(REQUEST_PAUSE)

    # Step 3: Metadata-based search fallback
    if not msg:
        msg = crossref_search_scholar_metadata(out)
        time.sleep(REQUEST_PAUSE)

    meta = extract_from_crossref(msg)
    if not meta:
        print(f"⚠️ No Crossref match found for: {title}")
        return out

    # Preserve Google Scholar fields
    meta["title"] = out.get("title", "")
    meta["url"] = out.get("url", meta.get("url", ""))

    out.update(meta)

    # Warn if Gurjão/Gurjao not found
    authors = out.get("authors", [])
    if authors and not any("gurjao" in normalize_text(a) for a in authors):
        print(f"⚠️ 'Gurjao' not found in Crossref author list for: {out['title']}")

    return out


def get_scholar_publications():
    """Retrieve all Google Scholar publications for a given author (paginated)."""
    pubs = []
    after_token = None

    while True:
        url = (
            f"https://serpapi.com/search.json?"
            f"engine=google_scholar_author&author_id={SCHOLAR_AUTHOR_ID}&api_key={SERPAPI_KEY}"
        )
        if after_token:
            url += f"&after_author={quote_plus(after_token)}"

        r = requests.get(url)
        r.raise_for_status()
        data = r.json()

        for item in data.get("articles", []):
            pubs.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "doi": item.get("publication_info", {}).get("doi", ""),
                "journal": item.get("publication", ""),
                "authors": [],
                "selected_publication": "no",
                "image": "",
            })

        after_token = data.get("serpapi_pagination", {}).get("next", "")
        if not after_token:
            break

        print("🔄 Loading next page of Google Scholar results...")
        time.sleep(REQUEST_PAUSE)

    print(f"✅ Total publications fetched from Scholar: {len(pubs)}")
    return pubs


def update_publications():
    """Main routine: merge and enrich publication data."""
    # Load existing YAML file
    existing = []
    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as f:
            existing = yaml.safe_load(f) or []

    titles_existing = {p["title"] for p in existing if "title" in p}
    new_pubs = []

    for pub in get_scholar_publications():
        if pub["title"] in titles_existing:
            print(f"⏩ Skipping existing: {pub['title']}")
            continue
        enriched = enrich_with_crossref(pub)
        if enriched:
            print(f"✅ Added: {enriched['title']}")
            new_pubs.append(enriched)
        else:
            print(f"⚠️ Could not enrich: {pub['title']}")

    all_pubs = existing + new_pubs
    with open(DATA_FILE, "w") as f:
        yaml.dump(all_pubs, f, sort_keys=False, allow_unicode=True)

    print(f"\n✅ Updated publications file with {len(new_pubs)} new entries.")
    print(f"📁 Total entries now: {len(all_pubs)}")


if __name__ == "__main__":
    update_publications()
