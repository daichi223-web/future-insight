'use strict';

const { GITHUB_TRENDING, FETCH_TIMEOUT_MS } = require('../config');

const SOURCE_NAME = 'GitHub Trending';

async function fetchAll() {
  const since = new Date();
  since.setDate(since.getDate() - GITHUB_TRENDING.daysBack);
  const dateStr = since.toISOString().slice(0, 10);

  const url = `${GITHUB_TRENDING.endpoint}?q=created:>${dateStr}&sort=stars&order=desc&per_page=${GITHUB_TRENDING.maxItems}`;
  const res = await fetch(url, {
    signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
    headers: {
      'User-Agent': 'FutureInsightBot/1.0',
      Accept: 'application/vnd.github+json',
    },
  });
  if (!res.ok) throw new Error(`GitHub Search HTTP ${res.status}`);
  const data = await res.json();

  return (data.items || []).map((repo) => ({
    title: `${repo.full_name}: ${repo.description || ''}`.slice(0, 200),
    url: repo.html_url || '',
    publishedAt: repo.created_at || new Date().toISOString(),
    summary: `${repo.description || ''} — ⭐ ${repo.stargazers_count} | ${repo.language || 'N/A'}`,
    source: SOURCE_NAME,
    type: 'blog',
    _engagement: repo.stargazers_count || 0,
  }));
}

module.exports = { name: SOURCE_NAME, fetch: fetchAll };
