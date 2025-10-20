#!/usr/bin/env python3
import os, requests, time, yaml
from urllib.parse import quote_plus

# --- constants ---
CROSSREF_BASE = "https://api.crossref.org/works/"
SERPAPI_BASE = "https://serpapi.com/search"
REQUEST_PAUSE = 0.4
AUTHOR_ID = "m3rLfS4AAAAJ"  # Carino Gurjao

# --- helper: get publications from Google Scholar via SerpAPI ---
def fetch_scholar_pubs(api_key: str):
    """Fetch all publications for an author from Google Scholar via SerpAPI."""
    results = []
    next_url = f"{SERPAPI_BASE}?engine=google_scholar_author&author_id={AUTHOR_ID}&api_key={api_key}"
    print("Fetching publications from Google Scholar...")

    while next_url:
        r = requests.get(next_url, timeout=30)
        r.raise_for_status()
        data = r.json()
        pubs = data.get("articles", [])
        for p in pubs:
            entry = {
                "title": p.get("title", "").strip(),
                "authors": p.get("authors", []),
                "journal": p.get("publication", "").strip(),
                "year": p.get("year"),
                "url": p.get("link", ""),
                "citation_count": p.get("cited_by", {}).get("value"),
            }
            results.append(entry)
        next_url = data.get("serpapi_pagination", {}).get("next")
        if next_url:
            time.sleep(REQUEST_PAUSE)
    return results


# --- Crossref utilities ---
def crossref_get(doi: str):
    """Fetch one Crossref record by DOI."""
    if not doi:
        return {}
    try:
        r = requests.get(CROSSREF_BASE + doi, timeout=20)
        r.raise_for_status()
        return r.json().get("message", {})
    except Exception:
        return {}

def crossref_search_title(title: str):
    """Fetch best Crossref match by title."""
    if not title:
        return {}
    try:
        url = f"https://api.crossref.org/works?query.bibliographic={quote_plus(title)}&rows=1"
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        items = r.json().get("message", {}).get("items", [])
        return items[0] if items else {}
    except Exception:
        return {}

def extract_crossref_meta(msg: dict):
    """Extract normalized metadata from Crossref record."""
    if not msg:
        return {}
    # Year
    year = None
    for k in ("published-print", "published-online", "issued"):
        dp = ((msg.get(k) or {}).get("date-parts") or [[]])
        if dp and dp[0]:
            y = dp[0][0]
            if isinstance(y, int):
                year = y
                break
    authors = []
    for a in msg.get("author", []):
        name = " ".join(filter(None, [a.get("given"), a.get("family")]))
        if name:
            authors.append(name)
    return {
        "title": msg.get("title", [""])[0],
        "journal": (msg.get("container-title") or [""])[0],
        "volume": msg.get("volume"),
        "issue": msg.get("issue"),
        "pages": msg.get("page"),
        "year": year,
        "doi": msg.get("DOI"),
        "url": msg.get("URL"),
        "authors": authors,
        "publisher": msg.get("publisher"),
        "type": msg.get("type"),
    }


# --- merge logic ---
def reconcile(scholar_pub: dict, crossref_meta: dict):
    """Combine Scholar + Crossref data into one record."""
    merged = dict(scholar_pub)
    for k, v in crossref_meta.items():
        if v:
            merged[k] = v  # Crossref overrides Scholar
    # Keep citation count from Scholar if present
    if scholar_pub.get("citation_count") is not None:
        merged["citation_count"] = scholar_pub["citation_count"]
    return merged


# --- main workflow ---
def main():
    api_key = os.environ.get("SERPAPI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing SERPAPI_API_KEY")

    scholar_pubs = fetch_scholar_pubs(api_key)
    print(f"Fetched {len(scholar_pubs)} publications from Scholar")

    enriched = []
    for i, pub in enumerate(scholar_pubs, 1):
        title = pub.get("title", "")
        print(f"[{i}/{len(scholar_pubs)}] Enriching '{title[:60]}…'")
        msg = crossref_search_title(title)
        meta = extract_crossref_meta(msg)
        combined = reconcile(pub, meta)
        enriched.append(combined)
        time.sleep(REQUEST_PAUSE)

    out_path = "_data/publications.yml"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        yaml.dump(enriched, f, sort_keys=False, allow_unicode=True)
    print(f"✅ Saved {len(enriched)} publications to {out_path}")


if __name__ == "__main__":
    main()
