/**
 * Fetches publications from a public Google Scholar profile and merges
 * into _data/publications.yml, preserving:
 *  - selected_publication
 *  - image
 *
 * Journal link is stored in `venue_link` (we use the Scholar cluster link).
 */
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const yaml = require('js-yaml');

const USER = process.env.SCHOLAR_USER_ID || 'm3rLfS4AAAAJ';
const URL  = `https://scholar.google.com/citations?user=${USER}&hl=en&cstart=0&pagesize=1000`;

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
  fs.writeFileSync(file, text);
}

(async () => {
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 120000 });

  // Try to reveal more rows if present
  for (let i = 0; i < 12; i++) {
    const more = page.locator('text=Show more');
    if (await more.count()) {
      await more.first().click();
      await page.waitForTimeout(700);
    } else break;
  }

  const scraped = await page.evaluate(() => {
    const rows = Array.from(document.querySelectorAll('#gsc_a_b .gsc_a_tr'));
    return rows.map(r => {
      const at = r.querySelector('.gsc_a_at');
      const title = at ? at.textContent.trim() : '';
      const titleLink = at ? at.href : '';
      const authors = r.querySelector('.gsc_a_t .gs_gray')?.textContent?.trim() || '';
      const venue = r.querySelector('.gsc_a_t .gs_gray:nth-child(2)')?.textContent?.trim() || '';
      const year  = parseInt((r.querySelector('.gsc_a_y span')?.textContent || '').trim(), 10) || null;

      // derive a stable-ish id
      let id = '';
      try {
        const m = new URL(titleLink).searchParams.get('cluster');
        id = m ? `scholar_${m}` : `scholar_${title.toLowerCase().replace(/[^a-z0-9]+/g,'-').slice(0,60)}`;
      } catch (e) {
        id = `scholar_${title.toLowerCase().replace(/[^a-z0-9]+/g,'-').slice(0,60)}`;
      }
      return { id, title, authors, venue, year, venue_link: titleLink };
    });
  });

  await browser.close();

  // Merge with existing YAML, preserving selection/image
  const existing = readYamlSafe(dataPath);
  const keep = new Map(existing.map(p => [p.id, p]));
  const merged = scraped.map(s => {
    const prev = keep.get(s.id) || {};
    return {
      id: s.id,
      title: s.title || prev.title,
      authors: s.authors || prev.authors,
      venue: s.venue || prev.venue,
      year: s.year || prev.year,
      venue_link: s.venue_link || prev.venue_link,
      selected_publication: prev.selected_publication === true, // default false
      image: prev.image || ''
    };
  });

  // If any old entries are missing from the new scrape (rare), keep them
  for (const [id, prev] of keep.entries()) {
    if (!merged.find(p => p.id === id)) merged.push(prev);
  }

  // newest first in file
  merged.sort((a, b) => (b.year || 0) - (a.year || 0));

  fs.mkdirSync(path.dirname(dataPath), { recursive: true });
  writeYaml(dataPath, merged);
  console.log(`Synced ${merged.length} publications -> ${dataPath}`);
})();
