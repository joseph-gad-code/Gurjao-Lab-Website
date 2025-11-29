#!/usr/bin/env python3
import os, time, yaml, unicodedata, requests
from urllib.parse import quote_plus, urlparse, parse_qs
from pathlib import Path
from typing import Any, Dict, List, Optional

SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")
if not SERPAPI_KEY:
    print("Missing SERPAPI_API_KEY environment variable.")

SCHOLAR_AUTHOR_ID = "m3rLfS4AAAAJ"
DATA_FILE = Path("_data/publications.yml")
REQUEST_PAUSE = 0.5

CROSSREF_BASE = "https://api.crossref.org/works/"

# Surnames we consider “ours”
TARGET_AUTHORS = {"gurjao"}  # add more: {"gurjao","boero-teyssier","hooper","gad"}

PRESERVE_FIELDS = {"image", "selected_publication"}

# ---------------- utils ----------------
def normalize_text(s: Optional[str]) -> str:
    return unicodedata.normalize("NFKD", s or "").encode("ascii","ignore").decode("utf-8").lower()

def authors_match_target(authors: Any) -> bool:
    if not authors: return False
    pool = [authors] if isinstance(authors, str) else list(authors)
    for a in pool:
        dn = normalize_text(a)
        if any(tok in dn for tok in TARGET_AUTHORS):
            return True
    return False

def load_existing_yaml(path: Path) -> List[Dict[str, Any]]:
    if not path.exists(): return []
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or []
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"⚠️  Could not parse {path}: {e}")
        return []

