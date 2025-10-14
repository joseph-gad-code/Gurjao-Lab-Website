#!/usr/bin/env node
/**
 * Scrape Google Scholar profile → _data/publications.yml
 * No API key needed. Uses headless Chrome with stealth plugin.
 *
 * Usage:
 *   node scripts/sync-scholar.js <SCHOLAR_USER_ID>
 * or set env SCHOLAR_USER=xxxx
 */

const fs = require("fs");
const path = require("path");
const yaml = require("js-yaml");
const puppeteer = require("puppeteer-extra");
const StealthPlugin = require("puppeteer-extra-plugin-stealth");

puppeteer.use(StealthPlugin());

const USER = process.env.SCHOLAR_USER || process.argv[2];
if (!USER) {
  console.error("Missing SCHOLAR_USER. Pass as env or arg. Example: SCHOLAR_USER=m3rLfS4AAAAJ");
  process.exit(1);
}

const OUT_FILE = path.join(process.cwd(), "_data", "publications.yml");

function normTitle(s) {
  return (s || "").trim().replace(/\s+/g, " ").toLowerCase();
}

async function loadExisting() {
  try {
    const t = fs.readFileSync(OUT_FILE, "utf8");
    const data = yaml.load(t) || [];
    const byTitle = new Map();
    data.forEach(p => byTitle.set(normTitle(p.title), p));
    return { list: data, map: byTitle };
  } catch {
    return { list: [], map: new Map() };
  }
}

async function scrapeScholar() {
  const url = `https://scholar.google.com/citations?user=${encodeURIComponent(
    USER
  )}&hl=en&view_op=list_works&sortby=pubdate`;

  const browser = await puppeteer.launch({
    headless: "new",
    args: ["--no-sandbox", "--disable-setuid-sandbox"]
  });
  const page = await browser.newPage();
  await page.setUserAgent(
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
  );

  await page.goto(url, { waitUntil: "networkidle2", timeout: 120000 });
  await page.waitForSelector("#gsc_bdy", { timeout: 60000 });

  // Keep clicking “Show more” until it disappears or a sane upper bound
  for (let i = 0; i < 50; i++) {
    const hasMore = await page.$("#gsc_bpf_more:not([disabled])");
    if (!hasMore) break;
    await page.click("#gsc_bpf_more");
    await page.waitForTimeout(800);
  }

  const rows = await page.$$(".gsc_a_tr");
  const results = [];
  for (const row of rows) {
    const titleEl = await row.$(".gsc_a_at");
    const title = titleEl ? (await page.evaluate(el => el.textContent, titleEl)).trim() : "";

    const href = titleEl ? await page.evaluate(el => el.href, titleEl) : "";

    // authors + venue live in .gs_gray elements under .gsc_a_t
    const meta = await row.$$eval(".gsc_a_t .gs_gray", els => els.map(e => e.textContent.trim()));
    const authors = meta[0] || "";
    const venue = meta[1] || "";

    // year is in .gsc_a_y span
    const yearText = await row.$eval(".gsc_a_y span", el => el.textContent.trim()).catch(() => "");
    const year = yearText ? parseInt(yearText, 10) : undefined;

    results.push({
      title,
      authors,
      venue,
      year,
      url: href
    });
  }

  await browser.close();
  return results;
}

function merge(existingMap, scraped) {
  // Keep selected-publication and image if already defined in existing.
  return scraped
    .map(p => {
      const current = existingMap.get(normTitle(p.title));
      if (current) {
        return {
          ...p,
          image: current.image || "",
          "selected-publication":
            current["selected-publication"] === "yes" || current["selected-publication"] === true
              ? "yes"
              : "no"
        };
      }
      return { ...p, image: "", "selected-publication": "no" };
    })
    .sort((a, b) => (b.year || 0) - (a.year || 0));
}

(async () => {
  console.log("Scraping Scholar for user:", USER);
  const existing = await loadExisting();
  const scraped = await scrapeScholar();
  const merged = merge(existing.map, scraped);

  const yamlText = yaml.dump(merged, { lineWidth: 1000, sortKeys: false });
  fs.mkdirSync(path.dirname(OUT_FILE), { recursive: true });
  fs.writeFileSync(OUT_FILE, yamlText, "utf8");

  console.log(`Wrote ${merged.length} records to ${OUT_FILE}`);
})();
