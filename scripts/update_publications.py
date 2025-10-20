# --- add these imports at the top ---
import time
import re
import requests
from urllib.parse import quote_plus

# --- constants ---
CROSSREF_BASE = "https://api.crossref.org/works/"
REQUEST_PAUSE = 0.4  # be polite to Crossref
CARINO_GURJAO_ORCID = "0000-0002-4813-5460"  # unique researcher ID


def crossref_get(doi: str) -> dict:
    """Fetch one Crossref record by DOI. Returns {} on any error."""
    if not doi:
        return {}
    try:
        r = requests.get(CROSSREF_BASE + doi, timeout=20)
        r.raise_for_status()
        data = r.json()
        msg = data.get("message", {}) or {}
        # Check if this record belongs to Carino Gurjao
        if is_carino_gurjao_author(msg):
            return msg
        return {}
    except Exception:
        return {}


def crossref_search_title(title: str) -> dict:
    """Search Crossref by title and only accept items authored by Carino Gurjao (ORCID or name variants)."""
    if not title:
        return {}
    try:
        url = f"https://api.crossref.org/works?query.bibliographic={quote_plus(title)}&rows=5"
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        items = (r.json().get("message", {}).get("items", []) or [])
        for item in items:
            if is_carino_gurjao_author(item):
                return item  # accept first matching record
        return {}
    except Exception:
        return {}


def is_carino_gurjao_author(msg: dict) -> bool:
    """
    Check whether a Crossref record lists Carino Gurjao as an author.
    Matches exact ORCID first, then flexible name variants.
    """
    authors = msg.get("author", [])
    for a in authors:
        # --- ORCID match (most reliable) ---
        orcid = (a.get("ORCID") or "").strip().replace("https://orcid.org/", "")
        if orcid == CARINO_GURJAO_ORCID:
            return True

        # --- Flexible name match fallback ---
        full_name = " ".join(
            [a.get("given", ""), a.get("family", ""), a.get("name", "")]
        ).lower()
        full_name = re.sub(r"[^\w\s]", "", full_name)  # normalize punctuation

        # Must contain 'gurjao' and either 'carino' or 'c'
        if "gurjao" in full_name and re.search(r"\b(carino|c)\b", full_name):
            return True

    return False


def extract_from_crossref(msg: dict) -> dict:
    """Normalize the fields we care about from a Crossref record."""
    if not msg:
        return {}

    # Try published print, then published online, then issued
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
    Only enriches if Carino Gurjao is an author.
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
        if val and not out.get(key):
            out[key] = val

    # Map into your YAML schema
    set_if_empty("journal", meta.get("journal"))
    # Keep `venue` synced when journal is present
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