def write_yaml(items: List[Dict[str, Any]], path: Path) -> None:
    def safe_year(x):
        y = x.get("year")
        if isinstance(y,int): return y
        try: return int(y)
        except: return -1
    items = sorted(items, key=safe_year, reverse=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(items, f, sort_keys=False, allow_unicode=True)

# ---------------- Crossref ----------------
def crossref_get(doi: str) -> Dict[str, Any]:
    if not doi: return {}
    try:
        url = CROSSREF_BASE + doi
        print(f"🔍 Crossref DOI lookup: {url}")
        r = requests.get(url, timeout=20); r.raise_for_status()
        return r.json().get("message", {}) or {}
    except Exception as e:
        print(f"⚠️ Crossref DOI fetch failed for {doi}: {e}")
        return {}

def _score_candidate(item: Dict[str,Any], title_norm: str, scholar_year: Optional[str]) -> int:
    """Score a Crossref candidate: prefer title similarity, author match to our surnames, year match, thesis/university containers."""
    score = 0
    cand_title = normalize_text((item.get("title") or [""])[0])
    if title_norm in cand_title or cand_title in title_norm:
        score += 50
    # author bonus if our surname is present
    cr_authors = []
    for a in item.get("author", []) or []:
        full = " ".join([(a.get("given") or "").strip(), (a.get("family") or "").strip()]).strip()
        if full: cr_authors.append(full)
    if authors_match_target(cr_authors):
        score += 40
    # year bonus
    year = None
    for k in ("published-print","published-online","issued"):
        dp = ((item.get(k) or {}).get("date-parts") or [[]])
        if dp and dp[0]:
            year = str(dp[0][0]); break
    if scholar_year and year and scholar_year == year:
        score += 8
    # prefer thesis/university-like containers when present
    container = normalize_text(((item.get("container-title") or [""])[0] or ""))
    if any(tok in container for tok in ["thesis","dissertation","universite","université","university"]):
        score += 6
    return score

def _pick_best(items: List[Dict[str,Any]], title: str, scholar_year: Optional[str]) -> Dict[str,Any]:
    if not items: return {}
    title_norm = normalize_text(title).split(":")[0].strip()
    best = max(items, key=lambda it: _score_candidate(it, title_norm, scholar_year))
    return best

def crossref_search_title(title: str, scholar_year: Optional[str]) -> Dict[str, Any]:
    if not title: return {}
    try:
        url = f"https://api.crossref.org/works?query.title={quote_plus(title)}&rows=10"
        print(f"🔍 Crossref title search: {url}")
        r = requests.get(url, timeout=20); r.raise_for_status()
        items = (r.json().get("message", {}).get("items", []) or [])
        return _pick_best(items, title, scholar_year)
    except Exception as e:
        print(f"⚠️ Crossref title search failed for {title}: {e}")
        return {}

def crossref_search_biblio(pub: Dict[str, Any]) -> Dict[str, Any]:
    title = pub.get("title","")
    journal = pub.get("journal","")
    year = str(pub.get("year","") or "")
    authors_str = pub.get("authors_str","")
    first_author = (authors_str.split(",")[0] if authors_str else "").strip()
    query = " ".join(filter(None, [title, first_author, journal, year]))
    if not query.strip(): return {}
    try:
        url = f"https://api.crossref.org/works?query.bibliographic={quote_plus(query)}&rows=10"
        print(f"🔍 Crossref metadata search: {url}")
        r = requests.get(url, timeout=20); r.raise_for_status()
        items = (r.json().get("message", {}).get("items", []) or [])
        return _pick_best(items, title, year or None)
    except Exception as e:
        print(f"⚠️ Crossref metadata search failed for {title}: {e}")
        return {}

def extract_from_crossref(msg: Dict[str, Any]) -> Dict[str, Any]:
    if not msg: return {}
    # year
    year = None
    for k in ("published-print","published-online","issued"):
        dp = ((msg.get(k) or {}).get("date-parts") or [[]])
        if dp and dp[0]:
            year = dp[0][0]; break
    # authors list
    authors_list = []
    for a in msg.get("author", []) or []:
        given = (a.get("given") or "").strip()
        family = (a.get("family") or "").strip()
        full = " ".join([given, family]).strip()
        if full: authors_list.append(full)
    return {
        "journal": ((msg.get("container-title") or [""])[0] or "").strip(),
        "volume": (msg.get("volume") or "").strip(),
        "issue":  (msg.get("issue") or "").strip(),
        "pages":  (msg.get("page") or "").strip(),
        "year":   year,
        "url":    (msg.get("URL") or "").strip(),
        "doi":    (msg.get("DOI") or "").strip(),
        "authors": authors_list,
    }

def enrich_with_crossref(pub: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Try DOI lookup, then title search, then biblio search.
    If best Crossref candidate does NOT include our surname but Scholar authors do,
    we keep the Scholar record (prevents “Cancer Cell 2019” from replacing your thesis).
    """
    out = dict(pub)
    doi = (out.get("doi") or "").strip()
    title = (out.get("title") or "").strip()
    scholar_year = str(out.get("year","") or "")
    msg = {}

    if doi:
        msg = crossref_get(doi); time.sleep(REQUEST_PAUSE)
    if not msg and title:
        msg = crossref_search_title(title, scholar_year or None); time.sleep(REQUEST_PAUSE)
    if not msg:
        msg = crossref_search_biblio(out); time.sleep(REQUEST_PAUSE)

    if not msg:
        print(f"⚠️ No Crossref match: {title}")
        # keep Scholar item if it clearly belongs to us
        if authors_match_target(out.get("authors_str","")):
            out.setdefault("selected_publication", False)
            return out
        return None

    meta = extract_from_crossref(msg)

    # SAFETY GUARD: if Scholar shows our surname but Crossref authors don’t,
    # do NOT overwrite (this prevents the wrong “Cancer Cell” record).
    if authors_match_target(out.get("authors_str","")) and not authors_match_target(meta.get("authors",[])):
        print("↩️  Crossref candidate rejected (authors mismatch). Keeping Scholar metadata.")
        out.setdefault("selected_publication", False)
        return out

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
    return merged

# ---------------- Scholar (SerpAPI) ----------------
def get_scholar_publications() -> List[Dict[str, Any]]:
    pubs: List[Dict[str, Any]] = []
    after_token: Optional[str] = None
    page = 1
    while True:
        base = "https://serpapi.com/search.json"
        params = f"engine=google_scholar_author&author_id={SCHOLAR_AUTHOR_ID}&api_key={SERPAPI_KEY}"
        if after_token:
            params += f"&after_author={quote_plus(after_token)}"
        url = f"{base}?{params}"
        print(f"🔎 Fetching Scholar page {page} ...")
        r = requests.get(url, timeout=30); r.raise_for_status()
        data = r.json()

        for item in data.get("articles", []) or []:
            authors_str = (
                item.get("authors")
                or (item.get("publication_info") or {}).get("authors")
                or ""
            )
            year = item.get("year")  # may be str/int/None
            pubs.append({
                "title": item.get("title", "") or "",
                "url": item.get("link", "") or "",
                "doi": ((item.get("publication_info") or {}).get("doi") or ""),
                "journal": item.get("publication", "") or "",
                "authors": [],                 # Crossref or Scholar fallback
                "authors_str": authors_str,    # raw string for guards
                "year": year,
                "selected_publication": False, # default field included
                "image": "",
            })

        next_url = (data.get("serpapi_pagination", {}) or {}).get("next")
        if not next_url: break
        try:
            qs = parse_qs(urlparse(next_url).query)
            after_token = (qs.get("after_author") or [None])[0]
        except Exception:
            after_token = None
        if not after_token: break

        page += 1
        time.sleep(REQUEST_PAUSE)

    print(f"✅ Total publications fetched from Scholar: {len(pubs)}")
    return pubs

# ---------------- merge/update ----------------
def norm_key(title: str) -> str:
    return normalize_text(title)

def merge_existing(existing: List[Dict[str, Any]], new_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    idx = {norm_key(e.get("title","")): e for e in existing if e.get("title")}
    merged = idx.copy()
    for it in new_items:
        t = it.get("title",""); 
        if not t: continue
        k = norm_key(t)
        if k in merged:
            prev = merged[k]
            for f in PRESERVE_FIELDS:
                if f in prev and prev[f] not in (None,"",[]):
                    it[f] = prev[f]
            if prev.get("doi") and not it.get("doi"):
                it["doi"] = prev["doi"]
            if prev.get("url") and not it.get("url"):
                it["url"] = prev["url"]
        merged[k] = it
    return list(merged.values())

def update_publications():
    existing = load_existing_yaml(DATA_FILE)
    existing_keys = {norm_key(p["title"]) for p in existing if p.get("title")}
    scholar_items = get_scholar_publications()

    new_enriched: List[Dict[str, Any]] = []
    for pub in scholar_items:
        key = norm_key(pub.get("title",""))
        if not key or key in existing_keys:
            continue
        enriched = enrich_with_crossref(pub)
        if enriched is None:
            continue
        new_enriched.append(enriched)

    final_list = merge_existing(existing, new_enriched)
    write_yaml(final_list, DATA_FILE)
    print(f"\n📁 Wrote {len(final_list)} publications to {DATA_FILE}")
    print(f"➕ Newly added this run: {len(new_enriched)}")

if __name__ == "__main__":
    if not SERPAPI_KEY:
        # Exit with success so CI does not fail
        raise SystemExit(0)
    update_publications()
