import os
import requests
import yaml
import time
import unicodedata
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


# --- Helpers ---
def normalize_name(s):
    """Normalize Unicode and lowercase for comparison (handles Gurjão → Gurjao)."""
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("utf-8").lower()


def crossref_get(doi):
    """Fetch one Crossref record by DOI."""
    if not doi:
        return {}
    try:
        r = requests.get(CROSSREF_BASE + doi, timeout=20)
        r.raise_for_status()
        return r.json().get("message", {}) or {}
    except Exception as e:
        print(f"Crossref DOI fetch failed for {doi}: {e}")
        return {}


def crossref_search_title(title):
    """Fallback Crossref search by title, using fuzzy matching."""
    if not title:
        return {}
    try:
        url = f"https://api.crossref.org/works?query.title={quote_plus(title)}&rows=3"
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        items = (r.json().get("message", {}).get("items", []) or [])
        if not items:
            return {}

        title_norm = normalize_name(title)
        for it in items:
            cand_title = normalize_name(it.get("title", [""])[0])
            if title_norm.split(":")[0] in cand_title or cand_title in title_norm:
                return it
        return items[0]
    except Exception as e:
        print(f"Crossref title search failed for {title}: {e}")
        return {}


def extract_from_crossref(msg):
    """Extract key metadata fields (including full author list)."""
    if not msg:
        return {}

    # Determine publication year
    year = None
    for k in ("published-print", "published-online", "issued"):
        dp = ((msg.get(k) or {}).get("date-parts") or [[]])
        if dp and dp[0]:
            year = dp[0][0]
            break

    # Extract all authors
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
    """Enrich publication with Crossref data while preserving title and URL."""
    out = dict(pub)
    msg = {}
    doi = out.get("doi", "").strip()
    title = out.get("title", "").strip()

    # Try DOI first, then title fallback
    if doi:
        msg = crossref_get(doi)
        time.sleep(REQUEST_PAUSE)
    if not msg and title:
        msg = crossref_search_title(title)
        time.sleep(REQUEST_PAUSE)

    meta = extract_from_crossref(msg)
    if not meta:
        print(f"No Crossref match for: {title}")
        return out

    # Keep Scholar title and URL
    meta["title"] = out.get("title", "")
    meta["url"] = out.get("url", meta.get("url", ""))

    # Merge metadata
    out.update(meta)

    # Keep all, but flag if Gurjao not found
    authors = out.get("authors", [])
    if authors and not any("gurjao" in normalize_name(a) for a in authors):
        print(f"'Gurjao' not found in Crossref author list for: {out['title']}")

    return out


def get_scholar_publications():
    """Fetch all publications for given author from Google Scholar via SerpApi."""
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

        print("Loading next page of Scholar results...")
        time.sleep(REQUEST_PAUSE)

    print(f"Total publications fetched from Scholar: {len(pubs)}")
    return pubs


def update_publications():
    """Main function to merge and enrich publication data."""
    # Load existing publications
    existing = []
    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as f:
            existing = yaml.safe_load(f) or []
