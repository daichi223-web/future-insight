'use strict';

/**
 * summarize-ja.js
 *
 * 英語記事（Hacker News / arXiv / GitHub Trending）に
 * Claude Haiku で日本語サマリー（summaryJa）を付与する。
 *
 * - 日本語ソース（lang: 'ja'）はスキップ
 * - ANTHROPIC_API_KEY 未設定時はサイレントスキップ
 * - バッチサイズ 10 件ずつ処理してコスト削減
 */

const BATCH_SIZE = 10;
const API_URL = 'https://api.anthropic.com/v1/messages';
const MODEL = 'claude-haiku-4-5-20251001';

/**
 * 1バッチ分の記事をまとめて翻訳リクエストする。
 * レスポンスは JSON 配列 [{id, summaryJa}] 形式。
 */
async function fetchBatch(articles, apiKey) {
  const items = articles.map((a) => ({
    id: a.id,
    title: a.title,
    summary: a.summary || '',
  }));

  const prompt = `以下の英語記事リストについて、それぞれ3〜4文の自然な日本語サマリーを生成してください。
技術的な用語はそのまま使用し、重要な数値・固有名詞は省略しないでください。

入力 (JSON配列):
${JSON.stringify(items, null, 2)}

出力は以下の形式のJSONのみを返してください（説明文・マークダウン不要）:
[{"id":"...","summaryJa":"..."}]`;

  const res = await fetch(API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
    },
    body: JSON.stringify({
      model: MODEL,
      max_tokens: 2048,
      messages: [{ role: 'user', content: prompt }],
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text.slice(0, 200)}`);
  }

  const data = await res.json();
  const raw = data.content?.[0]?.text || '[]';

  // JSON部分だけ抽出（```json ... ``` で囲まれている場合も対応）
  const jsonStr = raw.replace(/```json\s*/g, '').replace(/```\s*/g, '').trim();
  return JSON.parse(jsonStr);
}

/**
 * 記事配列に summaryJa を付与して返す。
 * 英語記事のみ対象。失敗したバッチはスキップして続行。
 */
async function addJapaneseSummary(articles) {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    console.log('[summarize-ja] ANTHROPIC_API_KEY not set — skipping');
    return articles;
  }

  // 英語記事のみ対象
  const targets = articles.filter((a) => a.lang === 'en' && a.id);
  if (targets.length === 0) {
    console.log('[summarize-ja] No English articles to summarize');
    return articles;
  }

  console.log(`[summarize-ja] Summarizing ${targets.length} English articles in batches of ${BATCH_SIZE}...`);

  // id -> summaryJa のマップを構築
  const summaryMap = {};

  for (let i = 0; i < targets.length; i += BATCH_SIZE) {
    const batch = targets.slice(i, i + BATCH_SIZE);
    const batchNum = Math.floor(i / BATCH_SIZE) + 1;
    const totalBatches = Math.ceil(targets.length / BATCH_SIZE);
    try {
      const results = await fetchBatch(batch, apiKey);
      for (const r of results) {
        if (r.id && r.summaryJa) summaryMap[r.id] = r.summaryJa;
      }
      console.log(`[summarize-ja] Batch ${batchNum}/${totalBatches} done (${results.length} summaries)`);
    } catch (err) {
      console.error(`[summarize-ja] Batch ${batchNum}/${totalBatches} FAILED: ${err.message} — skipping`);
    }
  }

  // 元の配列に summaryJa をマージして返す
  return articles.map((a) =>
    summaryMap[a.id] ? { ...a, summaryJa: summaryMap[a.id] } : a
  );
}

module.exports = addJapaneseSummary;
