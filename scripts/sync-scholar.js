const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');
const cheerio = require('cheerio');

const USER = process.env.SCHOLAR_USER_ID || 'm3rLfS4AAAAJ';
const BASE = `https://scholar.google.com/citations?user=${USER}&hl=en`;
const DATA_PATH = path.join(process.cwd(), '_data', 'publications.yml');

const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const norm = s => (s || '').toLowerCase().replace(/\s+/g, ' ').trim();

function loadYaml(file) {
  try {
    if (fs.existsSync(file)) {
      const text = fs.readFileSync(file, 'utf8');
      const data = yaml.load(text) || [];
      return Array.isArray(data) ? data : [];
    }
  } catch (e) {
    console.warn('YAML load warning:', e.message);
  }
  return [];
}

function saveYaml(file, data) {
  const yml = yaml.dump(data, { lineWidth: 1000, noRefs: true });
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, yml);
}

async function fetchPage(url) {
  const res = await fetch(url, {
    headers: {
      'User-Agent':
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121 Safari/537.36'
    }
  });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return await res.text();
}

async function scrapeAll() {
  const results = [];
  // Scholar shows 100 per page when pagesize=100; iterate until empty or 20 pages max
  for (let start = 0; start < 2000; start += 100) {
    const url = `${BASE}&cstart=${start}&pagesize=100`;
    const html = await fetchPage(url);
    const $ = cheerio.load(html);
    const rows = $('#gsc_a_b .gsc_a_tr');
    if (rows.length === 0) break;

    rows.each((_, el) => {
      const titleNode = $(el).find('.gsc_a_at').first();
      const title = titleNode.text().trim();
      const link = titleNode.attr('href')
        ? new URL(titleNode.attr('href'), 'https://scholar.google.com').toString()
        : '';

      const meta1 = $(el).find('.gsc_a_t .gs_gray').first().text().trim();       // authors
      const meta2 = $(el).find('.gsc_a_t .gs_gray').eq(1).text().trim();         // venue/year-ish
      const yearText = $(el).find('.gsc_a_y span').text().trim();
      const year = parseInt(yearText, 10) || null;

      results.push({
        title,
        authors: meta1,
        venue: meta2,
        year,
        link
      });
    });

    // polite delay
    await sleep(700);
  }
  return results;
}

(async () => {
  try {
    const scraped = await scrapeAll();
    if (!scraped.length) throw new Error('No publications scraped from Scholar.');

    const existing = loadYaml(DATA_PATH);
    const byTitle = new Map(existing.map(e => [norm(e.title), e]));

    for (const s of scraped) {
      const key = norm(s.title);
      if (!key) continue;
      const prev = byTitle.get(key);
      if (prev) {
        prev.title   = s.title || prev.title;
        prev.authors = s.authors || prev.authors;
        prev.venue   = s.venue   || prev.venue;
        prev.year    = s.year    || prev.year;
        prev.link    = s.link    || prev.link;
      } else {
        byTitle.set(key, {
          title: s.title,
          authors: s.authors,
          venue: s.venue,
          year: s.year,
          link: s.link,
          selected_publication: false
        });
      }
    }

    const merged = Array.from(byTitle.values())
      .sort((a, b) => (b.year || 0) - (a.year || 0));

    saveYaml(DATA_PATH, merged);
    console.log(`Merged ${merged.length} publications into ${DATA_PATH}`);
  } catch (err) {
    console.error('Sync failed:', err.stack || err.message);
    process.exit(1);
  }
})();
