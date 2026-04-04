'use strict';

const fetchRSS = require('../utils/fetch-rss');
const { RSS_FEEDS } = require('../config');

const SOURCE_NAME = 'はてなブックマーク';

async function fetch() {
  const articles = [];
  for (const url of RSS_FEEDS[SOURCE_NAME]) {
    const items = await fetchRSS(url);
    for (const item of items) {
      // Hatena RSS 1.0 uses dc:date instead of pubDate
      const dateStr = item.pubDate || item['dc:date'] || '';
      const bookmarkCount = parseInt(item['hatena:bookmarkcount'] || '0', 10);
      articles.push({
        title: item.title || '',
        url: item.link || item['@_rdf:about'] || '',
        publishedAt: dateStr ? new Date(dateStr).toISOString() : new Date().toISOString(),
        summary: item.description || '',
        source: SOURCE_NAME,
        type: 'news',
        _hatenaBookmarks: bookmarkCount,
      });
    }
  }
  return articles;
}

module.exports = { name: SOURCE_NAME, fetch };
