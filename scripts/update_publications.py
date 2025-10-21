#!/usr/bin/env python3
"""
update_publications.py

- Fetches publications from Google Scholar (via SerpAPI) for a given author_id
- Correct SerpAPI pagination (extracts the after_author token from 'next' URL)
- Enriches each item with Crossref metadata (DOI/journal/volume/pages/authors/year)
- Keeps Scholar-only items if the raw authors string contains a target author
- Merges with existing YAML without duplicating entries
- Preserves curated fields (image, selected_publication) on re-run
"""

import os
import time
import yaml
import unicodedata
import requests
from urllib.parse import quote_plus, urlparse, parse_qs
from pathlib import Path
from typing import Any, Dict, List, Optional

# -------------------
# Configuration
# -------------------
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")
if not SERPAPI_KEY:
    raise RuntimeError("Missing SERPAPI_API_KEY environment variable.")

SCHOLAR_AUTHOR_ID = "m3rLfS4AAAAJ"     # your Google Scholar author ID
DATA_FILE = Path("_data/publications.yml")
REQUEST_PAUSE = 0.5                     # polite delay between requests

# Crossref
CROSSREF_BASE = "https://api.crossref.org/works/"

# Target lab surnames to keep when enrichment fails
TARGET_AUTHORS = {
    "gurjao",
    # add more lab surnames here if desired:
    # "boero-teyssier", "hooper", "gad"
}


# -------------------
# Utilities
# -------------------
def normalize_text(s: Optional[str]) -> str:
    """Normalize Unicode and lowercase for comparison."""
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode("utf-8").lower()


def authors_match_target(authors: Any) -> bool:
    """
    True if any of the target surnames appear in a string or a list of strings.
    Accepts either the raw authors string (from SerpAPI) or a list (from Crossref).
    """
    if not authors:
        return False
    pool = [authors] if isinstance(authors, str) else list(authors)
    for a in pool:
        dn = normalize_text(a)
        if any(tok in dn for tok in TARGET_AUTHORS):
            return True
    return False


def load_existing_yaml(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or []
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"⚠️  Could not parse {path}: {e}")
        return []


