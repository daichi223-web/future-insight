'use strict';

/**
 * Keywords that require word-boundary matching (short terms prone to false positives).
 * These are matched with regex \bKEYWORD\b or surrounded by non-alphanumeric chars.
 */
const EXACT_MATCH_KEYWORDS = new Set([
  'ai', 'ev', 'nlp', 'dei', 'ipo', 'gdp', 'g7', 'g20', 'iot',
  'law', 'green', 'stock', 'court', 'trade',
]);

const PESTLE_KEYWORDS = {
  Political: [
    '政治', '政府', '選挙', '外交', '国会', '法案', '首相', '大統領',
    'G7', 'G20', '国連', 'NATO', '制裁', '安全保障', '防衛',
    'political', 'government', 'election', 'policy', 'diplomacy',
    'congress', 'parliament', 'president', 'sanctions',
  ],
  Economic: [
    '経済', 'GDP', '市場', '株価', '金融', '投資', 'スタートアップ', '半導体',
    'インフレ', 'デフレ', '為替', '円安', '円高', '利上げ', '利下げ',
    'サプライチェーン', '貿易', '関税', 'IPO',
    'economic', 'market', 'finance', 'trade', 'investment', 'inflation',
    'semiconductor', 'supply chain', 'GDP', 'stock',
  ],
  Social: [
    '社会', '教育', '医療', '高齢化', '少子化', '格差', '働き方',
    '介護', '人口', '移民', '難民', 'ジェンダー', '多様性', 'DEI',
    'social', 'education', 'health', 'community', 'inequality',
    'population', 'diversity', 'immigration',
  ],
  Technological: [
    '量子', 'ロボット', 'デジタル', 'サイバー', 'ブロックチェーン',
    'メタバース', '5G', '6G', '宇宙', '自動運転', 'IoT',
    'technology', 'quantum', 'robotics', 'autonomous',
  ],
  Legal: [
    '法律', '法改正', '規制', '裁判', '判決', '著作権', 'プライバシー',
    'GDPR', 'コンプライアンス', '独禁法', '特許', '知的財産',
    'legal', 'law', 'regulation', 'compliance', 'patent',
    'copyright', 'privacy', 'antitrust',
  ],
  Environmental: [
    '環境', '気候', 'CO2', 'カーボン', '再生可能エネルギー', '海洋',
    '森林', '生物多様性', '脱炭素', '太陽光', '風力',
    'サステナビリティ', 'SDGs', 'ESG', 'グリーン',
    'climate', 'environment', 'carbon', 'sustainability', 'renewable',
    'biodiversity', 'emission', 'green',
    '電気自動車',
  ],
  AI: [
    'AI', '人工知能', '機械学習', 'LLM', 'GPT', '生成AI', 'AGI',
    '大規模言語モデル', '基盤モデル', 'ファインチューニング',
    'ChatGPT', 'Claude', 'Gemini', 'Copilot', 'マルチモーダル',
    'AIエージェント', 'AI安全性', 'ディープフェイク', '自然言語処理',
    'トランスフォーマー', '拡散モデル',
    'artificial intelligence', 'machine learning', 'deep learning', 'neural network',
    'large language model', 'foundation model', 'generative AI',
    'diffusion model', 'multimodal', 'AI agent', 'AI safety', 'NLP',
    'computer vision', 'reinforcement learning', 'openai', 'anthropic',
  ],
};

/**
 * Remove URLs from text to prevent false keyword matches in URLs.
 */
function stripUrls(text) {
  return text.replace(/https?:\/\/[^\s)]+/g, ' ');
}

/**
 * Check if a keyword matches in text, using word-boundary matching for short keywords.
 */
function keywordMatches(text, keyword) {
  const kw = keyword.toLowerCase();
  if (EXACT_MATCH_KEYWORDS.has(kw)) {
    // Word-boundary match: for ASCII keywords use \b, for Japanese check surrounding chars
    const re = new RegExp(`(?:^|[\\s　、。,.:;!?\"'()\\[\\]{}/<>＜＞「」『』（）])${escapeRegExp(kw)}(?:$|[\\s　、。,.:;!?\"'()\\[\\]{}/<>＜＞「」『』（）])`, 'i');
    return re.test(text);
  }
  return text.includes(kw);
}

function escapeRegExp(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Classify an article into 1-3 PESTLE categories based on keyword matching.
 */
function classifyPestle(article) {
  // Use title + summary, strip URLs to avoid false matches
  const raw = `${article.title} ${article.summary}`;
  const text = stripUrls(raw).toLowerCase();
  const scores = {};

  for (const [category, keywords] of Object.entries(PESTLE_KEYWORDS)) {
    let count = 0;
    for (const kw of keywords) {
      if (keywordMatches(text, kw)) count++;
    }
    if (count > 0) scores[category] = count;
  }

  // Sort by match count descending, take top 1-3
  const sorted = Object.entries(scores).sort((a, b) => b[1] - a[1]);
  const pestle = sorted.slice(0, 3).map(([cat]) => cat);

  // No default — unmatched articles get empty pestle (shown as "未分類" in UI)
  return { ...article, pestle };
}

module.exports = classifyPestle;
