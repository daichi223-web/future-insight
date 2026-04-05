'use strict';

const fs = require('fs');
const path = require('path');
const { DATA_OUTPUT_PATH, BLOG_OUTPUT_PATH, RSS_INTERVAL_MS } = require('./config');
const normalize = require('./processors/normalize');
const deduplicate = require('./processors/deduplicate');
const addJapaneseSummary = require('./processors/summarize-ja');
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
const zenn = require('./sources/zenn');
const qiita = require('./sources/qiita');
const githubTrending = require('./sources/github-trending');

const rssSources = [googleNews, yahooNews, nhk, hatena];
const blogSources = [zenn, qiita, githubTrending];

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
  const { _hnScore, _hatenaBookmarks, _engagement, ...clean } = article;
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

  // 5. Drop articles with no PESTLE match (everyday news: sports, entertainment, etc.)
  const relevant = classified.filter((a) => a.pestle && a.pestle.length > 0);
  console.log(`After relevance filter: ${relevant.length} (dropped ${classified.length - relevant.length} unclassified)`);

  const scored = relevant.map(calculateScore);

  // 6. Sort by date descending
  scored.sort((a, b) => new Date(b.publishedAt) - new Date(a.publishedAt));

  // 7. Assign IDs, add Japanese summaries, then clean
  const withIds = assignIds(scored);
  const withJa = await addJapaneseSummary(withIds);
  const output = {
    lastUpdated: new Date().toISOString(),
    articles: withJa.map(cleanForOutput),
  };

  // 7. Ensure output directory exists
  const outDir = path.dirname(DATA_OUTPUT_PATH);
  if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir, { recursive: true });
  }

  // 8. Write output
  fs.writeFileSync(DATA_OUTPUT_PATH, JSON.stringify(output, null, 2), 'utf-8');
  console.log(`\nWrote ${withIds.length} articles to ${DATA_OUTPUT_PATH}`);

  // ============================
  // Blog / SNS collection
  // ============================
  console.log('\n=== Blog / SNS Collection ===');
  const rawBlogs = [];

  for (const source of blogSources) {
    try {
      console.log(`[${source.name}] Fetching...`);
      const articles = await source.fetch();
      console.log(`[${source.name}] Got ${articles.length} articles`);
      rawBlogs.push(...articles);
      await sleep(RSS_INTERVAL_MS);
    } catch (err) {
      console.error(`[${source.name}] FAILED: ${err.message}`);
    }
  }

  console.log(`Total raw blog articles: ${rawBlogs.length}`);

  const normBlogs = rawBlogs.map(normalize);
  const uniqueBlogs = deduplicate(normBlogs);
  const classifiedBlogs = uniqueBlogs.map(classifyPestle);
  const relevantBlogs = classifiedBlogs.filter((a) => a.pestle && a.pestle.length > 0);
  console.log(`After relevance filter: ${relevantBlogs.length} (dropped ${classifiedBlogs.length - relevantBlogs.length} unclassified)`);
  const scoredBlogs = relevantBlogs.map(calculateScore);
  scoredBlogs.sort((a, b) => new Date(b.publishedAt) - new Date(a.publishedAt));

  const today = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  const blogWithIds = scoredBlogs.map((a, i) => ({
    ...a,
    id: `blog-${today}-${String(i + 1).padStart(3, '0')}`,
  }));

  const blogWithJa = await addJapaneseSummary(blogWithIds);

  const blogOutput = {
    lastUpdated: new Date().toISOString(),
    articles: blogWithJa.map(cleanForOutput),
  };

  const blogDir = path.dirname(BLOG_OUTPUT_PATH);
  if (!fs.existsSync(blogDir)) {
    fs.mkdirSync(blogDir, { recursive: true });
  }
  fs.writeFileSync(BLOG_OUTPUT_PATH, JSON.stringify(blogOutput, null, 2), 'utf-8');
  console.log(`Wrote ${blogWithIds.length} blog articles to ${BLOG_OUTPUT_PATH}`);
  console.log(`Finished at ${new Date().toISOString()}`);
}

main().catch((err) => {
  console.error('Fatal error:', err);
  process.exit(1);
});