def write_yaml(items: List[Dict[str, Any]], path: Path) -> None:
    # sort by year desc when possible
    def safe_year(x):
        y = x.get("year")
        if isinstance(y, int):
            return y
        try:
            return int(y)
        except Exception:
            return -1

    items = sorted(items, key=safe_year, reverse=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(items, f, sort_keys=False, allow_unicode=True)


# -------------------
# Crossref helpers
# -------------------
def crossref_get(doi: str) -> Dict[str, Any]:
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


def crossref_search_title(title: str) -> Dict[str, Any]:
    """Search Crossref by title only (simple fallback)."""
    if not title:
        return {}
    try:
        url = f"https://api.crossref.org/works?query.title={quote_plus(title)}&rows=5"
        print(f"🔍 Crossref title search: {url}")
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        items = (r.json().get("message", {}).get("items", []) or [])
        if not items:
            return {}
        title_norm = normalize_text(title).split(":")[0]
        # prefer the closest title
        for it in items:
            cand_title = normalize_text((it.get("title") or [""])[0])
            if title_norm in cand_title or cand_title in title_norm:
                return it
        return items[0]
    except Exception as e:
        print(f"⚠️ Crossref title search failed for {title}: {e}")
        return {}


def crossref_search_biblio(pub: Dict[str, Any]) -> Dict[str, Any]:
    """Search Crossref using richer metadata from Scholar (title + first author + journal + year)."""
    title = pub.get("title", "")
    journal = pub.get("journal", "")
    year = str(pub.get("year", "") or "")
    authors_str = pub.get("authors_str", "")
    first_author = (authors_str.split(",")[0] if authors_str else "").strip()

    query = " ".join(filter(None, [title, first_author, journal, year]))
    if not query.strip():
        return {}

    url = f"https://api.crossref.org/works?query.bibliographic={quote_plus(query)}&rows=6"
    print(f"🔍 Crossref metadata search: {url}")
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        items = (r.json().get("message", {}).get("items", []) or [])
        if not items:
            return {}
        title_norm = normalize_text(title).split(":")[0]
        for it in items:
            cand_title = normalize_text((it.get("title") or [""])[0])
            if title_norm in cand_title or cand_title in title_norm:
                return it
        return items[0]
    except Exception as e:
        print(f"⚠️ Crossref metadata search failed for {title}: {e}")
        return {}


def extract_from_crossref(msg: Dict[str, Any]) -> Dict[str, Any]:
    """Extract structured fields from a Crossref work message."""
    if not msg:
        return {}

    # year
    year = None
    for k in ("published-print", "published-online", "issued"):
        dp = ((msg.get(k) or {}).get("date-parts") or [[]])
        if dp and dp[0]:
            year = dp[0][0]
            break

    # authors (list of "Given Family")
    authors_list = []
    for a in msg.get("author", []) or []:
        given = (a.get("given") or "").strip()
        family = (a.get("family") or "").strip()
        full = " ".join([given, family]).strip()
        if full:
            authors_list.append(full)

    out = {
        "journal": ((msg.get("container-title") or [""])[0] or "").strip(),
        "volume": (msg.get("volume") or "").strip(),
        "issue":  (msg.get("issue") or "").strip(),
        "pages":  (msg.get("page") or "").strip(),
        "year":   year,
        "url":    (msg.get("URL") or "").strip(),
        "doi":    (msg.get("DOI") or "").strip(),
        "authors": authors_list,
    }
    return out


def enrich_with_crossref(pub: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Try DOI lookup, then title search, then biblio search.
    If no Crossref match, keep the Scholar record ONLY if it matches target authors.
    """
    out = dict(pub)
    doi = (out.get("doi") or "").strip()
    title = (out.get("title") or "").strip()

    msg = {}
    if doi:
        msg = crossref_get(doi)
        time.sleep(REQUEST_PAUSE)

    if not msg and title:
        msg = crossref_search_title(title)
        time.sleep(REQUEST_PAUSE)

    if not msg:
        msg = crossref_search_biblio(out)
        time.sleep(REQUEST_PAUSE)

    if not msg:
        print(f"⚠️ No Crossref match: {title}")
        # FINAL GUARD: keep Scholar record if the raw authors string matches
        if authors_match_target(out.get("authors_str", "")):
            out.setdefault("selected_publication", False)
            return out
        return None

    meta = extract_from_crossref(msg)
    # Merge: prefer Crossref fields for structured metadata, but keep Scholar title/url if set
    merged = {
        "title": title or meta.get("title") or "",
        "url": out.get("url") or meta.get("url") or "",
        "journal": meta.get("journal", out.get("journal", "")),
        "volume": meta.get("volume", ""),
        "issue": meta.get("issue", ""),
        "pages": meta.get("pages", ""),
        "year": meta.get("year", out.get("year", "")),
        "doi": meta.get("doi", doi),
        "authors": meta.get("authors", []),
        "selected_publication": out.get("selected_publication", False),
        "image": out.get("image", ""),
        "authors_str": out.get("authors_str", ""),
    }

    # Guard: if Crossref authors don’t show target names, still allow,
    # because Scholar already said the item belongs to this author_id.
    return merged


# -------------------
# SerpAPI (Google Scholar)
# -------------------
def get_scholar_publications() -> List[Dict[str, Any]]:
    """Retrieve ALL publications for an author via SerpAPI (with correct pagination)."""
    pubs: List[Dict[str, Any]] = []
    after_token: Optional[str] = None
    page = 1

    while True:
        base = "https://serpapi.com/search.json"
        params = (
            f"engine=google_scholar_author&author_id={SCHOLAR_AUTHOR_ID}"
            f"&api_key={SERPAPI_KEY}"
        )
        if after_token:
            params += f"&after_author={quote_plus(after_token)}"
        url = f"{base}?{params}"

        print(f"🔎 Fetching Scholar page {page} ...")
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()

        for item in data.get("articles", []) or []:
            authors_str = (
                item.get("authors")
                or (item.get("publication_info") or {}).get("authors")
                or ""
            )
            pubs.append({
                "title": item.get("title", "") or "",
                "url": item.get("link", "") or "",
                "doi": ((item.get("publication_info") or {}).get("doi") or ""),
                "journal": item.get("publication", "") or "",
                "authors": [],                 # will be filled by Crossref
                "authors_str": authors_str,    # keep raw string for guards
                "selected_publication": False, # default field included
                "image": "",
            })

        # Extract after_author token from the 'next' URL
        next_url = (data.get("serpapi_pagination", {}) or {}).get("next")
        if not next_url:
            break
        try:
            qs = parse_qs(urlparse(next_url).query)
            after_token = (qs.get("after_author") or [None])[0]
        except Exception:
            after_token = None

        if not after_token:
            break

        page += 1
        time.sleep(REQUEST_PAUSE)

    print(f"✅ Total publications fetched from Scholar: {len(pubs)}")
    return pubs


# -------------------
# Merge & Update
# -------------------
PRESERVE_FIELDS = {"image", "selected_publication"}  # keep curated values

def norm_key(title: str) -> str:
    return normalize_text(title)


def merge_existing(existing: List[Dict[str, Any]], new_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge on normalized title; preserve curated fields.
    """
    idx = {norm_key(e.get("title", "")): e for e in existing if e.get("title")}
    merged = idx.copy()

    for it in new_items:
        t = it.get("title", "")
        if not t:
            continue
        k = norm_key(t)
        if k in merged:
            prev = merged[k]
            # preserve curated fields if present in previous
            for f in PRESERVE_FIELDS:
                if f in prev and prev[f] not in (None, "", []):
                    it[f] = prev[f]
            # also preserve a better URL/DOI if prev has and new doesn't
            if prev.get("doi") and not it.get("doi"):
                it["doi"] = prev["doi"]
            if prev.get("url") and not it.get("url"):
                it["url"] = prev["url"]
        merged[k] = it

    return list(merged.values())


def update_publications():
    # Load existing YAML
    existing = load_existing_yaml(DATA_FILE)
    existing_keys = {norm_key(p["title"]) for p in existing if p.get("title")}

    # Fetch from Scholar
    scholar_items = get_scholar_publications()

    # Only enrich new titles
    new_enriched: List[Dict[str, Any]] = []
    for pub in scholar_items:
        key = norm_key(pub.get("title", ""))
        if not key or key in existing_keys:
            # already present; will be merged later
            continue
        enriched = enrich_with_crossref(pub)
        if enriched is None:
            # filtered out (no match and no target author signal)
            continue
        new_enriched.append(enriched)

    # Merge and write
    final_list = merge_existing(existing, new_enriched)
    write_yaml(final_list, DATA_FILE)

    print(f"\n📁 Wrote {len(final_list)} publications to {DATA_FILE}")
    print(f"➕ Newly added this run: {len(new_enriched)}")


if __name__ == "__main__":
    update_publications()
