#!/usr/bin/env python3
import os, sys, yaml, requests, re

# ---- CONFIG ----
SERPAPI_API_KEY = os.environ.get("SERPAPI_API_KEY", "")  # or paste your key
GOOGLE_SCHOLAR_USER_ID = "m3rLfS4AAAAJ"                  # GurjaoLab Google Scholar ID
OUT_YAML = "_data/publications.yml"

if not SERPAPI_API_KEY:
    print("ERROR: Set SERPAPI_API_KEY environment variable (or hardcode it).")
    sys.exit(1)

DOI_PATTERN = re.compile(r"(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", re.IGNORECASE)

def extract_doi(text: str):
    if not text:
        return ""
    m = DOI_PATTERN.search(text)
    return m.group(1) if m else ""

def best_link(article: dict):
    """Return the best non-Google Scholar link available."""
    if "link" in article and "scholar.google" not in article["link"]:
        return article["link"]
    for link in article.get("resources", []):
        url = link.get("link")
        if url and "scholar.google" not in url:
            return url
    return article.get("link") or ""

def shorten_authors(authors: str, max_names: int = 3):
    """Truncate long author lists for selected publications."""
    parts = [a.strip() for a in authors.replace("…", "").split(",") if a.strip()]
    if len(parts) > max_names:
        return ", ".join(parts[:max_names]) + ", et al."
    return ", ".join(parts)

def load_existing(path):
    """Load existing YAML file if it exists."""
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or []

def fetch_all_pubs(user_id: str, api_key: str, pages: int = 5):
    """Fetch publications from SerpAPI Google Scholar Author endpoint."""
    all_items = []
    params = {
        "api_key": api_key,
        "engine": "google_scholar_author",
        "author_id": user_id,
        "hl": "en",
        "view_op": "list_works"
    }
    next_params = params.copy()

    for _ in range(pages):
        r = requests.get("https://serpapi.com/search", params=next_params, timeout=30)
        r.raise_for_status()
        data = r.json()
        pubs = data.get("articles", [])
        for a in pubs:
            title = a.get("title") or ""
            authors = a.get("authors", "")
            pubmeta = a.get("publication", "") or ""
            year = None
            try:
                year = int(a.get("year")) if a.get("year") else None
            except Exception:
                year = None

            doi = extract_doi(pubmeta + " " + title)
            url = f"https://doi.org/{doi}" if doi else best_link(a)

            all_items.append({
                "title": title.strip(),
                "authors": authors.strip(),
                "journal": pubmeta.strip(),
                "year": year,
                "url": url,
                "doi": doi,
                "selected_publication": False,
                "image": ""
            })

        next_link = data.get("serpapi_pagination", {}).get("next")
        if not next_link:
            break
        next_params = dict([p.split("=") for p in next_link.split("search?")[1].split("&")])

    return all_items

def merge_publications(old_list, new_list):
    """Merge existing and new publications without losing manual edits."""
    merged = {p["title"].strip().lower(): p for p in old_list}

    for new_pub in new_list:
        key = new_pub["title"].strip().lower()
        if key in merged:
            old_pub = merged[key]
            # Preserve manually curated fields
            for field in ["selected_publication", "image", "doi"]:
                if old_pub.get(field):
                    new_pub[field] = old_pub[field]
            # Preserve custom author shortening if selected
            if new_pub.get("selected_publication", False):
                new_pub["authors"] = shorten_authors(new_pub["authors"])
        merged[key] = new_pub
    return list(merged.values())

def write_yaml(items, path):
    items = sorted(items, key=lambda x: x.get("year") or 0, reverse=True)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(items, f, sort_keys=False, allow_unicode=True)

def main():
    print("Fetching updated publications from Google Scholar via SerpAPI...")
    new_pubs = fetch_all_pubs(GOOGLE_SCHOLAR_USER_ID, SERPAPI_API_KEY, pages=6)
    old_pubs = load_existing(OUT_YAML)
    merged = merge_publications(old_pubs, new_pubs)
    write_yaml(merged, OUT_YAML)
    print(f"Wrote {OUT_YAML} with {len(merged)} items (merged from {len(old_pubs)} existing).")

if __name__ == "__main__":
    main()
