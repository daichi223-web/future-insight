'use strict';

const fetchRSS = require('../utils/fetch-rss');
const sleep = require('../utils/sleep');
const { ARXIV, ARXIV_DELAY_MS, FETCH_TIMEOUT_MS } = require('../config');

const SOURCE_NAME = 'arXiv';

async function fetchAll() {
  const url = `${ARXIV.endpoint}?search_query=${ARXIV.categories}&start=0&max_results=${ARXIV.maxResults}&sortBy=submittedDate&sortOrder=descending`;

  // Mandatory 3-second delay before arXiv API call
  await sleep(ARXIV_DELAY_MS);

  const res = await fetch(url, {
    signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
    headers: { 'User-Agent': 'FutureInsightBot/1.0' },
  });
  if (!res.ok) {
    if (res.status === 503) {
      console.log('[arXiv] Rate limited, retrying after 5s...');
      await sleep(5000);
      const retry = await fetch(url, {
        signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
        headers: { 'User-Agent': 'FutureInsightBot/1.0' },
      });
      if (!retry.ok) throw new Error(`arXiv retry failed: HTTP ${retry.status}`);
      return parseAtom(await retry.text());
    }
    throw new Error(`arXiv HTTP ${res.status}`);
  }

  return parseAtom(await res.text());
}

function parseAtom(xml) {
  const { XMLParser } = require('fast-xml-parser');
  const parser = new XMLParser({ ignoreAttributes: false, attributeNamePrefix: '@_', parseTagValue: false, parseAttributeValue: false });
  const parsed = parser.parse(xml);
  const entries = parsed.feed && parsed.feed.entry
    ? (Array.isArray(parsed.feed.entry) ? parsed.feed.entry : [parsed.feed.entry])
    : [];

  return entries.map((entry) => {
    const id = typeof entry.id === 'string' ? entry.id : '';
    const arxivId = id.replace('http://arxiv.org/abs/', '').replace(/v\d+$/, '');
    const categories = [];
    if (entry.category) {
      const cats = Array.isArray(entry.category) ? entry.category : [entry.category];
      for (const c of cats) {
        if (c['@_term']) categories.push(c['@_term']);
      }
    }
    return {
      title: typeof entry.title === 'string' ? entry.title.replace(/\s+/g, ' ').trim() : '',
      url: id,
      publishedAt: entry.published ? new Date(entry.published).toISOString() : new Date().toISOString(),
      summary: typeof entry.summary === 'string' ? entry.summary.replace(/\s+/g, ' ').trim() : '',
      source: SOURCE_NAME,
      type: 'paper',
      arxivId,
      arxivCategories: categories,
    };
  });
}

module.exports = { name: SOURCE_NAME, fetch: fetchAll };
