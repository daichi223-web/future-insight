'use strict';

const FUTURE_KEYWORDS = [
  'AI', 'AGI', '量子', 'quantum', '気候変動', 'climate',
  '規制', 'regulation', '画期的', 'breakthrough', '革新',
  '自動運転', 'autonomous', '生成AI', 'generative',
  'バイオ', 'biotech', 'CRISPR', '核融合', 'fusion',
  'ロボット', 'robotics', '脱炭素', 'decarbonization',
];

/**
 * Calculate a signal score (1-10) for an article.
 */
function calculateScore(article) {
  let score = 5; // baseline

  // Source authority boost
  if (['arXiv', 'NHK'].includes(article.source)) score += 1;

  // Future-oriented keyword intensity
  const text = `${article.title} ${article.summary}`.toLowerCase();
  let keywordHits = 0;
  for (const kw of FUTURE_KEYWORDS) {
    if (text.includes(kw.toLowerCase())) keywordHits++;
  }
  score += Math.min(keywordHits, 3);

  // Hacker News vote boost
  if (article._hnScore > 200) score += 2;
  else if (article._hnScore > 100) score += 1;

  // Hatena bookmark boost
  if (article._hatenaBookmarks > 100) score += 2;
  else if (article._hatenaBookmarks > 50) score += 1;

  // Paper type slight boost (academic signal)
  if (article.type === 'paper') score += 1;

  // Clamp to 1-10
  score = Math.max(1, Math.min(10, score));

  // Derive signal level
  let signalLevel;
  if (score >= 7) signalLevel = 'HIGH';
  else if (score >= 4) signalLevel = 'Medium';
  else signalLevel = 'Low';

  return { ...article, signalScore: score, signalLevel };
}

module.exports = calculateScore;
