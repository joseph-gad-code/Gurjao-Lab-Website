import os
import time
import requests
import yaml
from urllib.parse import quote_plus

# --- Configuration ---
DATA_PATH = "_data/publications.yml"
CROSSREF_BASE = "https://api.crossref.org/works/"
REQUEST_PAUSE = 0.4  # polite delay between API calls

# ---------------------------------------------------------------------
# --- Crossref access helpers ---
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
        # Filter only those containing "C. Gurjao" or "Carino Gurjao"
        for item in items:
            authors = extract_authors(item)
            if any(is_carino_gurjao(a) for a in authors):
                return item
        return {}
    except Exception:
        return {}

# ---------------------------------------------------------------------
# --- Author parsing and filtering logic ---
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

def is_carino_gurjao(name: str) -> bool:
    """
    Return True if the author's name corresponds to Carino Gurjao or a valid variant:
      - Must contain 'Gurjao' (case-insensitive)
      - Must have first name or initial starting with 'C' (no others)
    """
    parts = name.strip().split()
    if len(parts) < 2:
        return False
    family = parts[-1].lower()
    first = parts[0].lower().replace(".", "")
    return (family == "gurjao") and first.startswith("c") and not first.startswith("e")  # exclude wrong initials

# ---------------------------------------------------------------------
# --- Metadata normalization ---
# ---------------------------------------------------------------------

def extract_from_crossref(msg: dict) -> dict:
    """Normalize relevant metadata from Crossref."""
    if not msg:
        return {}

    # Try multiple date fields
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
# --- Publication enrichment ---
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
# --- YAML file update ---
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
        # Only keep records containing a valid "C. Gurjao" or "Carino Gurjao"
        if any(is_carino_gurjao(a) for a in authors):
            updated.append(enriched)

    save_yaml(DATA_PATH, updated)
    print(f"✅ Updated {len(updated)} publications containing Carino Gurjao (or valid variants).")

# ---------------------------------------------------------------------
if __name__ == "__main__":
    main()
