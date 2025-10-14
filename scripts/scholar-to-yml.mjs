// scripts/scholar-to-yml.mjs
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import axios from "axios";
import yaml from "js-yaml";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ---- Config ----
const AUTHOR_ID = "m3rLfS4AAAAJ"; // your Scholar author id
const SERPAPI_KEY = process.env.SERPAPI_KEY;
if (!SERPAPI_KEY) {
  console.error("Missing SERPAPI_KEY env var.");
  process.exit(1);
}

const OUT_PATH = path.join(__dirname, "..", "_data", "publications.yml");

// load existing to preserve selected_publication + image
let existing = { publications: [] };
if (fs.existsSync(OUT_PATH)) {
  try {
    existing = yaml.load(fs.readFileSync(OUT_PATH, "utf8")) || { publications: [] };
  } catch {
    existing = { publications: [] };
  }
}
const existingById = new Map(
  existing.publications.map(p => [String(p.id || ""), p])
);

// fetch all pages from SerpAPI
async function fetchAll() {
  const base = "https://serpapi.com/search.json";
  let page = 1;
  const perPage = 100;
  let results = [];
  while (true) {
    const { data } = await axios.get(base, {
      params: {
        engine: "google_scholar_author",
        author_id: AUTHOR_ID,
        sort: "pubdate",
        num: perPage,
        start: (page - 1) * perPage,
        api_key: SERPAPI_KEY,
        hl: "en",
      },
      timeout: 30000,
    });

    const pubs = (data.articles || []).map(a => ({
      id: String(a.result_id || a.citation_id || a.position || Math.random().toString(36).slice(2)),
      title: a.title || "",
      authors: a.authors || "",
      year: a.year ? Number(a.year) : null,
      journal: a.publication || "",
      url: a.link || "",
    }));

    results.push(...pubs);

    // stop condition
    if (!data.serpapi_pagination || !data.serpapi_pagination.next) break;
    page += 1;
    // safety
    if (page > 10) break;
  }
  return results;
}

const fetched = await fetchAll();

// merge + preserve flags and images
const merged = fetched.map(p => {
  const prev = existingById.get(String(p.id));
  return {
    ...p,
    selected_publication: prev?.selected_publication || false,
    image: prev?.image || "",
  };
});

// write YAML
const out = { publications: merged.sort((a, b) => (b.year || 0) - (a.year || 0)) };
fs.writeFileSync(OUT_PATH, yaml.dump(out, { lineWidth: 1000 }), "utf8");
console.log(`Wrote ${out.publications.length} publications to ${OUT_PATH}`);
