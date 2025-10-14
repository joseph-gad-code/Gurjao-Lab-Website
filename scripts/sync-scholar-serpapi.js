/**
 * Sync Google Scholar publications using SerpAPI (reliable for CI).
 * Preserves:
 *  - selected_publication
 *  - image
 *
 * Env:
 *  SERPAPI_KEY (required)
 *  SCHOLAR_AUTHOR_ID (Google Scholar "user" id, e.g., m3rLfS4AAAAJ)
 */

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');
const { GoogleSearchResults } = require('google-search-results-nodejs');

const KEY = process.env.SERPAPI_KEY;
const AUTHOR_ID = process.env.SCHOLAR_AUTHOR_ID || 'm3rLfS4AAAAJ';

if (!KEY) {
  console.error('Missing SERPAPI_KEY in environment.');
  process.exit(1);
}

const client = new GoogleSearchResults(KEY);
const dataPath = path.join(process.cwd(), '_data', 'publications.yml');

function readYamlSafe(file) {
  try {
    return yaml.load(fs.readFileSync(file, 'utf8')) || [];
  } catch {
    return [];
  }
}
function writeYaml(file, obj) {
  const text = yaml.dump(obj, { lineWidth: 1000, noRefs: true, sortKeys: false });
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, text);
}

function normId(obj) {
  // Prefer cluster_id/serpapi_id if present; fallback to slugified title
  const cluster = obj?.cluster_id || obj?.serpapi_pagination?.next || '';
  if (cluster) return `scholar_${String(cluster).replace(/[^a-zA-Z0-9]+/g, '-')}`;
  const title = (obj?.title || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 60);
  return `scholar_${title || Math.random().toString(36).slice(2)}`;
}

function merge(existingArr, scrapedArr) {
  const existing = new Map(existingArr.map(p => [p.id, p]));
  const merged = scrapedArr.map(s => {
    const prev = existing.get(s.id) || {};
    return {
      id: s.id,
      title: s.title || prev.title,
      authors: s.authors || prev.authors,
      venue: s.venue || prev.venue,
      year: s.year || prev.year,
      venue_link: s.venue_link || prev.venue_link,
      selected_publication: prev.selected_publication === true,
      image: prev.image || ''
    };
  });
  // Keep any old entries not seen this scrape (rare)
  for (const [id, prev] of existing.entries()) {
    if (!merged.find(p => p.id === id)) merged.push(prev);
  }
  // Sort newest first
  merged.sort((a, b) => (b.year || 0) - (a.year || 0));
  return merged;
}

async function fetchAllPublications() {
  // SerpAPI: https://serpapi.com/google-scholar-api
  // We’ll use "google_scholar_author" engine and paginate until done.
  const paramsBase = {
    engine: 'google_scholar_author',
    author_id: AUTHOR_ID,
    sort: 'pubdate', // newest first
    hl: 'en',
    num: 100
  };

  let publications = [];
  let nextParams = { ...paramsBase };
  for (let i = 0; i < 10; i++) {
    const page = await new Promise((resolve, reject) => {
      client.json(nextParams, (json) => resolve(json));
    });

    const items = (page?.articles || []).map(a => {
      // SerpAPI returns fields like: title, authors, publication, year, link, etc.
      return {
        raw: a,
        id: normId(a),
        title: a.title || '',
        authors: (a.authors || []).map(x => x.name).join(', '),
        venue: a.publication || a.journal || '',
        year: a.year ? Number(a.year) : null,
        venue_link: a.link || a.result_id ? a.link : ''
      };
    });

    publications.push(...items);

    // pagination
    const nextLink = page?.serpapi_pagination?.next;
    if (!nextLink) break;
    // SerpAPI lets us pass page token directly by URL; simpler is to follow the index offset.
    // We’ll switch to `start` if provided:
    if (page?.serpapi_pagination?.current) {
      const start = Number(page.serpapi_pagination.current) * (paramsBase.num || 100);
      nextParams = { ...paramsBase, start };
    } else {
      break;
    }
  }

  // Deduplicate by id
  const uniq = new Map(publications.map(p => [p.id, p]));
  return Array.from(uniq.values()).map(p => ({
    id: p.id,
    title: p.title,
    authors: p.authors,
    venue: p.venue,
    year: p.year,
    venue_link: p.venue_link
  }));
}

(async () => {
  try {
    const scraped = await fetchAllPublications();
    const current = readYamlSafe(dataPath);
    const merged = merge(current, scraped);
    writeYaml(dataPath, merged);
    console.log(`Synced ${merged.length} publications to ${dataPath}`);
  } catch (err) {
    console.error('Sync failed:', err);
    process.exit(1);
  }
})();
