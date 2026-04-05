'use strict';

/**
 * Keywords indicating high societal impact — systemic change, policy shifts,
 * emerging risks, or breakthrough developments.
 */
const IMPACT_KEYWORDS = [
  // AI / Technology disruption
  'AI', 'AGI', 'LLM', 'GPT', '大規模言語モデル', 'AIエージェント',
  '生成AI', 'generative', '自動運転', 'autonomous',
  '量子', 'quantum', 'CRISPR', '核融合', 'fusion',
  // Policy & Regulation
  '規制', 'regulation', '法改正', '新法', '条約', '制裁',
  '国際協定', 'サミット', '閣議決定',
  // Systemic risk & societal shifts
  '気候変動', 'climate', '脱炭素', 'decarbonization',
  'パンデミック', 'pandemic', '安全保障', 'security',
  '人口減少', '少子化', '移民政策',
  // Breakthrough / disruption signals
  '画期的', 'breakthrough', '革新', '世界初', '史上初',
  '転換点', 'tipping point', 'paradigm',
  // Economic structural change
  '利上げ', '利下げ', '金融危機', 'インフレ', 'recession',
  'サプライチェーン', '半導体', 'semiconductor',
];

/**
 * Calculate a signal score (1-10) for an article.
 * Weights societal impact: cross-cutting PESTLE, impact keywords, social engagement.
 */
function calculateScore(article) {
  let score = 3; // lower baseline — earn points through relevance

  // --- Source authority ---
  if (['arXiv', 'NHK'].includes(article.source)) score += 1;

  // --- PESTLE breadth: cross-cutting articles have broader societal impact ---
  const pestleCount = (article.pestle || []).length;
  if (pestleCount >= 3) score += 2;
  else if (pestleCount >= 2) score += 1;

  // --- Impact keyword intensity ---
  const text = `${article.title} ${article.summary}`.toLowerCase();
  let impactHits = 0;
  for (const kw of IMPACT_KEYWORDS) {
    if (text.includes(kw.toLowerCase())) impactHits++;
  }
  score += Math.min(impactHits, 4); // up to +4

  // --- Social engagement (proof of public interest) ---
  if (article._hnScore > 200) score += 2;
  else if (article._hnScore > 100) score += 1;

  if (article._hatenaBookmarks > 100) score += 2;
  else if (article._hatenaBookmarks > 50) score += 1;

  if (article._engagement > 100) score += 2;
  else if (article._engagement > 30) score += 1;

  // --- Paper type boost (academic rigour) ---
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
