#!/usr/bin/env python3
"""
Hybrid updater: stable list from SerpAPI + rich enrichment from Crossref/OpenAlex.
- Adds/ensures "selected_publication": False on each record (preserves if True).
- Incremental by default (existing records are NOT re-enriched).
- New titles are enriched and appended.
- Curated fields (image, description, highlight, news1, news2) are preserved.

Requirements:
  pip install requests pyyaml
Env:
  SERPAPI_API_KEY (required)
  CROSSREF_MAILTO (optional but recommended for polite Crossref headers)
"""

import os, re, sys, time, yaml, requests, difflib
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus
from pathlib import Path

# ---------- CONFIG ----------
SERPAPI_API_KEY      = os.environ.get("SERPAPI_API_KEY", "")
GOOGLE_SCHOLAR_ID    = "m3rLfS4AAAAJ"
OUTFILE              = Path("_data/publist.yml")
MAX_PAGES            = 6
REQUEST_PAUSE_S      = 0.4
CROSSREF_MAILTO      = os.environ.get("CROSSREF_MAILTO", "")

# INCREMENTAL behavior:
SKIP_ENRICH_FOR_EXISTING   = True  # default: do not touch existing entries at all
FILL_MISSING_FOR_EXISTING  = False # set True to fill only missing fields for existing entries

# Preserve curated fields
PRESERVE_FIELDS = {"image", "description", "highlight", "news1", "news2"}

# ---------- UTIL ----------
def norm_space(s: Optional[str]) -> str:
    return re.sub(r"\s+", " ", s.strip()) if s else ""

def norm_title_key(t: str) -> str:
    t = norm_space(t).lower()
    return re.sub(r"[^a-z0-9 _:&()'/. -]", "", t)

def to_display(venue: str, volume: str, pages: str, year: str) -> str:
    parts = []
    if venue: parts.append(venue)
    tail = []
    if volume: tail.append(volume)
    if pages: tail.append(pages)
    if tail: parts.append(", ".join(tail))
    if year: parts.append(f"({year})")
    return " ".join(parts).strip() or (year or "")

def safe_year(y) -> str:
    if not y: return ""
    m = re.search(r"(19|20)\d{2}", str(y))
    return m.group(0) if m else ""

def classify_type(venue: str, doi: str) -> str:
    v = (venue or "").lower()
    if "arxiv" in v: return "preprint"
    if any(k in v for k in ["thesis","dissertation"]): return "thesis"
    if any(k in v for k in ["conf","conference","proc","proceedings","symposium"]):
        return "conference"
    return "journal" if venue else "article"

def gs_link_for_title(title: str) -> str:
    return f"https://scholar.google.com/scholar?q={quote_plus(title)}"

def load_existing(path: Path) -> List[Dict[str, Any]]:
    if not path.exists(): return []
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or []
        return data if isinstance(data, list) else []

