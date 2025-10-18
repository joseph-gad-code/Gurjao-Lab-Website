#!/usr/bin/env python3
import os
import sys
import yaml
import requests
import re
import traceback

# ---- CONFIG ----
SERPAPI_API_KEY = os.environ.get("SERPAPI_API_KEY", "")
GOOGLE_SCHOLAR_USER_ID = "m3rLfS4AAAAJ"
OUT_YAML = "_data/publications.yml"

if not SERPAPI_API_KEY:
    print("ERROR: SERPAPI_API_KEY environment variable not set.")
    sys.exit(1)

# ---- HELPERS ----
DOI_PATTERN = re.compile(r"(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", re.IGNORECASE)

def extract_doi(text: str):
    if not text:
        return ""
    m = DOI_PATTERN.search(text)
    return m.group(1) if m else ""

def best_link(article: dict):
    """Return best non-Google Scholar link."""
    if "link" in article and "scholar.google" not in article["link"]:
        return article["link"]
    for link in article.get("resources", []):
        url = link.get("link")
        if url and "scholar.google" not in url:
            return url
    return article.get("link") or ""

def shorten_authors(authors: str, max_names: int = 3):
    parts = [a.strip() for a in authors.replace("…", "").split(",") if a.strip()]
    if len(parts) > max_names:
        return ", ".join(parts[:max_names]) + ", et al."
    return ", ".join(parts)

def load_existing(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or []
    except Exception as e:
        print(f"Warning: Could not parse {path}: {e}")
        return []

def write_yaml(items, path):
    items = sorted(items, key=lambda x: x.get("year") or 0, reverse=True)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(items, f, sort_keys=False, allow_unicode=True)

# ---- FETCH ----
def fetch_all_pubs(user_id: str, api_key: str, pages: int = 5):
    """Fetch publications from SerpAPI Google Scholar Author endpoint."""
    print(f"Fetching Google Scholar data for user_id={user_id}")
    all_items = []
    params = {
        "api_key": api_key,
        "engine": "google_scholar_author",
        "author_id": user_id,
        "hl": "en",
        "view_op": "list_works"
    }

    for page in range(pages):
        print(f"Requesting page {page + 1}...")
        r = requests.get("https://serpapi.com/search", params=params, timeout=30)
        try:
            data = r.json()
        except Exception:
            print("Failed to parse JSON. Response:")
            print(r.text[:500])
            raise RuntimeError("SerpAPI returned non-JSON (likely invalid API key or rate limit).")

        if "error" in data:
            raise RuntimeError(f"SerpAPI error: {data['error']}")

        pubs = data.get("articles", [])
        if not pubs:
            print("No articles found on this page.")
            break

        for a in pubs:
            title = a.get("title", "").strip()
            authors = a.get("authors", "").strip()
            pubmeta = a.get("publication", "").strip()
            year = None
            try:
                year = int(a.get("year")) if a.get("year") else None
            except Exception:
                year = None

            doi = extract_doi(pubmeta + " " + title)
            url = f"https://doi.org/{doi}" if doi else best_link(a)

            all_items.append({
                "title": title,
                "authors": authors,
                "journal": pubmeta,
                "year": year,
                "url": url,
                "doi": doi,
                "selected_publication": False,
                "image": ""
            })

        next_link = data.get("serpapi_pagination", {}).get("next")
        if not next_link:
            print("No more pages.")
            break

        # Safely parse pagination parameters
        try:
            after_search = next_link.split("search?")[1]
            parts = [p.split("=", 1) for p in after_search.split("&") if "=" in p]
            params.update(dict(parts))
        except Exception as e:
            print(f"Warning: Could not parse pagination link: {e}")
            break

    print(f"Retrieved {len(all_items)} total publications.")
    return all_items

def merge_publications(old_list, new_list):
    merged = {p["title"].strip().lower(): p for p in old_list}

    for new_pub in new_list:
        key = new_pub["title"].strip().lower()
        if key in merged:
            old_pub = merged[key]
            for field in ["selected_publication", "image", "doi"]:
                if old_pub.get(field):
                    new_pub[field] = old_pub[field]
            if new_pub.get("selected_publication", False):
                new_pub["authors"] = shorten_authors(new_pub["authors"])
        merged[key] = new_pub
    return list(merged.values())

# ---- MAIN ----
def main():
    print("Starting publication update...")
    new_pubs = fetch_all_pubs(GOOGLE_SCHOLAR_USER_ID, SERPAPI_API_KEY, pages=6)
    old_pubs = load_existing(OUT_YAML)
    print(f"Loaded {len(old_pubs)} existing publications.")
    merged = merge_publications(old_pubs, new_pubs)
    write_yaml(merged, OUT_YAML)
    print(f"Wrote {OUT_YAML} with {len(merged)} items (merged from {len(old_pubs)}).")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ERROR running update_publications.py:")
        print(e)
        traceback.print_exc()
        sys.exit(2)
