'use strict';

const { QIITA, FETCH_TIMEOUT_MS } = require('../config');

const SOURCE_NAME = 'Qiita';

async function fetchAll() {
  const url = `${QIITA.endpoint}?page=1&per_page=${QIITA.maxItems}&query=${encodeURIComponent(QIITA.query)}`;
  const res = await fetch(url, {
    signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
    headers: { 'User-Agent': 'FutureInsightBot/1.0' },
  });
  if (!res.ok) throw new Error(`Qiita HTTP ${res.status}`);
  const items = await res.json();

  return items.map((item) => ({
    title: item.title || '',
    url: item.url || '',
    publishedAt: item.created_at || new Date().toISOString(),
    summary: (item.body || '').slice(0, 300).replace(/[#*`\n]/g, ' ').trim(),
    source: SOURCE_NAME,
    type: 'blog',
    _engagement: item.likes_count || 0,
  }));
}

module.exports = { name: SOURCE_NAME, fetch: fetchAll };
