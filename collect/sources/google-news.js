'use strict';

const fetchRSS = require('../utils/fetch-rss');
const { RSS_FEEDS } = require('../config');

const SOURCE_NAME = 'Google News';

async function fetch() {
  const articles = [];
  for (const url of RSS_FEEDS[SOURCE_NAME]) {
    const items = await fetchRSS(url);
    for (const item of items) {
      articles.push({
        title: item.title || '',
        url: item.link || '',
        publishedAt: item.pubDate ? new Date(item.pubDate).toISOString() : new Date().toISOString(),
        summary: item.description || '',
        source: SOURCE_NAME,
        type: 'news',
      });
    }
  }
  return articles;
}

module.exports = { name: SOURCE_NAME, fetch };
