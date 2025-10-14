#!/usr/bin/env python3
import os, sys, json, requests, yaml

# ---- CONFIG ----
SERPAPI_API_KEY = os.environ.get("SERPAPI_API_KEY", "")  # or paste your key as a string
GOOGLE_SCHOLAR_USER_ID = "m3rLfS4AAAAJ"                  # GurjaoLab Google Scholar user id
OUT_YAML = "_data/publications.yml"

if not SERPAPI_API_KEY:
    print("ERROR: Set SERPAPI_API_KEY environment variable (or hardcode it in the script).")
    sys.exit(1)

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
            link = a.get("link") or ""
            authors = a.get("authors", "")
            pubmeta = a.get("publication", "")
            year = None
            try:
                year = int(a.get("year")) if a.get("year") else None
            except Exception:
                year = None

            all_items.append({
                "title": title,
                "authors": authors,
                "journal": pubmeta,
                "year": year,
                "url": link,
                "doi": "",
                "selected_publication": False,
                "image": ""
            })
        # pagination
        next_link = data.get("serpapi_pagination", {}).get("next")
        if not next_link:
            break
        # SerpAPI gives next page via "next" full URL
        next_params = dict([p.split("=") for p in next_link.split("search?")[1].split("&")])

    return all_items

def write_yaml(items, path):
    # sort newest first
    items = sorted(items, key=lambda x: x.get("year") or 0, reverse=True)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(items, f, sort_keys=False, allow_unicode=True)

def main():
    pubs = fetch_all_pubs(GOOGLE_SCHOLAR_USER_ID, SERPAPI_API_KEY, pages=6)
    write_yaml(pubs, OUT_YAML)
    print(f"Wrote {OUT_YAML} with {len(pubs)} items.")

if __name__ == "__main__":
    main()
