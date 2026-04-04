'use strict';

/**
 * Simple character-level overlap ratio between two strings.
 * Returns a number between 0 and 1.
 */
function titleSimilarity(a, b) {
  if (!a || !b) return 0;
  const setA = new Set(a.toLowerCase());
  const setB = new Set(b.toLowerCase());
  let intersection = 0;
  for (const ch of setA) {
    if (setB.has(ch)) intersection++;
  }
  const union = new Set([...setA, ...setB]).size;
  return union === 0 ? 0 : intersection / union;
}

/** Source authority ranking (higher = more authoritative) */
const AUTHORITY = {
  arXiv: 5,
  NHK: 4,
  'Yahoo!ニュース': 3,
  'Google News': 2,
  'はてなブックマーク': 2,
  'Hacker News': 1,
};

/**
 * Remove duplicate articles.
 * Primary: exact URL match. Secondary: title similarity > 0.8.
 */
function deduplicate(articles) {
  const seen = new Map(); // url -> article
  const result = [];

  for (const article of articles) {
    if (!article.url) continue;

    // Exact URL match
    if (seen.has(article.url)) {
      const existing = seen.get(article.url);
      const existAuth = AUTHORITY[existing.source] || 0;
      const newAuth = AUTHORITY[article.source] || 0;
      if (newAuth > existAuth) {
        seen.set(article.url, article);
      }
      continue;
    }

    // Title similarity check
    let isDup = false;
    for (const [, existing] of seen) {
      if (titleSimilarity(article.title, existing.title) > 0.8) {
        isDup = true;
        break;
      }
    }

    if (!isDup) {
      seen.set(article.url, article);
      result.push(article);
    }
  }

  // Return with any authority-based replacements
  return [...seen.values()];
}

module.exports = deduplicate;
