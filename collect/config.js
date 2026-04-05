'use strict';

const path = require('path');

/** Output path for latest.json */
const DATA_OUTPUT_PATH = path.resolve(__dirname, '..', 'docs', 'data', 'latest.json');

/** Output path for sns-blogs.json */
const BLOG_OUTPUT_PATH = path.resolve(__dirname, '..', 'docs', 'data', 'sns-blogs.json');

/** Fetch timeout in milliseconds */
const FETCH_TIMEOUT_MS = 15000;

/** Polite interval between RSS requests (ms) */
const RSS_INTERVAL_MS = 1500;

/** Mandatory arXiv API delay (ms) */
const ARXIV_DELAY_MS = 3000;

/** RSS feed URLs by source */
const RSS_FEEDS = {
  'Google News': [
    'https://news.google.com/rss?hl=ja&gl=JP&ceid=JP:ja',
  ],
  'Yahoo!ニュース': [
    'https://news.yahoo.co.jp/rss/topics/top-picks.xml',
    'https://news.yahoo.co.jp/rss/topics/it.xml',
    'https://news.yahoo.co.jp/rss/topics/science.xml',
  ],
  NHK: [
    'https://www3.nhk.or.jp/rss/news/cat0.xml',
    'https://www3.nhk.or.jp/rss/news/cat4.xml',
    'https://www3.nhk.or.jp/rss/news/cat5.xml',
    'https://www3.nhk.or.jp/rss/news/cat7.xml',
  ],
  'はてなブックマーク': [
    'https://b.hatena.ne.jp/hotentry/it.rss',
    'https://b.hatena.ne.jp/hotentry/economics.rss',
    'https://b.hatena.ne.jp/hotentry/knowledge.rss',
  ],
};

/** Hacker News API endpoints */
const HACKERNEWS = {
  topStories: 'https://hacker-news.firebaseio.com/v0/topstories.json',
  item: (id) => `https://hacker-news.firebaseio.com/v0/item/${id}.json`,
  maxItems: 30,
};

/** arXiv API */
const ARXIV = {
  endpoint: 'http://export.arxiv.org/api/query',
  categories: 'cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CY+OR+cat:cs.CR+OR+cat:quant-ph',
  maxResults: 20,
};

/** Zenn RSS */
const ZENN = {
  feed: 'https://zenn.dev/feed',
};

/** Qiita API */
const QIITA = {
  endpoint: 'https://qiita.com/api/v2/items',
  query: 'tag:AI OR tag:機械学習 OR tag:LLM OR tag:プログラミング OR tag:Python',
  maxItems: 20,
};

/** GitHub Trending (via Search API) */
const GITHUB_TRENDING = {
  endpoint: 'https://api.github.com/search/repositories',
  daysBack: 7,
  maxItems: 20,
};

module.exports = {
  DATA_OUTPUT_PATH,
  BLOG_OUTPUT_PATH,
  FETCH_TIMEOUT_MS,
  RSS_INTERVAL_MS,
  ARXIV_DELAY_MS,
  RSS_FEEDS,
  HACKERNEWS,
  ARXIV,
  ZENN,
  QIITA,
  GITHUB_TRENDING,
};
