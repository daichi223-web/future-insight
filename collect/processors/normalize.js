'use strict';

/**
 * Strip HTML tags from a string.
 */
function stripHtml(str) {
  if (!str) return '';
  return str.replace(/<[^>]*>/g, '').trim();
}

/**
 * Normalize a raw article into the unified schema.
 * Does NOT assign id, pestle, signalScore, or signalLevel — those come later.
 */
function normalize(raw) {
  return {
    title: stripHtml(raw.title || '').slice(0, 500),
    source: raw.source || 'Unknown',
    url: (raw.url || '').trim(),
    publishedAt: raw.publishedAt || new Date().toISOString(),
    type: raw.type || 'news',
    summary: stripHtml(raw.summary || '').slice(0, 1000),
    // Paper-specific
    ...(raw.arxivId ? { arxivId: raw.arxivId } : {}),
    ...(raw.arxivCategories ? { arxivCategories: raw.arxivCategories } : {}),
    // Internal metadata (stripped before output)
    _hnScore: raw._hnScore || 0,
    _hatenaBookmarks: raw._hatenaBookmarks || 0,
  };
}

module.exports = normalize;
