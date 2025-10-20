#!/usr/bin/env python3
"""
Fetch all publications from Carino Gurjao's Google Scholar profile via SerpAPI,
enrich them with Crossref metadata, and save to _data/publications.yml.
"""

import os
import time
import requests
import yaml
from urllib.parse import quote_plus

# === CONFIG ===
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")
if not SERPAPI_KEY:
    raise RuntimeError("Missing SERPAPI_API_KEY environment variable")

CROSSREF_BASE = "https://api.crossref.org/works/"
SERPAPI_BASE = "https://serpapi.com/search.json"
REQUEST_PAUSE = 0.4  # polite delay to avoid hitting rate limits
OUTPUT_PATH = "_data/publications.yml"

# Carino Gurjao’s Google Scholar author ID
AUTHOR_ID = "m3rLfS4AAAAJ"


# --- CROSSREF HELPERS ---------------------------------------------------------
def crossref_get(doi: str) -> dict:
    """Fetch a Crossref record by DOI."""
    if not doi:
        return {}
    try:
        r = requests.get(CROSSREF_BASE + doi, timeout=20)
        r.raise_for_status()
        data = r.json()
        return data.get("message", {}) or {}
    except Exception:
        return {}


def crossref_search_title(title: str) -> dict:
    """Search Crossref by title if no DOI is available."""
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


def extract_from_crossref(msg: dict) -> dict:
    """Normalize Crossref metadata into simple fields."""
    if not msg:
        return {}

    year = None
    for k in ("published-print", "published-online", "issued"):
        dp = ((msg.get(k) or {}).get("date-parts") or [[]])
        if dp and dp[0]:
            y = dp[0][0]
            if isinstance(y, int):
                year = y
                break

    return {
        "journal": (msg.get("container-title") or [""])[0],
        "volume": msg.get("volume") or "",
        "issue": msg.get("issue") or "",
        "pages": msg.get("page") or "",
        "year": year,
        "url": msg.get("URL") or "",
        "doi": msg.get("DOI") or "",
    }


def enrich_with_crossref(pub: dict) -> dict:
    """Merge missing metadata from Crossref into the publication record."""
    out = dict(pub)
    msg = {}

    doi = (out.get("doi") or "").strip()
    if doi:
        time.sleep(REQUEST_PAUSE)
        msg = crossref_get(doi)
    if not msg:
        title = out.get("title", "").strip()
        if title:
            time.sleep(REQUEST_PAUSE)
            msg = crossref_search_title(title)

    meta = extract_from_crossref(msg)
    if not meta:
        return out

    def set_if_empty(key, val):
        if val and not out.get(key):
            out[key] = val

    set_if_empty("journal", meta.get("journal"))
    if meta.get("journal") and not out.get("venue"):
        out["venue"] = meta["journal"]
    set_if_empty("volume", meta.get("volume"))
    set_if_empty("issue", meta.get("issue"))
    set_if_empty("pages", meta.get("pages"))
    set_if_empty("year", meta.get("year"))
    set_if_empty("url", meta.get("url"))
    set_if_empty("doi", meta.get("doi"))

    return out


# --- GOOGLE SCHOLAR AUTHOR (via SerpAPI) -------------------------------------
def fetch_all_scholar_pubs(author_id: str) -> list:
    """
    Fetch all publications from a Google Scholar author profile.
    Automatically follows pagination using SerpAPI's next page token.
    """
    all_pubs = []
    next_token = None
    page = 1

    while True:
        params = {
            "engine": "google_scholar_author",
            "author_id": author_id,
            "api_key": SERPAPI_KEY,
        }
        if next_token:
            params["after_author"] = next_token

        print(f"Fetching page {page} from Google Scholar...")
        try:
            r = requests.get(SERPAPI_BASE, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"Error fetching from SerpAPI: {e}")
            break

        publications = data.get("articles", []) or []
        for pub in publications:
            title = pub.get("title", "")
            link = pub.get("link", "")
            year = pub.get("year")
            authors = pub.get("authors", "")
            if isinstance(authors, str):
                authors = [a.strip() for a in authors.split(",")]
            doi = ""
            if "doi.org" in link:
                doi = link.split("doi.org/")[-1]

            all_pubs.append({
                "title": title.strip(),
                "url": link.strip(),
                "authors": authors,
                "year": year,
                "doi": doi,
            })

        next_token = data.get("serpapi_pagination", {}).get("next_page_token")
        if not next_token:
            break
        page += 1
        time.sleep(1.5)  # be polite

    print(f"Fetched {len(all_pubs)} total publications from Google Scholar.")
    return all_pubs


# --- MAIN PIPELINE ------------------------------------------------------------
def scholar_to_crossref(author_id: str) -> list:
    """Fetch and enrich all publications for the given author."""
    articles = fetch_all_scholar_pubs(author_id)
    enriched = []
    for pub in articles:
        enriched_pub = enrich_with_crossref(pub)
        enriched.append(enriched_pub)
    print(f"Enriched {len(enriched)} publications with Crossref metadata.")
    return enriched


def save_yaml(records: list, path: str):
    """Save publication data to YAML file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(records, f, sort_keys=False, allow_unicode=True)
    print(f"Saved {len(records)} entries → {path}")


# --- EXECUTION ----------------------------------------------------------------
if __name__ == "__main__":
    pubs = scholar_to_crossref(AUTHOR_ID)
    save_yaml(pubs, OUTPUT_PATH)
