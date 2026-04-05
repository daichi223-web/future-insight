'use strict';

const fetchRSS = require('../utils/fetch-rss');
const { ZENN } = require('../config');

const SOURCE_NAME = 'Zenn';

async function fetchAll() {
  const items = await fetchRSS(ZENN.feed);
  const articles = [];
  for (const item of items) {
    // Atom feed: entry has title, link, published, summary/content
    const link = item.link
      ? (typeof item.link === 'string' ? item.link : item.link['@_href'] || '')
      : '';
    const dateStr = item.published || item.updated || item.pubDate || '';
    articles.push({
      title: item.title || '',
      url: link,
      publishedAt: dateStr ? new Date(dateStr).toISOString() : new Date().toISOString(),
      summary: item.summary || item.description || '',
      source: SOURCE_NAME,
      type: 'blog',
    });
  }
  return articles;
}

module.exports = { name: SOURCE_NAME, fetch: fetchAll };