def existing_index_by_title(items: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    idx = {}
    for it in items:
        t = it.get("title")
        if t: idx[norm_title_key(t)] = it
    return idx

def clean_link(d: Dict[str, Any]) -> Dict[str, Any]:
    if "link" in d and isinstance(d["link"], dict):
        d["link"] = {k: v for k, v in d["link"].items() if v}
    return d

# ---------- SERPAPI ----------
def fetch_serpapi_pubs(author_id: str, api_key: str, pages: int = 5) -> List[Dict[str, Any]]:
    if not api_key:
        print("ERROR: SERPAPI_API_KEY not set"); sys.exit(1)

    params = {
        "api_key": api_key,
        "engine": "google_scholar_author",
        "author_id": author_id,
        "hl": "en",
        "view_op": "list_works"
    }
    all_items = []

    for p in range(pages):
        r = requests.get("https://serpapi.com/search", params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            raise RuntimeError(f"SerpAPI error: {data['error']}")

        articles = data.get("articles", [])
        if not articles: break

        for a in articles:
            all_items.append({
                "title": norm_space(a.get("title","")),
                "authors_seen": norm_space(a.get("authors","")),
                "pubmeta": norm_space(a.get("publication","")),
                "year": a.get("year"),
                "link_raw": a.get("link") or "",
                "resources": a.get("resources") or [],
            })

        next_link = data.get("serpapi_pagination", {}).get("next")
        if not next_link: break
        # parse "next" safely
        try:
            after = next_link.split("search?")[1]
            parts = [s.split("=",1) for s in after.split("&") if "=" in s]
            params.update(dict(parts))
        except Exception:
            break
        time.sleep(REQUEST_PAUSE_S)

    return all_items

# ---------- ENRICH: Crossref & OpenAlex ----------
def crossref_headers():
    h = {"User-Agent": "lab-pubs-updater/1.0"}
    if CROSSREF_MAILTO:
        h["mailto"] = CROSSREF_MAILTO
    return h

def crossref_lookup(title: str, year_hint: Optional[str]) -> Optional[Dict[str, Any]]:
    q = title
    params = {
        "query.bibliographic": q,
        "rows": 5,
        "select": "title,author,container-title,issued,URL,DOI,page,volume,issue,publisher,type"
    }
    if year_hint:
        params["filter"] = f"from-pub-date:{year_hint}-01-01,until-pub-date:{year_hint}-12-31"

    r = requests.get("https://api.crossref.org/works", params=params, headers=crossref_headers(), timeout=25)
    if r.status_code != 200:
        return None
    items = r.json().get("message", {}).get("items", [])
    if not items: return None

    def best_ratio(item):
        cand = " ".join(item.get("title") or [])
        return difflib.SequenceMatcher(None, title.lower(), cand.lower()).ratio()

    items.sort(key=best_ratio, reverse=True)
    best = items[0]
    cand = " ".join(best.get("title") or [])
    if difflib.SequenceMatcher(None, title.lower(), cand.lower()).ratio() < 0.6:
        return None
    return best

def openalex_lookup_by_title(title: str, year_hint: Optional[str]) -> Optional[Dict[str, Any]]:
    params = {"search": title, "per-page": 5}
    if year_hint:
        params["filter"] = f"from_publication_date:{year_hint}-01-01,to_publication_date:{year_hint}-12-31"
    r = requests.get("https://api.openalex.org/works", params=params, timeout=25)
    if r.status_code != 200: return None
    results = r.json().get("results", [])
    if not results: return None

    def br(x):
        return difflib.SequenceMatcher(None, title.lower(), (x.get("title") or "").lower()).ratio()
    results.sort(key=br, reverse=True)
    best = results[0]
    if br(best) < 0.6: return None
    return best

def authors_from_crossref(item) -> str:
    authors = item.get("author") or []
    names = []
    for a in authors:
        given = a.get("given") or ""
        family = a.get("family") or ""
        full = " ".join([given, family]).strip()
        if full: names.append(full)
    return ", ".join(names)

def year_from_crossref(item) -> str:
    issued = item.get("issued", {}).get("date-parts", [[]])
    y = issued[0][0] if issued and issued[0] else ""
    return str(y) if y else ""

def to_rich_from_crossref(title: str, cr: Dict[str, Any]) -> Dict[str, Any]:
    venue  = (cr.get("container-title") or [""])[0]
    volume = cr.get("volume") or ""
    issue  = cr.get("issue") or ""
    pages  = cr.get("page") or ""
    year   = year_from_crossref(cr)
    doi    = cr.get("DOI") or ""
    url    = cr.get("URL") or (f"https://doi.org/{doi}" if doi else "")
    authors= authors_from_crossref(cr)
    display= to_display(venue, volume, pages, year)
    return {
        "title": title,
        "authors": authors or None,
        "venue": venue or None,
        "year": int(year) if year.isdigit() else (year or None),
        "volume": volume or None,
        "issue": issue or None,
        "pages": pages or None,
        "doi": doi or None,
        "publisher": cr.get("publisher") or None,
        "type": classify_type(venue, doi),
        "link": {"url": url or gs_link_for_title(title), "display": display},
        "publisher_url": url or None,
        "pdf_url": None,
        "image": None,
        "description": None,
        "highlight": 0,
        "news1": None,
        "news2": None,
        "selected_publication": False,
    }

def to_rich_from_openalex(title: str, oa: Dict[str, Any]) -> Dict[str, Any]:
    biblio = oa.get("biblio") or {}
    venue  = (oa.get("host_venue") or {}).get("display_name") or ""
    volume = biblio.get("volume") or ""
    issue  = biblio.get("issue") or ""
    pages  = biblio.get("first_page","")
    if biblio.get("last_page"):
        pages = f"{pages}-{biblio['last_page']}" if pages else biblio["last_page"]
    year   = safe_year(oa.get("publication_year"))
    doi    = (oa.get("ids") or {}).get("doi") or oa.get("doi") or ""
    url    = (oa.get("host_venue") or {}).get("url") or (f"https://doi.org/{doi}" if doi else "")
    authors= ", ".join([a.get("author",{}).get("display_name","") for a in (oa.get("authorships") or []) if a.get("author")]) or ""
    display= to_display(venue, volume, pages, year)
    return {
        "title": title,
        "authors": authors or None,
        "venue": venue or None,
        "year": int(year) if str(year).isdigit() else (year or None),
        "volume": volume or None,
        "issue": issue or None,
        "pages": pages or None,
        "doi": (doi.replace("https://doi.org/","") if doi else None),
        "publisher": None,
        "type": classify_type(venue, doi),
        "link": {"url": url or gs_link_for_title(title), "display": display},
        "publisher_url": url or None,
        "pdf_url": None,
        "image": None,
        "description": None,
        "highlight": 0,
        "news1": None,
        "news2": None,
        "selected_publication": False,
    }

# ---------- MERGE HELPERS ----------
def merge_fill_missing(old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """Fill only missing/empty fields in old using new. Preserve link.display from old."""
    out = dict(old)
    for k, v in new.items():
        if k in ("link",):  # handle link separately
            continue
        if k not in out or out[k] in (None, "", [], {}):
            out[k] = v
    # Merge link
    if isinstance(new.get("link"), dict):
        out.setdefault("link", {})
        for lk, lv in new["link"].items():
            if lk not in out["link"] or not out["link"][lk]:
                out["link"][lk] = lv

    # Ensure selected_publication exists, preserve True
    if "selected_publication" not in out:
        out["selected_publication"] = False
    return clean_link(out)

def ensure_selected_flag(d: Dict[str, Any]) -> Dict[str, Any]:
    if "selected_publication" not in d:
        d["selected_publication"] = False
    return d

# ---------- MAIN ----------
def main():
    print(f"Fetching base list from SerpAPI for {GOOGLE_SCHOLAR_ID} …")
    base = fetch_serpapi_pubs(GOOGLE_SCHOLAR_ID, SERPAPI_API_KEY, pages=MAX_PAGES)
    print(f"Got {len(base)} items")

    existing = load_existing(OUTFILE)
    existing_idx = existing_index_by_title(existing)
    seen_keys = set()

    results: List[Dict[str, Any]] = []

    for i, item in enumerate(base, 1):
        title = item["title"]
        if not title: continue
        key = norm_title_key(title)
        year_hint = safe_year(item.get("year"))
        enriched = None

        if key in existing_idx:
            prev = existing_idx[key]
            seen_keys.add(key)

            # Always ensure the flag exists; preserve curated fields below.
            prev = ensure_selected_flag(prev)

            if SKIP_ENRICH_FOR_EXISTING:
                # Carry record forward unchanged (fast & incremental)
                results.append(prev)
                print(f"{i:3d}. {title[:90]}  (kept existing)")
                continue

            # Otherwise optionally fill missing only
            if FILL_MISSING_FOR_EXISTING:
                # enrich then fill only missing fields
                try:
                    cr = crossref_lookup(title, year_hint)
                    if cr:
                        enriched = to_rich_from_crossref(title, cr)
                except Exception:
                    enriched = None
                if not enriched:
                    try:
                        oa = openalex_lookup_by_title(title, year_hint)
                        if oa:
                            enriched = to_rich_from_openalex(title, oa)
                    except Exception:
                        enriched = None

                if enriched:
                    # preserve curated & selected flag from prev
                    for fld in PRESERVE_FIELDS:
                        if fld in prev and prev[fld] not in (None, ""):
                            enriched[fld] = prev[fld]
                    if prev.get("selected_publication", False):
                        enriched["selected_publication"] = True

                    merged = merge_fill_missing(prev, enriched)
                    results.append(merged)
                    print(f"{i:3d}. {title[:90]}  (filled missing)")
                    time.sleep(REQUEST_PAUSE_S)
                    continue
                else:
                    results.append(prev)
                    print(f"{i:3d}. {title[:90]}  (no enrichment, kept)")
                    continue

        # NEW publication → enrich now
        try:
            cr = crossref_lookup(title, year_hint)
            if cr:
                enriched = to_rich_from_crossref(title, cr)
        except Exception:
            enriched = None

        if not enriched:
            try:
                oa = openalex_lookup_by_title(title, year_hint)
                if oa:
                    enriched = to_rich_from_openalex(title, oa)
            except Exception:
                enriched = None

        if not enriched:
            # fallback minimal
            venue = item.get("pubmeta","")
            year  = safe_year(item.get("year"))
            display = to_display(venue, "", "", year)
            enriched = {
                "title": title,
                "authors": item.get("authors_seen") or None,
                "venue": venue or None,
                "year": int(year) if year.isdigit() else (year or None),
                "volume": None, "issue": None, "pages": None,
                "doi": None, "publisher": None,
                "type": classify_type(venue, ""),
                "link": {"url": gs_link_for_title(title), "display": display},
                "publisher_url": None, "pdf_url": None,
                "image": None, "description": None, "highlight": 0,
                "news1": None, "news2": None,
                "selected_publication": False,
            }

        # preserve curated fields from existing if we somehow hit a key match
        if key in existing_idx:
            prev = existing_idx[key]
            for fld in PRESERVE_FIELDS:
                if fld in prev and prev[fld] not in (None, ""):
                    enriched[fld] = prev[fld]
            if prev.get("selected_publication", False):
                enriched["selected_publication"] = True

        results.append(clean_link(enriched))
        print(f"{i:3d}. {title[:90]}  (added)")
        time.sleep(REQUEST_PAUSE_S)

    # Keep any existing entries SerpAPI didn't return this run (optional)
    for key, rec in existing_idx.items():
        if key not in seen_keys and key not in {norm_title_key(r["title"]) for r in results}:
            results.append(ensure_selected_flag(rec))

    # sort newest first by year
    def ykey(x):
        y = x.get("year")
        if isinstance(y, int): return y
        if isinstance(y, str) and y.isdigit(): return int(y)
        return -1

    results.sort(key=ykey, reverse=True)
    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTFILE.open("w", encoding="utf-8") as f:
        yaml.safe_dump(results, f, sort_keys=False, allow_unicode=True)

    print(f"\nWrote {len(results)} publications to {OUTFILE}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ERROR:", e)
        sys.exit(2)
