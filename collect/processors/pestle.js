'use strict';

const PESTLE_KEYWORDS = {
  Political: [
    '政治', '政府', '選挙', '外交', '国会', '法案', '首相', '大統領',
    'G7', 'G20', '国連', 'NATO', '制裁', '安全保障', '防衛',
    'political', 'government', 'election', 'policy', 'diplomacy',
    'congress', 'parliament', 'president', 'sanctions',
  ],
  Economic: [
    '経済', 'GDP', '市場', '株', '金融', '投資', 'スタートアップ', '半導体',
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
    'AI', '人工知能', '量子', 'ロボット', 'デジタル', 'サイバー',
    'ブロックチェーン', '機械学習', 'LLM', 'GPT', '生成AI',
    'メタバース', '5G', '6G', '宇宙', 'EV', '自動運転',
    'technology', 'artificial intelligence', 'quantum', 'machine learning',
    'deep learning', 'neural', 'robotics', 'autonomous',
  ],
  Legal: [
    '法律', '法改正', '規制', '裁判', '判決', '著作権', 'プライバシー',
    'GDPR', 'コンプライアンス', '独禁法', '特許', '知的財産',
    'legal', 'law', 'court', 'regulation', 'compliance', 'patent',
    'copyright', 'privacy', 'antitrust',
  ],
  Environmental: [
    '環境', '気候', 'CO2', 'カーボン', '再生可能エネルギー', '海洋',
    '森林', '生物多様性', '脱炭素', 'EV', '太陽光', '風力',
    'サステナビリティ', 'SDGs', 'ESG', 'グリーン',
    'climate', 'environment', 'carbon', 'sustainability', 'renewable',
    'biodiversity', 'emission', 'green',
  ],
};

/**
 * Classify an article into 1-3 PESTLE categories based on keyword matching.
 */
function classifyPestle(article) {
  const text = `${article.title} ${article.summary}`.toLowerCase();
  const scores = {};

  for (const [category, keywords] of Object.entries(PESTLE_KEYWORDS)) {
    let count = 0;
    for (const kw of keywords) {
      if (text.includes(kw.toLowerCase())) count++;
    }
    if (count > 0) scores[category] = count;
  }

  // Sort by match count descending, take top 1-3
  const sorted = Object.entries(scores).sort((a, b) => b[1] - a[1]);
  const pestle = sorted.slice(0, 3).map(([cat]) => cat);

  // Default to Technological if no match
  if (pestle.length === 0) pestle.push('Technological');

  return { ...article, pestle };
}

module.exports = classifyPestle;
