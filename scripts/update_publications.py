import os
import time
import re
import requests
import yaml
from urllib.parse import quote_plus

# --- Configuration ---
DATA_PATH = "_data/publications.yml"
CROSSREF_BASE = "https://api.crossref.org/works/"
REQUEST_PAUSE = 0.4  # polite delay between API calls

# ---------------------------------------------------------------------
# --- Crossref helpers ---
# ---------------------------------------------------------------------

def crossref_get(doi: str) -> dict:
    """Fetch a single Crossref record by DOI."""
    if not doi:
        return {}
    try:
        r = requests.get(CROSSREF_BASE + doi, timeout=20)
        r.raise_for_status()
        return r.json().get("message", {}) or {}
    except Exception:
        return {}

def crossref_search_title(title: str) -> dict:
    """Fallback: search Crossref by title and return the best match."""
    if not title:
        return {}
    try:
        url = f"https://api.crossref.org/works?query.bibliographic={quote_plus(title)}&rows=5"
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        items = r.json().get("message", {}).get("items", []) or []
        for item in items:
            authors = extract_authors(item)
            if any(is_carino_gurjao_strict(a) for a in authors):
                return item
        return {}
    except Exception:
        return {}

# ---------------------------------------------------------------------
# --- Author parsing and strict filtering ---
# ---------------------------------------------------------------------

def extract_authors(msg: dict) -> list[str]:
    """Extract full author names from a Crossref record."""
    authors = []
    for a in msg.get("author", []) or []:
        given = a.get("given", "").strip()
        family = a.get("family", "").strip()
        full_name = " ".join(x for x in [given, family] if x)
        if full_name:
            authors.append(full_name)
    return authors

def normalize_author_name(name: str) -> str:
    """Normalize an author name for consistent comparison."""
    name = re.sub(r"\s+", " ", name.strip())
    name = re.sub(r"\s*,\s*", ", ", name)
    name = re.sub(r"\s*\.\s*", ". ", name)
    return name.strip()

def is_carino_gurjao_strict(name: str) -> bool:
    """
    Return True only for exact known variants of 'Carino Gurjao' or 'C. Gurjao' (and reversals).
    Accepts punctuation and spacing variations.
    """
    name = normalize_author_name(name).lower()

    valid_variants = {
        "carino gurjao",
        "c. gurjao",
        "c gurjao",
        "gurjao, carino",
        "gurjao, c.",
        "gurjao, c",
        "gurjao c.",
        "gurjao c",
    }

    # Remove extra spaces and periods for comparison
    name_nopunct = re.sub(r"[.\s]", "", name)
    variants_nopunct = {re.sub(r"[.\s]", "", v) for v in valid_variants}

    return name in valid_variants or name_nopunct in variants_nopunct

# ---------------------------------------------------------------------
# --- Metadata normalization ---
# ---------------------------------------------------------------------

def extract_from_crossref(msg: dict) -> dict:
    """Normalize relevant metadata from Crossref."""
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

    authors = extract_authors(msg)

    return {
        "title": msg.get("title", [""])[0],
        "authors": authors,
        "journal": (msg.get("container-title") or [""])[0],
        "volume": msg.get("volume") or "",
        "issue": msg.get("issue") or "",
        "pages": msg.get("page") or "",
        "year": year,
        "url": msg.get("URL") or "",
        "doi": msg.get("DOI") or "",
    }

# ---------------------------------------------------------------------
# --- Enrichment ---
# ---------------------------------------------------------------------

def enrich_with_crossref(pub: dict) -> dict:
    """Fill missing fields in one publication record using Crossref."""
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
    if not msg:
        return out

    meta = extract_from_crossref(msg)
    if not meta:
        return out

    def set_if_empty(k, v):
        if v and not out.get(k):
            out[k] = v

    for k in ("journal", "volume", "issue", "pages", "year", "url", "doi", "authors", "title"):
        set_if_empty(k, meta.get(k))

    return out

# ---------------------------------------------------------------------
# --- YAML helpers ---
# ---------------------------------------------------------------------

def load_yaml(path: str) -> list:
    """Load publications YAML file."""
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or []

def save_yaml(path: str, data: list):
    """Save updated publications to YAML."""
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True, width=120)

# ---------------------------------------------------------------------
# --- Main logic ---
# ---------------------------------------------------------------------

def main():
    publications = load_yaml(DATA_PATH)
    updated = []

    for pub in publications:
        enriched = enrich_with_crossref(pub)
        authors = enriched.get("authors", [])
        if any(is_carino_gurjao_strict(a) for a in authors):
            updated.append(enriched)

    save_yaml(DATA_PATH, updated)
    print(f"Updated {len(updated)} publications containing Carino Gurjao (strict name matching).")

# ---------------------------------------------------------------------
if __name__ == "__main__":
    main()
