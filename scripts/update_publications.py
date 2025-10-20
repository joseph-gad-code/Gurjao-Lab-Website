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

# Author filtering: any of these tokens must appear in an author full name
TARGET_AUTHORS = {"gurjao"}  # add more lowercased last names if needed


# --- Utility functions ---
def normalize_text(s: str) -> str:
    """Normalize Unicode and lowercase for comparison."""
    return unicodedata.normalize("NFKD", (s or "")).encode("ascii", "ignore").decode("utf-8").lower().strip()


def title_key(s: str) -> str:
    """Loose key for dedup (strip spaces/punct/case)."""
    t = normalize_text(s)
    keep = []
    for ch in t:
        if ch.isalnum():
            keep.append(ch)
        elif ch.isspace():
            keep.append(" ")
    return " ".join("".join(keep).split())


def author_list_from_crossref(msg) -> list[str]:
    authors = []
    for a in (msg or {}).get("author", []) or []:
        given = (a.get("given") or "").strip()
        family = (a.get("family") or "").strip()
        full = " ".join([given, family]).strip()
        if full:
            authors.append(full)
    return authors


def authors_match_target(authors) -> bool:
    """
    True if any TARGET_AUTHORS token appears in any author name (case/accents ignored).
    `authors` can be list[str] or a single string.
    """
    if not authors:
        return False
    if isinstance(authors, str):
        pool = [authors]
    else:
        pool = list(authors)
    for a in pool:
        dn = normalize_text(a)
        # match on last-name token anywhere in the string
        if any(tok in dn.split() or tok in dn for tok in TARGET_AUTHORS):
            return True
    return False


def crossref_get(doi: str) -> dict:
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


def pick_best_crossref(items: list[dict], wanted_title: str) -> dict:
    """
    Choose the best Crossref item:
      1) title similar
      2) AND authors include target (preferred)
      3) otherwise the first title-similar item
    """
    if not items:
        return {}
    wkey = title_key(wanted_title)
    similar = []
    for it in items:
        t = (it.get("title") or [""])[0]
        if not t:
            continue
        if title_key(t) == wkey or wkey in title_key(t) or title_key(t) in wkey:
            similar.append(it)

    if not similar:
        return {}

    # prefer author match
    similar_with_author = [it for it in similar if authors_match_target(author_list_from_crossref(it))]
    if similar_with_author:
        return similar_with_author[0]
    return similar[0]


def crossref_search_title(title: str) -> dict:
    if not title:
        return {}
    try:
        url = f"https://api.crossref.org/works?query.title={quote_plus(title)}&rows=8"
        print(f"🔍 Crossref title search: {url}")
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        items = (r.json().get("message", {}).get("items", []) or [])
        return pick_best_crossref(items, title)
    except Exception as e:
        print(f"⚠️ Crossref title search failed for {title}: {e}")
        return {}


def crossref_search_scholar_metadata(pub: dict) -> dict:
    """Crossref search by a composite query from Scholar metadata."""
    title = pub.get("title", "") or ""
    journal = pub.get("journal", "") or ""
    year = str(pub.get("year", "") or "")
    serpa_authors = pub.get("authors_str", "") or ""  # store SerpAPI authors string

    query = " ".join(filter(None, [title, serpa_authors, journal, year]))
    try:
        url = f"https://api.crossref.org/works?query.bibliographic={quote_plus(query)}&rows=8"
        print(f"🔍 Crossref metadata search: {url}")
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        items = (r.json().get("message", {}).get("items", []) or [])
        return pick_best_crossref(items, title)
    except Exception as e:
        print(f"⚠️ Crossref metadata search failed for {title}: {e}")
        return {}


def extract_from_crossref(msg: dict) -> dict:
    if not msg:
        return {}
    # year
    year = None
    for k in ("published-print", "published-online", "issued"):
        dp = ((msg.get(k) or {}).get("date-parts") or [[]])
        if dp and dp[0]:
            year = dp[0][0]
            break
    # authors
    authors = author_list_from_crossref(msg)
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


