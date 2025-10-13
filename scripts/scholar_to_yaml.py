#!/usr/bin/env python3
import os, sys, re, json, time
from pathlib import Path
from typing import List, Dict, Any

import yaml
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# --- Optional: SERPAPI fallback (only if you add a key) ---
USE_SERPAPI = bool(os.getenv("SERPAPI_KEY"))
if USE_SERPAPI:
    import requests

# --- Scholar via scholarly ---
from scholarly import scholarly, ProxyGenerator

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "_data" / "publications.yml"
USER_ID = os.environ.get("SCHOLAR_USER_ID", "").strip()

if not USER_ID:
    print("SCHOLAR_USER_ID env var is required", file=sys.stderr)
    sys.exit(1)

def load_yaml(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or []

def dump_yaml(path: Path, data: List[Dict[str, Any]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, width=1000)

def normalize_author_line(names: List[str]) -> str:
    # e.g., convert list to a comma-separated line as you’re storing now
    return ", ".join(n.strip() for n in names if n and n.strip())

def clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()

def map_entry_from_scholarly(p: Dict[str, Any]) -> Dict[str, Any]:
    title = clean_text(p.get("bib", {}).get("title"))
    year  = p.get("bib", {}).get("pub_year")
    try:
        year = int(year)
    except Exception:
        year = None

    authors = p.get("bib", {}).get("author", [])
    if isinstance(authors, str):
        # scholarly sometimes returns "A; B; C" – split on common separators
        authors = re.split(r"\s*(?:,|;)\s*", authors)
    author_line = normalize_author_line(authors)

    journal = clean_text(p.get("bib", {}).get("venue")) or clean_text(p.get("bib", {}).get("journal"))
    volume  = clean_text(p.get("bib", {}).get("volume"))
    pages   = clean_text(p.get("bib", {}).get("pages"))
    url     = clean_text(p.get("pub_url"))

    return {
        "title": title,
        "authors": author_line,
        "journal": journal,
        "journal_url": "",  # you can enrich later
        "year": year,
        "volume": volume or None,
        "pages": pages or None,
        "url": url or None,
        # DO NOT set/override selected-publication here – preserve user choice below
    }

@retry(stop=stop_after_attempt(5),
       wait=wait_exponential(multiplier=1, min=2, max=20),
       retry=retry_if_exception_type(Exception))
def fetch_scholar_profile(user_id: str) -> List[Dict[str, Any]]:
    # simple, non-proxy first; fall back to Tor if needed
    # (Tor is not enabled by default here to keep CI simple)
    # scholarly has internal caching; the retry will help if rate-limited
    author = scholarly.search_author_id(user_id)
    author = scholarly.fill(author, sections=["publications"])
    pubs = []
    for pub in author.get("publications", []):
        try:
            filled = scholarly.fill(pub)
            pubs.append(filled)
        except Exception as e:
            # skip one bad entry; continue
            print(f"WARN: could not fill one pub: {e}", file=sys.stderr)
            continue
    return pubs

def fetch_serpapi(user_id: str, api_key: str) -> List[Dict[str, Any]]:
    # lightweight fallback using SerpAPI's Google Scholar author endpoint
    # https://serpapi.com/google-scholar-api (requires API key)
    # NOTE: This gives summary info; you may need to page for all results.
    url = "https://serpapi.com/search.json"
    params = {"engine": "google_scholar_author", "author_id": user_id, "api_key": api_key}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("articles", [])

def map_entry_from_serpapi(it: Dict[str, Any]) -> Dict[str, Any]:
    title = clean_text(it.get("title"))
    year  = it.get("year")
    try:
        year = int(year)
    except Exception:
        year = None

    author_line = clean_text(it.get("authors"))
    journal = clean_text(it.get("publication"))
    url = it.get("link")

    return {
        "title": title,
        "authors": author_line,
        "journal": journal,
        "journal_url": "",
        "year": year,
        "volume": None,
        "pages": None,
        "url": url or None,
    }

def merge_keep_selected(old: List[Dict[str, Any]], new: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # index existing by (title lower) to preserve selected-publication flags
    idx = { (clean_text(o.get("title")).lower()): o for o in old }
    out = []
    for n in new:
        key = clean_text(n.get("title")).lower()
        existing = idx.get(key)
        if existing and "selected-publication" in existing:
            n["selected-publication"] = bool(existing["selected-publication"])
        out.append(n)
    # sort newest first by year, then title
    out.sort(key=lambda x: (x.get("year") or 0, x.get("title") or ""), reverse=True)
    return out

def main():
    old = load_yaml(DATA_FILE)

    if USE_SERPAPI:
        try:
            api_key = os.environ["SERPAPI_KEY"]
            raw = fetch_serpapi(USER_ID, api_key)
            mapped = [map_entry_from_serpapi(x) for x in raw]
        except Exception as e:
            print(f"SerpAPI failed, falling back to scholarly: {e}", file=sys.stderr)
            mapped = None
    else:
        mapped = None

    if mapped is None:
        pubs = fetch_scholar_profile(USER_ID)
        mapped = [map_entry_from_scholarly(x) for x in pubs if x]

    new = merge_keep_selected(old, mapped)
    if new != old:
        dump_yaml(DATA_FILE, new)
        print(f"Wrote {len(new)} entries to {DATA_FILE}")
    else:
        print("No changes detected.")

if __name__ == "__main__":
    main()
