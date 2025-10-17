#!/usr/bin/env python3
import os, sys, json, requests, yaml, re

# ---- CONFIG ----
SERPAPI_API_KEY = os.environ.get("SERPAPI_API_KEY", "")  # or paste your key
GOOGLE_SCHOLAR_USER_ID = "m3rLfS4AAAAJ"                  # GurjaoLab user id
OUT_YAML = "_data/publications.yml"

if not SERPAPI_API_KEY:
    print("ERROR: Set SERPAPI_API_KEY environment variable (or hardcode it in the script).")
    sys.exit(1)

DOI_PATTERN = re.compile(r"(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", re.IGNORECASE)

def extract_doi(text: str):
    """Extract DOI from any field string if present."""
    if not text:
        return ""
    m = DOI_PATTERN.search(text)
    return m.group(1) if m else ""

def best_link(article: dict):
    """Try to pick a non-Google Scholar link when possible."""
    # Prefer direct DOI link if found
    if "link" in article and "scholar.google" not in article["link"]:
        return article["link"]
    for link in article.get("resources", []):
        url = link.get("link")
        if url and "scholar.google" not in url:
            return url
    return article.get("link") or ""

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
                "title": title,
                "authors": authors,
                "journal": pubmeta,
                "year": year,
                "url": url,
                "doi": doi,
                "selected_publication": False,
                "image": ""
            })
        # pagination
        next_link = data.get("serpapi_pagination", {}).get("next")
        if not next_link:
            break
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
#!/usr/bin/env python3
import os, sys, json, requests, yaml, re

# ---- CONFIG ----
SERPAPI_API_KEY = os.environ.get("SERPAPI_API_KEY", "")  # or paste your key
GOOGLE_SCHOLAR_USER_ID = "m3rLfS4AAAAJ"                  # GurjaoLab user id
OUT_YAML = "_data/publications.yml"

if not SERPAPI_API_KEY:
    print("ERROR: Set SERPAPI_API_KEY environment variable (or hardcode it in the script).")
    sys.exit(1)

DOI_PATTERN = re.compile(r"(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", re.IGNORECASE)

def extract_doi(text: str):
    """Extract DOI from any field string if present."""
    if not text:
        return ""
    m = DOI_PATTERN.search(text)
    return m.group(1) if m else ""

def best_link(article: dict):
    """Try to pick a non-Google Scholar link when possible."""
    # Prefer direct DOI link if found
    if "link" in article and "scholar.google" not in article["link"]:
        return article["link"]
    for link in article.get("resources", []):
        url = link.get("link")
        if url and "scholar.google" not in url:
            return url
    return article.get("link") or ""

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
                "title": title,
                "authors": authors,
                "journal": pubmeta,
                "year": year,
                "url": url,
                "doi": doi,
                "selected_publication": False,
                "image": ""
            })
        # pagination
        next_link = data.get("serpapi_pagination", {}).get("next")
        if not next_link:
            break
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
