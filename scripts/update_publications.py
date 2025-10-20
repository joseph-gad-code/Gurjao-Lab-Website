#!/usr/bin/env python3
"""
Fetch all publication titles from Carino Gurjao's Google Scholar profile via SerpAPI,
then enrich each title exclusively using Crossref metadata.
Save final results to _data/publications.yml.
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

AUTHOR_ID = "m3rLfS4AAAAJ"  # Carino Gurjao
SERPAPI_BASE = "https://serpapi.com/search.json"
CROSSREF_BASE = "https://api.crossref.org/works"
REQUEST_PAUSE = 0.5
OUTPUT_PATH = "_data/publications.yml"


# --- FETCH TITLES FROM GOOGLE SCHOLAR ----------------------------------------
def fetch_titles_from_scholar(author_id: str) -> list[str]:
    """
    Fetch only publication titles from a Google Scholar author profile.
    Uses SerpAPI pagination to get all results.
    """
    titles = []
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

        print(f"Fetching page {page} of Google Scholar titles...")
        try:
            r = requests.get(SERPAPI_BASE, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"Error fetching from SerpAPI: {e}")
            break

        for art in data.get("articles", []):
            title = art.get("title", "").strip()
            if title:
                titles.append(title)

        next_token = data.get("serpapi_pagination", {}).get("next_page_token")
        if not next_token:
            break
        page += 1
        time.sleep(1.5)

    print(f"Fetched {len(titles)} titles from Google Scholar.")
    return titles


# --- CROSSREF METADATA RETRIEVAL --------------------------------------------
def query_crossref_by_title(title: str) -> dict:
    """Search Crossref for metadata given an article title."""
    try:
        url = f"{CROSSREF_BASE}?query.bibliographic={quote_plus(title)}&rows=1"
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        items = (r.json().get("message", {}).get("items", []) or [])
        return items[0] if items else {}
    except Exception as e:
        print(f"Crossref query failed for '{title}': {e}")
        return {}


def normalize_crossref_record(msg: dict, title: str) -> dict:
    """Extract relevant fields from a Crossref record."""
    year = None
    for k in ("published-print", "published-online", "issued"):
        dp = ((msg.get(k) or {}).get("date-parts") or [[]])
        if dp and dp[0]:
            y = dp[0][0]
            if isinstance(y, int):
                year = y
                break

    authors = []
    for a in msg.get("author", []) or []:
        name_parts = []
        if "given" in a:
            name_parts.append(a["given"])
        if "family" in a:
            name_parts.append(a["family"])
        if name_parts:
            authors.append(" ".join(name_parts))

    return {
        "title": title,
        "authors": authors,
        "journal": (msg.get("container-title") or [""])[0],
        "year": year,
        "volume": msg.get("volume", ""),
        "issue": msg.get("issue", ""),
        "pages": msg.get("page", ""),
        "doi": msg.get("DOI", ""),
        "url": msg.get("URL", ""),
    }


# --- PIPELINE ----------------------------------------------------------------
def scholar_titles_to_crossref(author_id: str) -> list:
    """Fetch titles from Scholar and enrich each using Crossref."""
    titles = fetch_titles_from_scholar(author_id)
    enriched = []

    for i, title in enumerate(titles, 1):
        print(f"[{i}/{len(titles)}] Enriching '{title[:80]}...'")
        time.sleep(REQUEST_PAUSE)
        msg = query_crossref_by_title(title)
        if msg:
            record = normalize_crossref_record(msg, title)
            enriched.append(record)
        else:
            enriched.append({"title": title})
    return enriched


def save_yaml(records: list, path: str):
    """Write the publications list to YAML."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(records, f, sort_keys=False, allow_unicode=True)
    print(f"Saved {len(records)} entries → {path}")


# --- MAIN --------------------------------------------------------------------
if __name__ == "__main__":
    pubs = scholar_titles_to_crossref(AUTHOR_ID)
    save_yaml(pubs, OUTPUT_PATH)
