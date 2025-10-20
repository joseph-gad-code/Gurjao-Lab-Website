#!/usr/bin/env python3
"""
update_publications.py

Fetch all publications from Crossref for author 'Carino Gurjao'
(including variants like 'C. Gurjao' and 'C Gurjao'),
enrich metadata, and safely update _data/publications.yml
without duplicating or overwriting existing entries.
"""

import time
import requests
import yaml
from pathlib import Path
from urllib.parse import quote_plus

# --- Configuration ---
AUTHOR_VARIANTS = [
    "Carino Gurjao",
    "C. Gurjao",
    "C Gurjao"
]

CROSSREF_API = "https://api.crossref.org/works"
DATA_PATH = Path("_data/publications.yml")
REQUEST_PAUSE = 0.3  # be polite to Crossref


# --- Helper functions ---

def fetch_crossref_by_author(name: str) -> list:
    """Fetch works from Crossref by author name."""
    print(f"Fetching publications for author: {name}")
    pubs = []
    cursor = "*"

    try:
        while True:
            url = f"{CROSSREF_API}?query.author={quote_plus(name)}&rows=1000&cursor={cursor}"
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            data = r.json().get("message", {})
            items = data.get("items", [])
            pubs.extend(items)

            print(f"Fetched {len(items)} records (total so far: {len(pubs)})")

            cursor = data.get("next-cursor")
            if not cursor or not items:
                break

            time.sleep(REQUEST_PAUSE)

        return pubs

    except Exception as e:
        print("Error fetching from Crossref:", e)
        return []


def normalize_crossref_entry(entry: dict) -> dict:
    """Extract and simplify the essential fields from a Crossref entry."""
    title = (entry.get("title") or [""])[0]
    authors = []
    for a in entry.get("author", []) or []:
        name = " ".join(filter(None, [a.get("given"), a.get("family")]))
        if name:
            authors.append(name)

    # Determine publication year
    year = None
    for k in ("published-print", "published-online", "issued"):
        dp = (entry.get(k) or {}).get("date-parts", [[]])
        if dp and dp[0]:
            y = dp[0][0]
            if isinstance(y, int):
                year = y
                break

    return {
        "title": title.strip(),
        "authors": authors,
        "journal": (entry.get("container-title") or [""])[0],
        "volume": entry.get("volume", ""),
        "issue": entry.get("issue", ""),
        "pages": entry.get("page", ""),
        "year": year,
        "doi": entry.get("DOI", ""),
        "url": entry.get("URL", ""),
    }


def filter_by_author_variants(entries: list) -> list:
    """Keep only entries where an author matches any variant of 'Carino Gurjao'."""
    filtered = []
    variants_lower = [v.lower() for v in AUTHOR_VARIANTS]

    for entry in entries:
        authors = entry.get("author", []) or []
        for a in authors:
            full_name = " ".join(filter(None, [a.get("given"), a.get("family")])).lower()
            if any(v in full_name for v in variants_lower):
                filtered.append(entry)
                break  # Found one matching author, no need to check further
    return filtered


def load_existing_publications() -> list:
    """Load the current publications.yml (if any)."""
    if not DATA_PATH.exists():
        print("No _data/publications.yml found. Starting fresh.")
        return []
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or []
    except Exception as e:
        print("Error reading existing YAML:", e)
        return []


def is_duplicate(new_pub: dict, existing: list) -> bool:
    """Check if a new publication already exists (by DOI or title match)."""
    new_doi = (new_pub.get("doi") or "").lower()
    new_title = (new_pub.get("title") or "").strip().lower()

    for pub in existing:
        doi = (pub.get("doi") or "").lower()
        title = (pub.get("title") or "").strip().lower()

        if new_doi and doi and new_doi == doi:
            return True
        if new_title and title and new_title == title:
            return True
    return False


def save_publications(publications: list):
    """Write updated publications back to the YAML file."""
    try:
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            yaml.dump(publications, f, sort_keys=False, allow_unicode=True)
        print(f"Saved {len(publications)} publications to {DATA_PATH}")
    except Exception as e:
        print("Error writing publications.yml:", e)


# --- Main execution ---

def main():
    existing_pubs = load_existing_publications()
    print(f"Loaded {len(existing_pubs)} existing publications.")

    all_new_entries = []
    for name in AUTHOR_VARIANTS:
        pubs = fetch_crossref_by_author(name)
        if pubs:
            all_new_entries.extend(pubs)
        time.sleep(REQUEST_PAUSE)

    # Filter duplicates at the raw Crossref level
    unique_entries = {p.get("DOI", p.get("title", "")): p for p in all_new_entries}.values()

    # Keep only entries actually authored by Carino Gurjao variants
    filtered_entries = filter_by_author_variants(list(unique_entries))
    print(f"Filtered down to {len(filtered_entries)} entries with author match.")

    normalized_pubs = [normalize_crossref_entry(p) for p in filtered_entries]
    print(f"Normalized {len(normalized_pubs)} publications from Crossref.")

    merged = existing_pubs[:]
    added_count = 0

    for pub in normalized_pubs:
        if not is_duplicate(pub, merged):
            merged.append(pub)
            added_count += 1

    print(f"Added {added_count} new publications (total now {len(merged)}).")

    # Sort by year descending (most recent first)
    merged.sort(key=lambda x: x.get("year") or 0, reverse=True)

    save_publications(merged)


if __name__ == "__main__":
    main()
