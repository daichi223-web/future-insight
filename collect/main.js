'use strict';

const fs = require('fs');
const path = require('path');
const { DATA_OUTPUT_PATH, RSS_INTERVAL_MS } = require('./config');
const normalize = require('./processors/normalize');
const deduplicate = require('./processors/deduplicate');
const classifyPestle = require('./processors/pestle');
const calculateScore = require('./processors/scorer');
const sleep = require('./utils/sleep');

// Source modules
const googleNews = require('./sources/google-news');
const yahooNews = require('./sources/yahoo-news');
const nhk = require('./sources/nhk');
const hatena = require('./sources/hatena');
const hackernews = require('./sources/hackernews');
const arxiv = require('./sources/arxiv');

const rssSources = [googleNews, yahooNews, nhk, hatena];

/**
 * Assign sequential IDs based on date.
 */
function assignIds(articles) {
  const today = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  return articles.map((a, i) => ({
    ...a,
    id: `art-${today}-${String(i + 1).padStart(3, '0')}`,
  }));
}

/**
 * Remove internal metadata fields before writing output.
 */
function cleanForOutput(article) {
  const { _hnScore, _hatenaBookmarks, ...clean } = article;
  return clean;
}

async function main() {
  console.log('=== Future Insight Collector ===');
  console.log(`Started at ${new Date().toISOString()}`);
  const rawArticles = [];

  // 1. Fetch RSS sources (with polite interval)
  for (const source of rssSources) {
    try {
      console.log(`[${source.name}] Fetching...`);
      const articles = await source.fetch();
      console.log(`[${source.name}] Got ${articles.length} articles`);
      rawArticles.push(...articles);
      await sleep(RSS_INTERVAL_MS);
    } catch (err) {
      console.error(`[${source.name}] FAILED: ${err.message}`);
    }
  }

  // 2. Fetch Hacker News (JSON API, parallel)
  try {
    console.log(`[${hackernews.name}] Fetching...`);
    const hnArticles = await hackernews.fetch();
    console.log(`[${hackernews.name}] Got ${hnArticles.length} articles`);
    rawArticles.push(...hnArticles);
  } catch (err) {
    console.error(`[${hackernews.name}] FAILED: ${err.message}`);
  }

  // 3. Fetch arXiv (with mandatory delay)
  try {
    console.log(`[${arxiv.name}] Fetching (with ${3}s delay)...`);
    const arxivArticles = await arxiv.fetch();
    console.log(`[${arxiv.name}] Got ${arxivArticles.length} articles`);
    rawArticles.push(...arxivArticles);
  } catch (err) {
    console.error(`[${arxiv.name}] FAILED: ${err.message}`);
  }

  console.log(`\nTotal raw articles: ${rawArticles.length}`);

  // 4. Pipeline: normalize → deduplicate → classify → score
  const normalized = rawArticles.map(normalize);
  console.log(`After normalize: ${normalized.length}`);

  const unique = deduplicate(normalized);
  console.log(`After deduplicate: ${unique.length}`);

  const classified = unique.map(classifyPestle);
  const scored = classified.map(calculateScore);

  // 5. Sort by date descending
  scored.sort((a, b) => new Date(b.publishedAt) - new Date(a.publishedAt));

  // 6. Assign IDs and clean
  const withIds = assignIds(scored);
  const output = {
    lastUpdated: new Date().toISOString(),
    articles: withIds.map(cleanForOutput),
  };

  // 7. Ensure output directory exists
  const outDir = path.dirname(DATA_OUTPUT_PATH);
  if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir, { recursive: true });
  }

  // 8. Write output
  fs.writeFileSync(DATA_OUTPUT_PATH, JSON.stringify(output, null, 2), 'utf-8');
  console.log(`\nWrote ${withIds.length} articles to ${DATA_OUTPUT_PATH}`);
  console.log(`Finished at ${new Date().toISOString()}`);
}

main().catch((err) => {
  console.error('Fatal error:', err);
  process.exit(1);
});
