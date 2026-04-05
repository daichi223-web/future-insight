'use strict';

/**
 * Strip HTML tags from a string.
 */
function stripHtml(str) {
  if (!str) return '';
  return str.replace(/<[^>]*>/g, '').trim();
}

/**
 * Decode common HTML/XML numeric character references and named entities.
 */
function decodeEntities(str) {
  if (!str) return '';
  return str
    .replace(/&#x([0-9a-fA-F]+);/g, (_, hex) => String.fromCodePoint(parseInt(hex, 16)))
    .replace(/&#(\d+);/g, (_, dec) => String.fromCodePoint(parseInt(dec, 10)))
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'");
}

/**
 * Detect language: 'ja' if text contains significant Japanese characters, else 'en'.
 */
function detectLang(text) {
  const ja = (text.match(/[\u3000-\u9FFF\uF900-\uFAFF]/g) || []).length;
  return ja >= 3 ? 'ja' : 'en';
}

/**
 * Normalize a raw article into the unified schema.
 * Does NOT assign id, pestle, signalScore, or signalLevel — those come later.
 */
function normalize(raw) {
  const title = decodeEntities(stripHtml(raw.title || '')).slice(0, 500);
  return {
    title,
    source: raw.source || 'Unknown',
    url: (raw.url || '').trim(),
    publishedAt: raw.publishedAt || new Date().toISOString(),
    type: raw.type || 'news',
    lang: detectLang(title),
    summary: decodeEntities(stripHtml(raw.summary || '')).slice(0, 1000),
    // Paper-specific
    ...(raw.arxivId ? { arxivId: raw.arxivId } : {}),
    ...(raw.arxivCategories ? { arxivCategories: raw.arxivCategories } : {}),
    // Internal metadata (stripped before output)
    _hnScore: raw._hnScore || 0,
    _hatenaBookmarks: raw._hatenaBookmarks || 0,
    _engagement: raw._engagement || 0,
  };
}

module.exports = normalize;
