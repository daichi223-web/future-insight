/* ============================================================
   未来洞察支援アプリ — Future Insight App
   Single-page vanilla JS application (no build step)
   ============================================================ */

(function () {
  'use strict';

  // ----------------------------------------------------------
  // Constants
  // ----------------------------------------------------------

  const DATA_PATHS = {
    latest: './data/latest.json',
    claIndex: './data/cla/index.json',
    claYear: (year) => `./data/cla/${year}.json`,
    scenarios: './data/scenarios/scenarios.json',
  };

  const PESTLE_EN_TO_JA = {
    Political: '政治',
    Economic: '経済',
    Social: '社会',
    Technological: '技術',
    Legal: '法律',
    Environmental: '環境',
  };

  const PESTLE_COLORS = {
    Political: '#e74c3c',
    Economic: '#f39c12',
    Social: '#2ecc71',
    Technological: '#3498db',
    Legal: '#9b59b6',
    Environmental: '#1abc9c',
  };

  const SIGNAL_LEVELS = {
    HIGH: { label: 'HIGH', color: '#e74c3c', min: 7 },
    Medium: { label: 'Medium', color: '#f39c12', min: 4 },
    Low: { label: 'Low', color: '#95a5a6', min: 0 },
  };

  const TABS = [
    { id: 'overview', label: '概要' },
    { id: 'pestle-news', label: 'PESTLEニュース' },
    { id: 'papers', label: '学術論文' },
    { id: 'cla', label: 'CLA分析' },
    { id: 'scenarios', label: 'シナリオ' },
    { id: 'weak-signals', label: 'ウィークシグナル' },
    { id: 'settings', label: '設定' },
  ];

  const CLA_FIELDS = ['全体', '政治', '経済', '社会', '技術', '法律', '環境'];

  const CLA_LAYERS = [
    { key: 'layer1_litany', label: 'Layer 1 リタニー（出来事）' },
    { key: 'layer2_causes', label: 'Layer 2 原因（構造）' },
    { key: 'layer3_worldview', label: 'Layer 3 世界観' },
    { key: 'layer4_myth', label: 'Layer 4 メタファー・神話' },
  ];

  const QUADRANT_COLORS = {
    'high-high': '#3498db',
    'low-high': '#2ecc71',
    'high-low': '#f39c12',
    'low-low': '#e74c3c',
  };

  const KNOWN_SOURCES = [
    'Google News',
    'Yahoo!ニュース',
    'NHK',
    'はてなブックマーク',
    'Hacker News',
    'arXiv',
  ];

  // ----------------------------------------------------------
  // State
  // ----------------------------------------------------------

  const state = {
    articles: [],
    lastUpdated: null,
    claIndex: null,
    claData: {},
    scenarios: null,
    activeTab: 'overview',
    filters: {
      pestle: [],
      search: '',
      sort: 'date',
      type: 'all',
      claYear: 2020,
      claField: '全体',
    },
  };

  // Track Chart.js instances so we can destroy before recreating
  let chartInstances = {};

  // ----------------------------------------------------------
  // Utility functions
  // ----------------------------------------------------------

  function formatDate(isoString) {
    if (!isoString) return '';
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
    return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`;
  }

  function formatDateTime(isoString) {
    if (!isoString) return '';
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
    const pad = (n) => String(n).padStart(2, '0');
    return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  }

  function getPestleJa(en) {
    return PESTLE_EN_TO_JA[en] || en;
  }

  function getPestleColor(category) {
    return PESTLE_COLORS[category] || '#888';
  }

  function getSignalLevel(score) {
    if (score >= 7) return 'HIGH';
    if (score >= 4) return 'Medium';
    return 'Low';
  }

  function getSignalBadge(level) {
    const info = SIGNAL_LEVELS[level] || SIGNAL_LEVELS.Low;
    return `<span class="signal-badge signal-${info.label.toLowerCase()}" style="background:${info.color}">${info.label}</span>`;
  }

  function getSignalScoreBadge(score) {
    const level = getSignalLevel(score);
    const info = SIGNAL_LEVELS[level];
    return `<span class="signal-badge signal-${info.label.toLowerCase()}" style="background:${info.color}">${score}/10</span>`;
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function debounce(fn, ms) {
    let timer;
    return function (...args) {
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), ms);
    };
  }

  function filterArticles(articles, filters) {
    let result = articles;

    // Type filter
    if (filters.type && filters.type !== 'all') {
      result = result.filter((a) => a.type === filters.type);
    }

    // PESTLE filter (if any selected, article must have at least one matching)
    if (filters.pestle && filters.pestle.length > 0) {
      result = result.filter((a) =>
        a.pestle && a.pestle.some((p) => filters.pestle.includes(p))
      );
    }

    // Search filter
    if (filters.search && filters.search.trim()) {
      const q = filters.search.trim().toLowerCase();
      result = result.filter(
        (a) =>
          (a.title && a.title.toLowerCase().includes(q)) ||
          (a.summary && a.summary.toLowerCase().includes(q))
      );
    }

    // Sort
    if (filters.sort === 'score') {
      result = result.slice().sort((a, b) => (b.signalScore || 0) - (a.signalScore || 0));
    } else {
      result = result.slice().sort(
        (a, b) => new Date(b.publishedAt || 0) - new Date(a.publishedAt || 0)
      );
    }

    return result;
  }

  // ----------------------------------------------------------
  // Data fetching
  // ----------------------------------------------------------

  async function fetchJSON(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Fetch failed: ${res.status} ${url}`);
    return res.json();
  }

  async function loadData() {
    showLoading(true);
    try {
      const [latestData, claIndex, scenariosData] = await Promise.all([
        fetchJSON(DATA_PATHS.latest).catch(() => null),
        fetchJSON(DATA_PATHS.claIndex).catch(() => null),
        fetchJSON(DATA_PATHS.scenarios).catch(() => null),
      ]);

      if (latestData) {
        state.articles = latestData.articles || [];
        state.lastUpdated = latestData.lastUpdated || null;
      }
      if (claIndex) {
        const years = Array.isArray(claIndex) ? claIndex : (claIndex.years || []);
        state.claIndex = years;
        // Default to latest year
        if (years.length > 0) {
          state.filters.claYear = years[years.length - 1];
        }
      }
      if (scenariosData) {
        state.scenarios = scenariosData;
      }
    } catch (err) {
      console.error('Data load error:', err);
    } finally {
      showLoading(false);
    }
  }

  async function loadCLAYear(year) {
    if (state.claData[year]) return state.claData[year];
    showLoading(true);
    try {
      const data = await fetchJSON(DATA_PATHS.claYear(year));
      state.claData[year] = data;
      return data;
    } catch (err) {
      console.error(`CLA ${year} load error:`, err);
      return null;
    } finally {
      showLoading(false);
    }
  }

  // ----------------------------------------------------------
  // DOM helpers
  // ----------------------------------------------------------

  function $(selector) {
    return document.querySelector(selector);
  }

  function showLoading(show) {
    const el = $('#loading-overlay');
    if (el) el.style.display = show ? 'flex' : 'none';
  }

  function destroyCharts() {
    Object.values(chartInstances).forEach((c) => {
      if (c && typeof c.destroy === 'function') c.destroy();
    });
    chartInstances = {};
  }

  // ----------------------------------------------------------
  // Tab management
  // ----------------------------------------------------------

  function switchTab(tabId) {
    if (state.activeTab === tabId) return;
    destroyCharts();
    state.activeTab = tabId;

    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach((btn) => {
      btn.classList.toggle('active', btn.dataset.tab === tabId);
    });

    renderTab(tabId);
  }

  function renderTab(tabId) {
    const content = $('#tab-content');
    if (!content) return;

    switch (tabId) {
      case 'overview':
        renderOverview(content);
        break;
      case 'pestle-news':
        renderPestleNews(content);
        break;
      case 'papers':
        renderPapers(content);
        break;
      case 'cla':
        renderCLA(content);
        break;
      case 'scenarios':
        renderScenarios(content);
        break;
      case 'weak-signals':
        renderWeakSignals(content);
        break;
      case 'settings':
        renderSettings(content);
        break;
      default:
        content.innerHTML = '<p>Unknown tab</p>';
    }
  }

  // ----------------------------------------------------------
  // 1. Overview
  // ----------------------------------------------------------

  function renderOverview(container) {
    const articles = state.articles;
    const news = articles.filter((a) => a.type === 'news');
    const papers = articles.filter((a) => a.type === 'paper');
    const avgScore =
      articles.length > 0
        ? (articles.reduce((s, a) => s + (a.signalScore || 0), 0) / articles.length).toFixed(1)
        : '---';
    const highSignals = articles
      .filter((a) => a.signalLevel === 'HIGH' || (a.signalScore && a.signalScore >= 7))
      .sort((a, b) => (b.signalScore || 0) - (a.signalScore || 0))
      .slice(0, 5);

    container.innerHTML = `
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-number">${articles.length}</div>
          <div class="stat-label">記事総数</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">${news.length}</div>
          <div class="stat-label">ニュース</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">${papers.length}</div>
          <div class="stat-label">学術論文</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">${avgScore}</div>
          <div class="stat-label">平均シグナルスコア</div>
        </div>
        <div class="stat-card stat-card-wide">
          <div class="stat-number stat-number-small">${state.lastUpdated ? formatDateTime(state.lastUpdated) : '---'}</div>
          <div class="stat-label">最終更新</div>
        </div>
      </div>

      <div class="charts-row">
        <div class="chart-container">
          <h3>PESTLEカテゴリ分布</h3>
          <canvas id="pestle-chart"></canvas>
        </div>
        <div class="chart-container">
          <h3>シグナルレベル分布</h3>
          <canvas id="signal-chart"></canvas>
        </div>
      </div>

      <div class="section">
        <h3>最近のHIGHシグナル</h3>
        ${
          highSignals.length === 0
            ? '<p class="empty-state">HIGHシグナルの記事はありません</p>'
            : `<div class="signal-list">${highSignals
                .map(
                  (a) => `
              <div class="signal-item" data-url="${escapeHtml(a.url || '')}">
                <div class="signal-item-header">
                  ${getSignalScoreBadge(a.signalScore)}
                  <span class="signal-item-title">${escapeHtml(a.title)}</span>
                </div>
                <div class="signal-item-meta">
                  <span>${escapeHtml(a.source || '')}</span>
                  <span>${formatDate(a.publishedAt)}</span>
                  ${(a.pestle || []).map((p) => `<span class="pestle-tag" style="background:${getPestleColor(p)}">${getPestleJa(p)}</span>`).join('')}
                </div>
              </div>`
                )
                .join('')}</div>`
        }
      </div>
    `;

    // Render charts after DOM is ready
    requestAnimationFrame(() => {
      renderPestleChart(articles);
      renderSignalChart(articles);
    });
  }

  function renderPestleChart(articles) {
    const canvas = document.getElementById('pestle-chart');
    if (!canvas || typeof Chart === 'undefined') return;

    const counts = {};
    Object.keys(PESTLE_EN_TO_JA).forEach((k) => (counts[k] = 0));
    articles.forEach((a) => {
      (a.pestle || []).forEach((p) => {
        if (counts[p] !== undefined) counts[p]++;
      });
    });

    const labels = Object.keys(counts).map(getPestleJa);
    const data = Object.values(counts);
    const colors = Object.keys(counts).map(getPestleColor);

    chartInstances.pestle = new Chart(canvas.getContext('2d'), {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{ data, backgroundColor: colors, borderWidth: 2, borderColor: '#fff' }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { padding: 16, font: { size: 13 } } },
        },
      },
    });
  }

  function renderSignalChart(articles) {
    const canvas = document.getElementById('signal-chart');
    if (!canvas || typeof Chart === 'undefined') return;

    const counts = { HIGH: 0, Medium: 0, Low: 0 };
    articles.forEach((a) => {
      const level = a.signalLevel || getSignalLevel(a.signalScore || 0);
      if (counts[level] !== undefined) counts[level]++;
    });

    chartInstances.signal = new Chart(canvas.getContext('2d'), {
      type: 'bar',
      data: {
        labels: ['HIGH', 'Medium', 'Low'],
        datasets: [
          {
            label: '記事数',
            data: [counts.HIGH, counts.Medium, counts.Low],
            backgroundColor: [
              SIGNAL_LEVELS.HIGH.color,
              SIGNAL_LEVELS.Medium.color,
              SIGNAL_LEVELS.Low.color,
            ],
            borderRadius: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { beginAtZero: true, ticks: { stepSize: 1 } },
        },
        plugins: {
          legend: { display: false },
        },
      },
    });
  }

  // ----------------------------------------------------------
  // 2. PESTLE News
  // ----------------------------------------------------------

  function renderPestleNews(container) {
    const newsArticles = state.articles.filter((a) => a.type === 'news');

    // PESTLE category counts
    const pestleCounts = {};
    Object.keys(PESTLE_EN_TO_JA).forEach((k) => (pestleCounts[k] = 0));
    newsArticles.forEach((a) => {
      (a.pestle || []).forEach((p) => {
        if (pestleCounts[p] !== undefined) pestleCounts[p]++;
      });
    });

    container.innerHTML = `
      <div class="filter-bar">
        <div class="search-box">
          <input type="text" id="news-search" placeholder="タイトル・要約で検索..."
                 value="${escapeHtml(state.filters.search)}">
        </div>
        <div class="sort-select">
          <select id="news-sort">
            <option value="date" ${state.filters.sort === 'date' ? 'selected' : ''}>日付順</option>
            <option value="score" ${state.filters.sort === 'score' ? 'selected' : ''}>スコア順</option>
          </select>
        </div>
      </div>
      <div class="pestle-chips" id="pestle-chips">
        ${Object.keys(PESTLE_EN_TO_JA)
          .map(
            (p) => `
          <button class="pestle-chip ${state.filters.pestle.includes(p) ? 'active' : ''}"
                  data-pestle="${p}"
                  style="--chip-color:${getPestleColor(p)}">
            ${getPestleJa(p)} <span class="chip-count">${pestleCounts[p]}</span>
          </button>`
          )
          .join('')}
      </div>
      <div id="news-list" class="article-list"></div>
    `;

    renderNewsArticles();
    bindNewsEvents();
  }

  function renderNewsArticles() {
    const listEl = document.getElementById('news-list');
    if (!listEl) return;

    const newsArticles = state.articles.filter((a) => a.type === 'news');
    const filtered = filterArticles(newsArticles, state.filters);

    if (filtered.length === 0) {
      listEl.innerHTML = '<p class="empty-state">条件に一致するニュースがありません</p>';
      return;
    }

    listEl.innerHTML = filtered
      .map(
        (a) => `
      <div class="article-card" data-url="${escapeHtml(a.url || '')}">
        <div class="article-header">
          <h4 class="article-title">${escapeHtml(a.title)}</h4>
          ${getSignalScoreBadge(a.signalScore)}
        </div>
        <div class="article-meta">
          <span class="article-source">${escapeHtml(a.source || '')}</span>
          <span class="article-date">${formatDate(a.publishedAt)}</span>
        </div>
        <div class="article-tags">
          ${(a.pestle || []).map((p) => `<span class="pestle-tag" style="background:${getPestleColor(p)}">${getPestleJa(p)}</span>`).join('')}
        </div>
        <p class="article-summary">${escapeHtml(a.summary || '')}</p>
      </div>`
      )
      .join('');
  }

  function bindNewsEvents() {
    const searchInput = document.getElementById('news-search');
    const sortSelect = document.getElementById('news-sort');
    const chipsContainer = document.getElementById('pestle-chips');

    if (searchInput) {
      searchInput.addEventListener(
        'input',
        debounce(function () {
          state.filters.search = this.value;
          renderNewsArticles();
        }, 300)
      );
    }

    if (sortSelect) {
      sortSelect.addEventListener('change', function () {
        state.filters.sort = this.value;
        renderNewsArticles();
      });
    }

    if (chipsContainer) {
      chipsContainer.addEventListener('click', function (e) {
        const chip = e.target.closest('.pestle-chip');
        if (!chip) return;
        const p = chip.dataset.pestle;
        const idx = state.filters.pestle.indexOf(p);
        if (idx >= 0) {
          state.filters.pestle.splice(idx, 1);
          chip.classList.remove('active');
        } else {
          state.filters.pestle.push(p);
          chip.classList.add('active');
        }
        renderNewsArticles();
      });
    }
  }

  // ----------------------------------------------------------
  // 3. Papers
  // ----------------------------------------------------------

  function renderPapers(container) {
    const papers = state.articles.filter((a) => a.type === 'paper');

    // Gather all unique arxiv categories
    const categorySet = new Set();
    papers.forEach((a) => {
      (a.arxivCategories || []).forEach((c) => categorySet.add(c));
    });
    const categories = Array.from(categorySet).sort();

    container.innerHTML = `
      <div class="filter-bar">
        <div class="search-box">
          <input type="text" id="paper-search" placeholder="タイトル・要約で検索..."
                 value="${escapeHtml(state.filters.search)}">
        </div>
        <div class="sort-select">
          <select id="paper-category-filter">
            <option value="">全カテゴリ</option>
            ${categories.map((c) => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join('')}
          </select>
        </div>
        <div class="sort-select">
          <select id="paper-sort">
            <option value="date" ${state.filters.sort === 'date' ? 'selected' : ''}>日付順</option>
            <option value="score" ${state.filters.sort === 'score' ? 'selected' : ''}>スコア順</option>
          </select>
        </div>
      </div>
      <div id="paper-list" class="article-list"></div>
    `;

    renderPaperList();
    bindPaperEvents();
  }

  function renderPaperList(categoryFilter) {
    const listEl = document.getElementById('paper-list');
    if (!listEl) return;

    let papers = state.articles.filter((a) => a.type === 'paper');

    // Category filter
    if (categoryFilter) {
      papers = papers.filter(
        (a) => a.arxivCategories && a.arxivCategories.includes(categoryFilter)
      );
    }

    const filtered = filterArticles(papers, {
      ...state.filters,
      type: 'all', // already filtered by type above
    });

    if (filtered.length === 0) {
      listEl.innerHTML = '<p class="empty-state">条件に一致する論文がありません</p>';
      return;
    }

    listEl.innerHTML = filtered
      .map(
        (a) => `
      <div class="article-card paper-card">
        <div class="article-header">
          <h4 class="article-title">${escapeHtml(a.title)}</h4>
          ${getSignalScoreBadge(a.signalScore)}
        </div>
        <div class="article-meta">
          <span class="article-date">${formatDate(a.publishedAt)}</span>
          ${a.arxivId ? `<span class="arxiv-id">arXiv: ${escapeHtml(a.arxivId)}</span>` : ''}
        </div>
        <div class="article-tags">
          ${(a.arxivCategories || []).map((c) => `<span class="category-tag">${escapeHtml(c)}</span>`).join('')}
          ${(a.pestle || []).map((p) => `<span class="pestle-tag" style="background:${getPestleColor(p)}">${getPestleJa(p)}</span>`).join('')}
        </div>
        <p class="article-summary">${escapeHtml(a.summary || '')}</p>
        <div class="article-actions">
          ${a.url ? `<a href="${escapeHtml(a.url)}" target="_blank" rel="noopener" class="btn btn-primary btn-sm">arXivで読む</a>` : ''}
        </div>
      </div>`
      )
      .join('');
  }

  function bindPaperEvents() {
    const searchInput = document.getElementById('paper-search');
    const catSelect = document.getElementById('paper-category-filter');
    const sortSelect = document.getElementById('paper-sort');

    let currentCategory = '';

    if (searchInput) {
      searchInput.addEventListener(
        'input',
        debounce(function () {
          state.filters.search = this.value;
          renderPaperList(currentCategory);
        }, 300)
      );
    }

    if (catSelect) {
      catSelect.addEventListener('change', function () {
        currentCategory = this.value;
        renderPaperList(currentCategory);
      });
    }

    if (sortSelect) {
      sortSelect.addEventListener('change', function () {
        state.filters.sort = this.value;
        renderPaperList(currentCategory);
      });
    }
  }

  // ----------------------------------------------------------
  // 4. CLA Analysis
  // ----------------------------------------------------------

  function renderCLA(container) {
    const years = state.claIndex || [];

    container.innerHTML = `
      <div class="cla-year-selector" id="cla-year-selector">
        ${years
          .map(
            (y) => `
          <button class="year-btn ${y === state.filters.claYear ? 'active' : ''}"
                  data-year="${y}">${y}</button>`
          )
          .join('')}
      </div>
      <div class="cla-field-tabs" id="cla-field-tabs">
        ${CLA_FIELDS.map(
          (f) => `
          <button class="field-tab ${f === state.filters.claField ? 'active' : ''}"
                  data-field="${f}">${f}</button>`
        ).join('')}
      </div>
      <div id="cla-content" class="cla-content">
        <p class="empty-state">読み込み中...</p>
      </div>
    `;

    bindCLAEvents();
    loadAndRenderCLA();
  }

  async function loadAndRenderCLA() {
    const contentEl = document.getElementById('cla-content');
    if (!contentEl) return;

    const year = state.filters.claYear;
    const field = state.filters.claField;

    const data = await loadCLAYear(year);

    if (!data || !data.fields || !data.fields[field]) {
      contentEl.innerHTML = `<p class="empty-state">${year}年のCLAデータがありません</p>`;
      return;
    }

    const fieldData = data.fields[field];
    const sources = data.sources || [];

    contentEl.innerHTML = `
      <div class="cla-layers">
        ${CLA_LAYERS.map(
          (layer, i) => `
          <div class="cla-layer-card" data-layer="${i}">
            <div class="cla-layer-header">
              <h4>${layer.label}</h4>
              <span class="expand-icon">&#9660;</span>
            </div>
            <div class="cla-layer-body expanded">
              <p>${escapeHtml(fieldData[layer.key] || 'データなし')}</p>
            </div>
          </div>`
        ).join('')}
      </div>
      ${
        sources.length > 0
          ? `<div class="cla-sources">
              <h4>出典</h4>
              <ul>
                ${sources
                  .map(
                    (s) => `
                  <li>
                    ${s.url ? `<a href="${escapeHtml(s.url)}" target="_blank" rel="noopener">${escapeHtml(s.title)}</a>` : escapeHtml(s.title)}
                    ${s.addedAt ? `<span class="source-date">(${formatDate(s.addedAt)})</span>` : ''}
                  </li>`
                  )
                  .join('')}
              </ul>
            </div>`
          : ''
      }
      ${data.generatedBy ? `<p class="cla-meta">生成: ${escapeHtml(data.generatedBy)} | 更新: ${formatDate(data.updatedAt)}</p>` : ''}
    `;

    // Bind expand/collapse
    contentEl.querySelectorAll('.cla-layer-card').forEach((card) => {
      card.querySelector('.cla-layer-header').addEventListener('click', function () {
        const body = card.querySelector('.cla-layer-body');
        const icon = card.querySelector('.expand-icon');
        body.classList.toggle('expanded');
        icon.textContent = body.classList.contains('expanded') ? '\u25BC' : '\u25B6';
      });
    });
  }

  function bindCLAEvents() {
    const yearSelector = document.getElementById('cla-year-selector');
    const fieldTabs = document.getElementById('cla-field-tabs');

    if (yearSelector) {
      yearSelector.addEventListener('click', function (e) {
        const btn = e.target.closest('.year-btn');
        if (!btn) return;
        const year = parseInt(btn.dataset.year, 10);
        state.filters.claYear = year;
        yearSelector.querySelectorAll('.year-btn').forEach((b) =>
          b.classList.toggle('active', parseInt(b.dataset.year, 10) === year)
        );
        loadAndRenderCLA();
      });
    }

    if (fieldTabs) {
      fieldTabs.addEventListener('click', function (e) {
        const btn = e.target.closest('.field-tab');
        if (!btn) return;
        const field = btn.dataset.field;
        state.filters.claField = field;
        fieldTabs.querySelectorAll('.field-tab').forEach((b) =>
          b.classList.toggle('active', b.dataset.field === field)
        );
        loadAndRenderCLA();
      });
    }
  }

  // ----------------------------------------------------------
  // 5. Scenarios
  // ----------------------------------------------------------

  function renderScenarios(container) {
    const data = state.scenarios;

    if (!data || !data.axes || !data.quadrants) {
      container.innerHTML = '<p class="empty-state">シナリオデータがありません</p>';
      return;
    }

    const axes = data.axes;
    const quadrants = data.quadrants;

    // Map position to grid placement
    const positionMap = {
      'low-high': { row: 1, col: 1 },
      'high-high': { row: 1, col: 2 },
      'low-low': { row: 2, col: 1 },
      'high-low': { row: 2, col: 2 },
    };

    const quadrantHtml = quadrants
      .map((q) => {
        const pos = positionMap[q.position] || { row: 1, col: 1 };
        const color = QUADRANT_COLORS[q.position] || '#888';
        const likelihood = q.likelihood != null ? Math.round(q.likelihood * 100) : null;
        return `
        <div class="scenario-quadrant"
             style="grid-row:${pos.row};grid-column:${pos.col};background:${color}15;border-left:4px solid ${color}">
          <h4 class="quadrant-name" style="color:${color}">${escapeHtml(q.name)}</h4>
          ${likelihood != null ? `<div class="quadrant-likelihood">${likelihood}%</div>` : ''}
          <p class="quadrant-desc">${escapeHtml(q.description || '')}</p>
        </div>`;
      })
      .join('');

    container.innerHTML = `
      <div class="scenario-matrix">
        <div class="axis-label axis-y-high">${escapeHtml(axes.y.high)}</div>
        <div class="axis-label axis-y-low">${escapeHtml(axes.y.low)}</div>
        <div class="axis-label axis-y-name">${escapeHtml(axes.y.label)}</div>
        <div class="axis-label axis-x-low">${escapeHtml(axes.x.low)}</div>
        <div class="axis-label axis-x-high">${escapeHtml(axes.x.high)}</div>
        <div class="axis-label axis-x-name">${escapeHtml(axes.x.label)}</div>
        <div class="matrix-grid">
          ${quadrantHtml}
        </div>
      </div>
    `;
  }

  // ----------------------------------------------------------
  // 6. Weak Signals
  // ----------------------------------------------------------

  function renderWeakSignals(container) {
    const articles = state.articles.filter((a) => a.signalScore != null);

    const high = articles.filter((a) => a.signalScore >= 7).sort((a, b) => b.signalScore - a.signalScore);
    const medium = articles.filter((a) => a.signalScore >= 4 && a.signalScore < 7).sort((a, b) => b.signalScore - a.signalScore);
    const low = articles.filter((a) => a.signalScore < 4).sort((a, b) => b.signalScore - a.signalScore);

    function renderSection(label, items, level) {
      const info = SIGNAL_LEVELS[level];
      return `
        <div class="signal-section">
          <div class="signal-section-header" data-section="${level}">
            <h3>
              ${label}
              <span class="count-badge" style="background:${info.color}">${items.length}</span>
            </h3>
            <span class="expand-icon">&#9660;</span>
          </div>
          <div class="signal-section-body expanded">
            ${
              items.length === 0
                ? '<p class="empty-state">該当なし</p>'
                : items
                    .map(
                      (a) => `
                <div class="signal-card" data-url="${escapeHtml(a.url || '')}">
                  <div class="signal-card-header">
                    ${getSignalScoreBadge(a.signalScore)}
                    <span class="signal-card-title">${escapeHtml(a.title)}</span>
                  </div>
                  <div class="signal-card-meta">
                    <span>${escapeHtml(a.source || '')}</span>
                    ${(a.pestle || []).map((p) => `<span class="pestle-tag" style="background:${getPestleColor(p)}">${getPestleJa(p)}</span>`).join('')}
                  </div>
                  <p class="signal-card-summary">${escapeHtml(a.summary || '')}</p>
                </div>`
                    )
                    .join('')
            }
          </div>
        </div>`;
    }

    container.innerHTML = `
      <div class="weak-signals">
        ${renderSection('HIGH シグナル (7+)', high, 'HIGH')}
        ${renderSection('Medium シグナル (4-6)', medium, 'Medium')}
        ${renderSection('Low シグナル (0-3)', low, 'Low')}
      </div>
    `;

    // Bind expand/collapse
    container.querySelectorAll('.signal-section-header').forEach((header) => {
      header.addEventListener('click', function () {
        const body = header.nextElementSibling;
        const icon = header.querySelector('.expand-icon');
        body.classList.toggle('expanded');
        icon.textContent = body.classList.contains('expanded') ? '\u25BC' : '\u25B6';
      });
    });
  }

  // ----------------------------------------------------------
  // 7. Settings
  // ----------------------------------------------------------

  function renderSettings(container) {
    const articles = state.articles;

    // Determine seen sources
    const seenSources = new Set(articles.map((a) => a.source).filter(Boolean));

    // Date range
    const dates = articles.map((a) => new Date(a.publishedAt)).filter((d) => !isNaN(d.getTime()));
    const minDate = dates.length > 0 ? new Date(Math.min(...dates)) : null;
    const maxDate = dates.length > 0 ? new Date(Math.max(...dates)) : null;

    container.innerHTML = `
      <div class="settings-section">
        <h3>ソースステータス</h3>
        <div class="table-wrap">
          <table class="source-table">
            <thead>
              <tr><th>ソース名</th><th>ステータス</th></tr>
            </thead>
            <tbody>
              ${KNOWN_SOURCES.map(
                (src) => `
                <tr>
                  <td>${escapeHtml(src)}</td>
                  <td>
                    ${
                      seenSources.has(src)
                        ? '<span class="status-ok">有効</span>'
                        : '<span class="status-na">データなし</span>'
                    }
                  </td>
                </tr>`
              ).join('')}
            </tbody>
          </table>
        </div>
      </div>

      <div class="settings-section">
        <h3>データ統計</h3>
        <dl class="settings-dl">
          <dt>記事数</dt><dd>${articles.length}</dd>
          <dt>ニュース</dt><dd>${articles.filter((a) => a.type === 'news').length}</dd>
          <dt>論文</dt><dd>${articles.filter((a) => a.type === 'paper').length}</dd>
          <dt>日付範囲</dt>
          <dd>${minDate && maxDate ? `${formatDate(minDate.toISOString())} 〜 ${formatDate(maxDate.toISOString())}` : '---'}</dd>
          <dt>最終更新</dt><dd>${state.lastUpdated ? formatDateTime(state.lastUpdated) : '---'}</dd>
        </dl>
      </div>

      <div class="settings-section">
        <h3>データエクスポート</h3>
        <button class="btn btn-primary" id="export-json-btn">JSONエクスポート</button>
      </div>

      <div class="settings-section">
        <h3>アプリ情報</h3>
        <dl class="settings-dl">
          <dt>アプリ名</dt><dd>未来洞察支援アプリ</dd>
          <dt>バージョン</dt><dd>1.0.0</dd>
          <dt>ビルド</dt><dd>Vanilla JS (no build step)</dd>
        </dl>
      </div>
    `;

    const exportBtn = document.getElementById('export-json-btn');
    if (exportBtn) {
      exportBtn.addEventListener('click', function () {
        const blob = new Blob(
          [JSON.stringify({ lastUpdated: state.lastUpdated, articles: state.articles }, null, 2)],
          { type: 'application/json' }
        );
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'latest.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      });
    }
  }

  // ----------------------------------------------------------
  // Event delegation (global)
  // ----------------------------------------------------------

  function initGlobalEvents() {
    // Tab switching
    const tabBar = document.getElementById('tab-bar');
    if (tabBar) {
      tabBar.addEventListener('click', function (e) {
        const btn = e.target.closest('.tab-btn');
        if (!btn) return;
        switchTab(btn.dataset.tab);
      });
    }

    // Click on article / signal cards -> open URL
    document.addEventListener('click', function (e) {
      const card =
        e.target.closest('.article-card') ||
        e.target.closest('.signal-item') ||
        e.target.closest('.signal-card');
      if (!card) return;
      // Don't intercept if clicking a link or button inside the card
      if (e.target.closest('a') || e.target.closest('button')) return;
      const url = card.dataset.url;
      if (url) window.open(url, '_blank', 'noopener');
    });
  }

  // ----------------------------------------------------------
  // Bootstrap HTML shell
  // ----------------------------------------------------------

  function buildShell() {
    const app = document.getElementById('app');
    if (!app) {
      console.error('#app element not found');
      return;
    }

    app.innerHTML = `
      <div id="loading-overlay" class="loading-overlay" style="display:none">
        <div class="spinner"></div>
      </div>
      <header class="app-header">
        <h1 class="app-title">未来洞察支援アプリ</h1>
        <p class="app-subtitle">Future Insight Support App</p>
      </header>
      <nav id="tab-bar" class="tab-bar">
        ${TABS.map(
          (t) => `
          <button class="tab-btn ${t.id === 'overview' ? 'active' : ''}"
                  data-tab="${t.id}">${t.label}</button>`
        ).join('')}
      </nav>
      <main id="tab-content" class="tab-content">
        <p class="empty-state">読み込み中...</p>
      </main>
      <footer class="app-footer">
        <p>未来洞察支援アプリ v1.0.0</p>
      </footer>
    `;
  }

  // ----------------------------------------------------------
  // Init
  // ----------------------------------------------------------

  async function init() {
    buildShell();
    initGlobalEvents();
    await loadData();
    renderTab(state.activeTab);
  }

  // Start when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
