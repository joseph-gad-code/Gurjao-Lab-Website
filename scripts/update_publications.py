import os
import requests
import yaml
import time
from urllib.parse import quote_plus
from pathlib import Path

# --- Config ---
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")
if not SERPAPI_KEY:
    raise RuntimeError("Missing SERPAPI_API_KEY environment variable.")

SCHOLAR_AUTHOR_ID = "m3rLfS4AAAAJ"
CROSSREF_BASE = "https://api.crossref.org/works/"
DATA_FILE = Path("_data/publications.yml")
REQUEST_PAUSE = 0.4


def crossref_get(doi):
    """Fetch one Crossref record by DOI."""
    if not doi:
        return {}
    try:
        r = requests.get(CROSSREF_BASE + doi, timeout=20)
        r.raise_for_status()
        return r.json().get("message", {}) or {}
    except Exception:
        return {}


def crossref_search_title(title):
    """Fallback Crossref search by title."""
    if not title:
        return {}
    try:
        url = f"https://api.crossref.org/works?query.bibliographic={quote_plus(title)}&rows=1"
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        items = (r.json().get("message", {}).get("items", []) or [])
        return items[0] if items else {}
    except Exception:
        return {}


def extract_from_crossref(msg):
    """Extract key metadata fields (full author list included)."""
    if not msg:
        return {}

    # Determine publication year
    year = None
    for k in ("published-print", "published-online", "issued"):
        dp = ((msg.get(k) or {}).get("date-parts") or [[]])
        if dp and dp[0]:
            year = dp[0][0]
            break

    # Extract all authors in full format
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
    """Enrich publication with Crossref data, preserving Scholar journal/title."""
    out = dict(pub)
    msg = {}
    doi = out.get("doi", "").strip()
    title = out.get("title", "").strip()

    if doi:
        msg = crossref_get(doi)
        time.sleep(REQUEST_PAUSE)
    if not msg and title:
        msg = crossref_search_title(title)
        time.sleep(REQUEST_PAUSE)

    meta = extract_from_crossref(msg)
    if not meta:
        return out

    # Keep Google Scholar title and URL
    meta["title"] = out.get("title", "")
    meta["url"] = out.get("url", meta.get("url", ""))

    # Merge metadata
    out.update(meta)

    # Filter: keep only if any author name contains 'Gurjao'
    authors = out.get("authors", [])
    if not any("gurjao" in a.lower() for a in authors):
        return None

    return out


def get_scholar_publications():
    """Fetch all publications for the given author from Google Scholar via SerpApi."""
    pubs = []
    next_token = None

    while True:
        url = (
            f"https://serpapi.com/search.json?"
            f"engine=google_scholar_author&author_id={SCHOLAR_AUTHOR_ID}"
            f"&api_key={SERPAPI_KEY}"
        )
        if next_token:
            url += f"&after_author={quote_plus(next_token)}"

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

        next_token = data.get("serpapi_pagination", {}).get("next", "")
        if not next_token:
            break
        time.sleep(REQUEST_PAUSE)

    return pubs


def update_publications():
    """Main function to merge and enrich publication data."""
    # Load existing publications
    existing = []
    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as f:
            existing = yaml.safe_load(f) or []

    titles_existing = {p["title"] for p in existing if "title" in p}
    new_pubs = []

    for pub in get_scholar_publications():
        if pub["title"] in titles_existing:
            print(f"Skipping existing: {pub['title']}")
            continue
        enriched = enrich_with_crossref(pub)
        if enriched:
            print(f"Added: {enriched['title']}")
            new_pubs.append(enriched)
        else:
            print(f"Filtered (no Gurjao): {pub['title']}")

    all_pubs = existing + new_pubs
    with open(DATA_FILE, "w") as f:
        yaml.dump(all_pubs, f, sort_keys=False, allow_unicode=True)


if __name__ == "__main__":
    update_publications()
