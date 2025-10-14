#!/usr/bin/env node
/**
 * Playwright-based Google Scholar scraper -> _data/publications.yml
 * Robust in GitHub Actions. No API keys.
 */
const fs = require("fs");
const path = require("path");
const yaml = require("js-yaml");
const { chromium } = require("playwright");

const USER = process.env.SCHOLAR_USER || process.argv[2];
if (!USER) {
  console.error("Missing SCHOLAR_USER. Example: SCHOLAR_USER=m3rLfS4AAAAJ");
  process.exit(1);
}

const OUT = path.join(process.cwd(), "_data", "publications.yml");
const DEBUG_PNG = "scholar-debug.png";
const DEBUG_HTML = "scholar-page.html";
const DEBUG_LOG = fs.createWriteStream("scholar-console.log", { flags: "a" });

function normTitle(s) { return (s || "").trim().replace(/\s+/g, " ").toLowerCase(); }

function loadExisting() {
  try {
    const txt = fs.readFileSync(OUT, "utf8");
    const list = yaml.load(txt) || [];
    const map = new Map();
    list.forEach(p => map.set(normTitle(p.title), p));
    return { list, map };
  } catch {
    return { list: [], map: new Map() };
  }
}

function merge(existingMap, scraped) {
  return scraped
    .map(p => {
      const cur = existingMap.get(normTitle(p.title));
      return {
        ...p,
        image: cur?.image || "",
        "selected-publication":
          cur && (cur["selected-publication"] === "yes" || cur["selected-publication"] === true)
            ? "yes" : "no"
      };
    })
    .sort((a, b) => (b.year || 0) - (a.year || 0));
}

async function maybeAcceptCookies(page) {
  // Try common consent buttons quickly; ignore errors
  const selectors = [
    'button:has-text("I agree")',
    'button:has-text("Accept all")',
    'button:has-text("J\'accepte")',
    'button:has-text("Accepter")',
    'button:has-text("OK")'
  ];
  for (const sel of selectors) {
    try {
      const el = await page.$(sel);
      if (el) { await el.click(); await page.waitForTimeout(500); return; }
    } catch {}
  }
}

async function clickShowMore(page, maxClicks = 80) {
  for (let i = 0; i < maxClicks; i++) {
    const more = await page.$('#gsc_bpf_more:not([disabled])');
    if (!more) break;
    await more.click();
    await page.waitForTimeout(700);
  }
}

async function scrapeRows(page) {
  const rows = await page.$$('.gsc_a_tr');
  const out = [];
  for (const row of rows) {
    const a = await row.$('.gsc_a_at');
    const title = a ? (await a.textContent())?.trim() : "";
    const url = a ? await a.getAttribute('href') : null;
    const href = url && !url.startsWith('http')
      ? `https://scholar.google.com${url}` : (url || "");

    const meta = await row.$$eval(".gsc_a_t .gs_gray", els => els.map(e => e.textContent.trim()));
    const authors = meta[0] || "";
    const venue = meta[1] || "";
    const y = await row.$(".gsc_a_y span");
    const yearStr = y ? (await y.textContent())?.trim() : "";
    const year = yearStr ? parseInt(yearStr, 10) : undefined;

    out.push({ title, authors, venue, year, url: href });
  }
  return out;
}

(async () => {
  const url = `https://scholar.google.com/citations?user=${encodeURIComponent(USER)}&hl=en&view_op=list_works&sortby=pubdate`;

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    userAgent:
      "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
    viewport: { width: 1280, height: 1600 }
  });

  const page = await context.newPage();
  page.on("console", msg => DEBUG_LOG.write(`[${msg.type()}] ${msg.text()}\n`));

  try {
    await page.goto(url, { waitUntil: "networkidle" });
    await maybeAcceptCookies(page);
    await page.waitForSelector("#gsc_bdy", { timeout: 60000 });

    await clickShowMore(page);
    const scraped = await scrapeRows(page);

    if (!scraped.length) {
      await page.screenshot({ path: DEBUG_PNG, fullPage: true });
      fs.writeFileSync(DEBUG_HTML, await page.content(), "utf8");
      throw new Error("No rows scraped; saved screenshot and HTML for diagnostics.");
    }

    const existing = loadExisting();
    const merged = merge(existing.map, scraped);

    fs.mkdirSync(path.dirname(OUT), { recursive: true });
    fs.writeFileSync(OUT, yaml.dump(merged, { lineWidth: 1000, sortKeys: false }), "utf8");

    console.log(`Wrote ${merged.length} items → ${OUT}`);
    await browser.close();
  } catch (err) {
    console.error(err?.stack || err);
    try {
      await page.screenshot({ path: DEBUG_PNG, fullPage: true });
      fs.writeFileSync(DEBUG_HTML, await page.content(), "utf8");
    } catch {}
    await browser.close();
    process.exit(1);
  }
})();
