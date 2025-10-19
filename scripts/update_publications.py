# --- add these imports at the top ---
import time
from urllib.parse import quote_plus

CROSSREF_BASE = "https://api.crossref.org/works/"
REQUEST_PAUSE = 0.4  # be polite to Crossref

def crossref_get(doi: str) -> dict:
    """Fetch one Crossref record by DOI. Returns {} on any error."""
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
    """Very light title search fallback if we have no DOI."""
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
    """Normalize the fields we care about from a Crossref record."""
    if not msg:
        return {}
    # try published print, then published online
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
    """
    Given one pub dict from SerpAPI mapping, fill any missing fields
    (journal/venue, volume, issue, pages, year, url) from Crossref.
    Does not overwrite non-empty values.
    """
    out = dict(pub)  # copy
    msg = {}

    doi = (out.get("doi") or "").strip()
    if doi:
        time.sleep(REQUEST_PAUSE)
        msg = crossref_get(doi)
    if not msg:
        # No DOI or DOI didn’t resolve -> gentle title search
        title = out.get("title", "").strip()
        if title:
            time.sleep(REQUEST_PAUSE)
            msg = crossref_search_title(title)

    meta = extract_from_crossref(msg)
    if not meta:
        return out

    def set_if_empty(key, val):
        if val:
            if not out.get(key):
                out[key] = val

    # Map into your YAML schema
    set_if_empty("journal", meta.get("journal"))
    # If you use `venue` in templates too, keep it synced when journal is present
    if meta.get("journal") and not out.get("venue"):
        out["venue"] = meta["journal"]

    set_if_empty("volume", meta.get("volume"))
    set_if_empty("issue", meta.get("issue"))
    set_if_empty("pages", meta.get("pages"))
    set_if_empty("year", meta.get("year"))
    # Prefer DOI URL if no url set
    set_if_empty("url", meta.get("url"))
    # If SerpAPI didn’t give DOI but Crossref did, keep it
    set_if_empty("doi", meta.get("doi"))

    return out