def enrich_with_crossref(pub: dict) -> dict | None:
    """
    Enrich a pub with Crossref. If after enrichment we cannot confirm the target author,
    return None so the caller can skip it.
    """
    out = dict(pub)
    doi = (out.get("doi") or "").strip()
    title = (out.get("title") or "").strip()
    msg = {}

    # 1) DOI lookup
    if doi:
        msg = crossref_get(doi)
        time.sleep(REQUEST_PAUSE)

    # 2) Title search fallback
    if not msg and title:
        msg = crossref_search_title(title)
        time.sleep(REQUEST_PAUSE)

    # 3) Metadata search fallback
    if not msg:
        msg = crossref_search_scholar_metadata(out)
        time.sleep(REQUEST_PAUSE)

    meta = extract_from_crossref(msg)
    if not meta:
        print(f"⚠️ No Crossref match found for: {title}")
        # final guard: if SerpAPI authors string already matches our target, keep minimal record
        if authors_match_target(out.get("authors_str", "")):
            out.setdefault("selected_publication", False)
            return out
        return None

    # prefer Crossref authors if present
    out.update(meta)

    # author guards: Crossref authors OR SerpAPI authors must match target
    if not authors_match_target(out.get("authors")) and not authors_match_target(out.get("authors_str", "")):
        print(f"⛔ Dropping (author mismatch): {title}")
        return None

    # Keep the original title if Crossref title capitalization differs
    out["title"] = pub.get("title", meta.get("title", "")) or ""
    # Prefer Crossref URL if we have a DOI URL; otherwise keep SerpAPI link
    out["url"] = meta.get("url") or pub.get("url", "")
    out.setdefault("selected_publication", False)
    return out


def get_scholar_publications() -> list[dict]:
    """Retrieve Google Scholar publications (SerpAPI) with pagination."""
    pubs = []
    after_token = None

    while True:
        base = "https://serpapi.com/search.json"
        params = (
            f"engine=google_scholar_author&author_id={SCHOLAR_AUTHOR_ID}"
            f"&api_key={SERPAPI_KEY}"
        )
        if after_token:
            params += f"&after_author={quote_plus(after_token)}"
        url = f"{base}?{params}"

        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()

        for item in data.get("articles", []):
            # SerpAPI returns authors string in 'authors' or 'publication_info'. Handle both.
            authors_str = item.get("authors") or item.get("publication_info", {}).get("authors") or ""
            pubs.append({
                "title": item.get("title", "") or "",
                "url": item.get("link", "") or "",
                "doi": (item.get("publication_info", {}) or {}).get("doi", "") or "",
                "journal": item.get("publication", "") or "",
                "authors": [],                   # Crossref will fill a full list
                "authors_str": authors_str,      # keep raw string for guard
                "selected_publication": False,   # boolean
                "image": "",
            })

        after_token = data.get("serpapi_pagination", {}).get("next")
        if not after_token:
            break

        print("🔄 Loading next page of Google Scholar results...")
        time.sleep(REQUEST_PAUSE)

    print(f"✅ Total publications fetched from Scholar: {len(pubs)}")
    return pubs


def load_existing() -> list[dict]:
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or []
    return []


def update_publications():
    existing = load_existing()

    # dedup map by normalized title
    by_title = {title_key(p.get("title", "")): p for p in existing if p.get("title")}

    new_count = 0
    for pub in get_scholar_publications():
        k = title_key(pub.get("title", ""))
        if not k:
            continue
        if k in by_title:
            print(f"⏩ Skipping existing (by normalized title): {pub['title']}")
            continue

        enriched = enrich_with_crossref(pub)
        if not enriched:
            print(f"⚠️ Skipped (no match or author mismatch): {pub['title']}")
            continue

        by_title[k] = enriched
        new_count += 1
        print(f"✅ Added: {enriched['title']}")

    all_pubs = list(by_title.values())
    # Sort newest first (fallback -1 puts undated at end)
    def safe_year(p):
        y = p.get("year")
        try:
            return int(y)
        except Exception:
            return -1
    all_pubs.sort(key=safe_year, reverse=True)

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump(all_pubs, f, sort_keys=False, allow_unicode=True)

    print(f"\n✅ Updated publications file with {new_count} new entries.")
    print(f"📁 Total entries now: {len(all_pubs)}")


if __name__ == "__main__":
    update_publications()
