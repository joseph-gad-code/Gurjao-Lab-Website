import requests
import yaml
import time
from urllib.parse import quote_plus
from pathlib import Path

# --- Config ---
SERPAPI_KEY = "YOUR_SERPAPI_KEY"
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


def normalize_author(name):
    """Abbreviate author name (e.g. 'John D. Smith' -> 'J.D. Smith')."""
    parts = name.replace(",", "").split()
    if len(parts) == 0:
        return name
    last = parts[-1]
    initials = "".join([p[0] + "." for p in parts[:-1]])
    return f"{initials} {last}".strip()


def extract_from_crossref(msg):
    """Extract key metadata fields."""
    if not msg:
        return {}
    year = None
    for k in ("published-print", "published-online", "issued"):
        dp = ((msg.get(k) or {}).get("date-parts") or [[]])
        if dp and dp[0]:
            year = dp[0][0]
            break
    return {
        "journal": (msg.get("container-title") or [""])[0],
        "volume": msg.get("volume") or "",
        "issue": msg.get("issue") or "",
        "pages": msg.get("page") or "",
        "year": year,
        "url": msg.get("URL") or "",
        "doi": msg.get("DOI") or "",
        "authors": [normalize_author(a.get("given", "") + " " + a.get("family", "")) 
                    for a in msg.get("author", []) if a.get("family")],
    }


def enrich_with_crossref(pub):
    """Enrich publication with Crossref data."""
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

    # Update only empty fields
    for k, v in meta.items():
        if v and (k not in out or not out[k]):
            out[k] = v

    # Filter: keep only if "Gurjao" appears in Crossref author list
    if not any("Gurjao" in a for a in out.get("authors", [])):
        return None

    return out


def get_scholar_publications():
    """Fetch all publications for given author from Google Scholar."""
    url = f"https://serpapi.com/search.json?engine=google_scholar_author&author_id={SCHOLAR_AUTHOR_ID}&api_key={SERPAPI_KEY}"
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    pubs = []
    for item in data.get("articles", []):
        pubs.append({
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "doi": item.get("publication_info", {}).get("doi", ""),
            "authors": [normalize_author(a.strip()) for a in item.get("authors", "").split(",")],
            "selected_publication": "no",
            "image": "",
        })
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

    all_pubs = existing + new_pubs
    with open(DATA_FILE, "w") as f:
        yaml.dump(all_pubs, f, sort_keys=False, allow_unicode=True)


if __name__ == "__main__":
    update_publications()
