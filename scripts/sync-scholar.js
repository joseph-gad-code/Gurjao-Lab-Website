// Merge publications collected from Google Scholar into _data/publications.yml
const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');
const { chromium } = require('playwright');

const USER = process.env.SCHOLAR_USER_ID || 'm3rLfS4AAAAJ';
const URL  = `https://scholar.google.com/citations?user=${USER}&hl=en&cstart=0&pagesize=1000`;

const DATA_PATH = path.join(process.cwd(), '_data', 'publications.yml');

function loadYaml(file) {
  try {
    if (fs.existsSync(file)) {
      const txt = fs.readFileSync(file, 'utf8').trim();
      if (!txt) return [];
      const data = yaml.load(txt);
      return Array.isArray(data) ? data : [];
    }
  } catch (e) { console.warn('YAML load error:', e.message); }
  return [];
}

function saveYaml(file, data) {
  const yml = yaml.dump(data, { lineWidth: 1000, noRefs: true });
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, yml);
}

function normTitle(t) {
  return (t || '').toLowerCase().replace(/\s+/g, ' ').trim();
}

(async () => {
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 120000 });

  // Click "Show more" if present a few times
  for (let i = 0; i < 8; i++) {
    const more = page.locator('text=Show more');
    if (await more.count()) {
      await more.first().click();
      await page.waitForTimeout(700);
    } else break;
  }

  const scraped = await page.evaluate(() => {
    const rows = Array.from(document.querySelectorAll('#gsc_a_b .gsc_a_tr'));
    return rows.map(r => {
      const t = r.querySelector('.gsc_a_at');
      const title = t ? t.textContent.trim() : '';
      const link  = t ? t.href : '';
      const authors = r.querySelector('.gsc_a_t .gs_gray')?.textContent?.trim() || '';
      const venue   = r.querySelector('.gsc_a_t .gs_gray:nth-child(2)')?.textContent?.trim() || '';
      const year    = parseInt((r.querySelector('.gsc_a_y span')?.textContent || '').trim(), 10) || null;
      return { title, authors, venue, year, link };
    });
  });

  await browser.close();

  // Load current YAML and index by normalized title
  const existing = loadYaml(DATA_PATH);
  const byTitle  = new Map(existing.map(e => [normTitle(e.title), e]));

  // Merge/insert
  for (const s of scraped) {
    const key = normTitle(s.title);
    if (!key) continue;

    const prev = byTitle.get(key);
    if (prev) {
      // Update Scholar-managed fields, preserve your custom fields
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
        selected_publication: false,   // default for new items
        // image / blurb can be added later by you
      });
    }
  }

  // Sort newest first in file (nicer to review in Git)
  const merged = Array.from(byTitle.values())
    .sort((a, b) => (b.year || 0) - (a.year || 0));

  saveYaml(DATA_PATH, merged);
  console.log(`Merged ${merged.length} publications into ${DATA_PATH}`);
})();
