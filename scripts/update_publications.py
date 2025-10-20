#!/usr/bin/env python3
"""
Fetch publications from Google Scholar via SerpAPI,
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
REQUEST_PAUSE = 0.4  # politeness delay for Crossref
OUTPUT_PATH = "_data/publications.yml"
QUERY = "Gad J OR Gurjao L OR Boero-Teyssier OR Hooper L"  # customize this query


# --- CROSSREF HELPERS ---------------------------------------------------------
def crossref_get(doi: str) -> dict:
    """Fetch Crossref record by DOI."""
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
    """Normalize Crossref metadata."""
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
    """Merge missing fields from Crossref into a publication record."""
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


# --- GOOGLE SCHOLAR (via SerpAPI) ---------------------------------------------
def fetch_google_scholar_articles(query: str, num_results: int = 20) -> list:
    """
    Fetch articles from Google Scholar via SerpAPI.
    Returns a list of dicts with title, authors, year, and DOI if found.
    """
    params = {
        "engine": "google_scholar",
        "q": query,
        "num": num_results,
        "api_key": SERPAPI_KEY,
    }
    try:
        r = requests.get(SERPAPI_BASE, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"Error fetching from SerpAPI: {e}")
        return []

    results = []
    for item in data.get("organic_results", []):
        title = item.get("title") or ""
        link = item.get("link") or ""
        pubinfo = item.get("publication_info", {}) or {}
        year = pubinfo.get("year")
        authors = pubinfo.get("authors", [])
        if isinstance(authors, list):
            authors = [a.get("name", "") if isinstance(a, dict) else a for a in authors]
        elif isinstance(authors, str):
            authors = [authors]
        else:
            authors = []

        # Extract DOI if link contains one
        doi = ""
        if "doi.org" in link:
            doi = link.split("doi.org/")[-1]

        results.append({
            "title": title.strip(),
            "url": link.strip(),
            "authors": authors,
            "year": year,
            "doi": doi,
        })

    return results


# --- MAIN PIPELINE ------------------------------------------------------------
def scholar_to_crossref(query: str, num_results: int = 20) -> list:
    """Fetch and enrich results from Scholar via Crossref."""
    print(f"Fetching top {num_results} results for: {query}")
    articles = fetch_google_scholar_articles(query, num_results)
    enriched = []
    for a in articles:
        enriched_pub = enrich_with_crossref(a)
        enriched.append(enriched_pub)
    print(f"Collected {len(enriched)} publications.")
    return enriched


def save_yaml(records: list, path: str):
    """Write publication records to YAML."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(records, f, sort_keys=False, allow_unicode=True)
    print(f"Saved {len(records)} entries → {path}")


# --- EXECUTION ---------------------------------------------------------------
if __name__ == "__main__":
    publications = scholar_to_crossref(QUERY, num_results=30)
    save_yaml(publications, OUTPUT_PATH)
