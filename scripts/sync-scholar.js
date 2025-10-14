#!/usr/bin/env node
/**
 * Scrape Google Scholar → _data/publications.yml
 * No API keys. Headless Chrome with stealth and diagnostics.
 */
const fs = require("fs");
const path = require("path");
const yaml = require("js-yaml");
const puppeteer = require("puppeteer-extra");
const StealthPlugin = require("puppeteer-extra-plugin-stealth");
puppeteer.use(StealthPlugin());

const USER = process.env.SCHOLAR_USER || process.argv[2];
if (!USER) {
  console.error("Missing SCHOLAR_USER (env or arg). Example: SCHOLAR_USER=m3rLfS4AAAAJ");
  process.exit(1);
}
const OUT_FILE = path.join(process.cwd(), "_data", "publications.yml");
const DEBUG_SCREEN = path.join(process.cwd(), "scholar-debug.png");
const DEBUG_HTML = path.join(process.cwd(), "scholar-page.html");
const DEBUG_LOG = fs.createWriteStream(path.join(process.cwd(), "scholar-console.log"), { flags: "a" });

function normTitle(s) { return (s || "").trim().replace(/\s+/g, " ").toLowerCase(); }

async function loadExisting() {
  try {
    const t = fs.readFileSync(OUT_FILE, "utf8");
    const data = yaml.load(t) || [];
    const byTitle = new Map();
    data.forEach(p => byTitle.set(normTitle(p.title), p));
    return { list: data, map: byTitle };
  } catch { return { list: [], map: new Map() }; }
}

async function openScholar(browser, url) {
  const page = await browser.newPage();
  page.setDefaultNavigationTimeout(120000);
  page.on("console", msg => DEBUG_LOG.write(`[${msg.type()}] ${msg.text()}\n`));
  await page.setUserAgent("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36");
  await page.goto(url, { waitUntil: "networkidle2", timeout: 120000 });

  // Accept cookie banner if present
  try {
    const btn = await page.$x("//button[contains(., 'Accept') or contains(., 'I agree') or contains(., 'Je comprends')]");
    if (btn && btn.length) { await btn[0].click(); await page.waitForTimeout(800); }
  } catch {}

  // Scholar body present?
  await page.waitForSelector("#gsc_bdy", { timeout: 60000 });
  return page;
}

async function scrapeList(page) {
  // Click “More” several times (if available)
  for (let i = 0; i < 60; i++) {
    const more = await page.$("#gsc_bpf_more:not([disabled])");
    if (!more) break;
    await more.click();
    await page.waitForTimeout(700);
  }

  const rows = await page.$$(".gsc_a_tr");
  const out = [];
  for (const row of rows) {
    const titleEl = await row.$(".gsc_a_at");
    const title = titleEl ? (await page.evaluate(el => el.textContent, titleEl)).trim() : "";
    const href = titleEl ? await page.evaluate(el => el.href, titleEl) : "";

    const meta = await row.$$eval(".gsc_a_t .gs_gray", els => els.map(e => e.textContent.trim()));
    const authors = meta[0] || "";
    const venue = meta[1] || "";
    const yearTxt = await row.$eval(".gsc_a_y span", el => el.textContent.trim()).catch(() => "");
    const year = yearTxt ? parseInt(yearTxt, 10) : undefined;

    out.push({ title, authors, venue, year, url: href });
  }
  return out;
}

function merge(existingMap, scraped) {
  return scraped
    .map(p => {
      const current = existingMap.get(normTitle(p.title));
      return {
        ...p,
        image: current?.image || "",
        "selected-publication":
          current && (current["selected-publication"] === "yes" || current["selected-publication"] === true)
            ? "yes" : "no"
      };
    })
    .sort((a, b) => (b.year || 0) - (a.year || 0));
}

async function run() {
  const url = `https://scholar.google.com/citations?user=${encodeURIComponent(USER)}&hl=en&view_op=list_works&sortby=pubdate`;

  const browser = await puppeteer.launch({
    headless: "new",
    executablePath: require("puppeteer").executablePath(),
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-dev-shm-usage",
      "--disable-gpu",
      "--single-process",
      "--no-zygote"
    ]
  });

  try {
    const page = await openScholar(browser, url);
    const scraped = await scrapeList(page);

    if (!scraped.length) {
      // capture diagnostics
      await page.screenshot({ path: DEBUG_SCREEN, fullPage: true });
      const html = await page.content();
      fs.writeFileSync(DEBUG_HTML, html, "utf8");
      throw new Error("No publications scraped; saved screenshot and HTML for debugging.");
    }

    const existing = await loadExisting();
    const merged = merge(existing.map, scraped);

    fs.mkdirSync(path.dirname(OUT_FILE), { recursive: true });
    const out = yaml.dump(merged, { lineWidth: 1000, sortKeys: false });
    fs.writeFileSync(OUT_FILE, out, "utf8");
    console.log(`Wrote ${merged.length} records → ${OUT_FILE}`);
  } finally {
    await browser.close();
  }
}

run().catch(err => {
  console.error(err?.stack || err);
  process.exit(1);
});
