'use strict';

const { XMLParser } = require('fast-xml-parser');
const { FETCH_TIMEOUT_MS } = require('../config');

const parser = new XMLParser({
  ignoreAttributes: false,
  attributeNamePrefix: '@_',
  parseTagValue: false,
  parseAttributeValue: false,
  processEntities: false,
});

/**
 * Fetch and parse an RSS/Atom feed.
 * Returns an array of raw item objects.
 */
async function fetchRSS(url) {
  const res = await fetch(url, {
    signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
    headers: { 'User-Agent': 'FutureInsightBot/1.0' },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  const xml = await res.text();
  const parsed = parser.parse(xml);

  // RSS 2.0
  if (parsed.rss && parsed.rss.channel) {
    const channel = parsed.rss.channel;
    const items = Array.isArray(channel.item) ? channel.item : channel.item ? [channel.item] : [];
    return items;
  }

  // RSS 1.0 (RDF) — used by Hatena
  if (parsed['rdf:RDF']) {
    const items = parsed['rdf:RDF'].item;
    return Array.isArray(items) ? items : items ? [items] : [];
  }

  // Atom — used by arXiv
  if (parsed.feed && parsed.feed.entry) {
    const entries = parsed.feed.entry;
    return Array.isArray(entries) ? entries : entries ? [entries] : [];
  }

  return [];
}

module.exports = fetchRSS;
