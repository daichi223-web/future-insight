'use strict';

const { HACKERNEWS, FETCH_TIMEOUT_MS } = require('../config');

const SOURCE_NAME = 'Hacker News';

async function fetchItem(id) {
  const res = await fetch(HACKERNEWS.item(id), {
    signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
  });
  if (!res.ok) return null;
  return res.json();
}

async function fetchAll() {
  const res = await fetch(HACKERNEWS.topStories, {
    signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
  });
  if (!res.ok) throw new Error(`HN topStories HTTP ${res.status}`);
  const ids = await res.json();
  const topIds = ids.slice(0, HACKERNEWS.maxItems);

  const items = await Promise.allSettled(topIds.map(fetchItem));
  const articles = [];
  for (const result of items) {
    if (result.status !== 'fulfilled' || !result.value) continue;
    const item = result.value;
    if (!item.url || item.type !== 'story') continue;
    articles.push({
      title: item.title || '',
      url: item.url,
      publishedAt: item.time ? new Date(item.time * 1000).toISOString() : new Date().toISOString(),
      summary: '',
      source: SOURCE_NAME,
      type: 'news',
      _hnScore: item.score || 0,
    });
  }
  return articles;
}

module.exports = { name: SOURCE_NAME, fetch: fetchAll };
