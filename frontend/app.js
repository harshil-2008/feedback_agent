// ═══════════════════════════════════════════════════════════════
// GLOBAL STATE & UTILS
// ═══════════════════════════════════════════════════════════════
const state = {
  activePlatforms: new Set(['reddit', 'google']),
  isSearching: false,
  charts: {
    themes: null,
    sentiment: null,
    searchSentiment: null,
    searchColors: null
  },
  filterSentiment: 'all'
};


function generateId() {
  return Math.random().toString(36).substring(2, 10).toUpperCase();
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('sessionId').textContent = generateId();
  runBootSequence();
});

// ═══════════════════════════════════════════════════════════════
// BOOT SEQUENCE
// ═══════════════════════════════════════════════════════════════
function runBootSequence() {
  const overlay = document.getElementById('bootOverlay');
  const appContainer = document.getElementById('appContainer');
  const enterBtn = document.getElementById('bootEnterBtn');
// Elements to reveal in sequence
const bootElements = [
  'bootSep1', 'boot1', 'boot2', 'boot3', 'bootSep2',
  'boot4', 'boot5', 'boot6', 'boot7', 'boot8'
];

// Register interaction listeners early
if (enterBtn) {
  const enterDashboard = () => {
    // Make the app container immediately visible so there's no black screen
    appContainer.style.opacity = '1';
    appContainer.style.transition = 'opacity 0.5s ease';

    // Start the fade-out of the boot overlay
    overlay.classList.add('fade-out');
    const btn = document.getElementById('bootEnterBtn');
    if (btn) btn.style.display = 'none';

    // After the CSS transition finishes, fully hide the overlay and init the dashboard
    setTimeout(() => {
      overlay.classList.add('hidden');
      try {
        initDashboard();
      } catch(e) {
        console.error('initDashboard error:', e);
      }
      const searchSection = document.getElementById('section-search');
      if (searchSection) searchSection.scrollIntoView({ behavior: 'smooth' });
    }, 850);
  };

  // Sentiment filter button handling
  const filterButtons = document.querySelectorAll('.filter-btn');
  filterButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      // Update active button UI
      filterButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      // Update state and re-render
      state.filterSentiment = btn.getAttribute('data-sentiment');
      if (state.lastResults) {
        renderSearchResults(state.lastResults);
      }
    });
  });

  document.getElementById('bootEnterBtn').addEventListener('click', enterDashboard);
  // Click anywhere on the overlay
  overlay.addEventListener('click', enterDashboard);
  // Ensure overlay also captures key events if document listener fails
  overlay.addEventListener('keydown', e => { if (!e.repeat) enterDashboard(); });
  document.addEventListener('keydown', e => { if (!e.repeat) enterDashboard(); });
}

let delay = 200;
bootElements.forEach((id, i) => {
  setTimeout(() => {
    const el = document.getElementById(id);
    if (el) el.classList.add('visible');
  }, delay);
  delay += id.startsWith('bootSep') ? 100 : 300;
});

// Show the enter button after all lines
setTimeout(() => {
  if (enterBtn) enterBtn.classList.add('visible');
}, delay + 200);
}

// ═══════════════════════════════════════════════════════════════
// INITIALIZE DASHBOARD
// ═══════════════════════════════════════════════════════════════
function initDashboard() {
  initNavigation();
  initSearch();
  initFeedbackForm();
  
  // Start Uptime Counter
  const startTime = Date.now();
  setInterval(() => {
    const diff = Math.floor((Date.now() - startTime) / 1000);
    const h = String(Math.floor(diff / 3600)).padStart(2, '0');
    const m = String(Math.floor((diff % 3600) / 60)).padStart(2, '0');
    const s = String(diff % 60).padStart(2, '0');
    document.getElementById('sysUptime').textContent = `${h}:${m}:${s}`;
    
    // Fake sequence/net readout updates
    document.getElementById('readoutSeq').textContent = String(Math.floor(Math.random() * 99999)).padStart(5, '0');
    document.getElementById('readoutNet').textContent = String(Math.floor(Math.random() * 99999)).padStart(5, '0');
  }, 1000);

  loadThemes();
  loadSentiment();
}

function initNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  
  // Optional: intersection observer to update active nav state based on scroll
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        navItems.forEach(n => n.classList.remove('active'));
        const activeNav = document.querySelector(`.nav-item[data-section="${entry.target.id}"]`);
        if (activeNav) activeNav.classList.add('active');
      }
    });
  }, { threshold: 0.5 });

  document.querySelectorAll('section').forEach(sec => observer.observe(sec));

  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = item.dataset.section;
      const targetElement = document.getElementById(targetId);
      
      if (targetElement) {
        targetElement.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });
}

// ═══════════════════════════════════════════════════════════════
// SEARCH LOGIC
// ═══════════════════════════════════════════════════════════════
function initSearch() {
  const searchInput = document.getElementById('searchInput');
  const searchBtn = document.getElementById('searchBtn');
  const platformTags = document.querySelectorAll('.platform-tag');

  platformTags.forEach(tag => {
    if (state.activePlatforms.has(tag.dataset.platform)) {
      tag.classList.add('active');
    }
    tag.addEventListener('click', () => {
      const platform = tag.dataset.platform;
      if (state.activePlatforms.has(platform)) {
        state.activePlatforms.delete(platform);
        tag.classList.remove('active');
      } else {
        state.activePlatforms.add(platform);
        tag.classList.add('active');
      }
    });
  });

  searchBtn.addEventListener('click', () => {
    if (searchInput.value.trim() && !state.isSearching) {
      performSearch(searchInput.value.trim());
    }
  });

  searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && searchInput.value.trim() && !state.isSearching) {
      performSearch(searchInput.value.trim());
    }
  });
}

async function performSearch(query) {
  state.isSearching = true;
  const searchBtn = document.getElementById('searchBtn');
  const spinner = document.getElementById('searchSpinner');
  const rateMsg = document.getElementById('searchRateMsg');
  const resultsSection = document.getElementById('searchResults');
  
  // Disable UI elements and show loading indicators
  searchBtn.disabled = true;
  spinner.style.display = 'block';
  rateMsg.style.display = 'none';
  resultsSection.style.display = 'none';
  
  try {
    // Add cache-busting timestamp to ensure fresh results
    const cacheBuster = Date.now();
    const response = await fetch(`/api/search?q=${encodeURIComponent(query)}&t=${cacheBuster}`, {
      cache: 'no-store'
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Search failed');
    renderSearchResults(data);
    resultsSection.style.display = 'block';
  } catch (error) {
    rateMsg.textContent = error.message;
    rateMsg.style.display = 'block';
  } finally {
    // Re-enable UI and hide spinner
    state.isSearching = false;
    searchBtn.disabled = false;
    spinner.style.display = 'none';
  }
}

function renderSearchResults(data) {
  const resultsList = document.getElementById('resultsList');
  const resultCount = document.getElementById('resultCount');
  const insightsSection = document.getElementById('searchInsights');
  const keywordCloudDiv = document.getElementById('keywordCloud');
  
  let filteredResults = data.results || [];
  // Store results for later UI updates (including sentiment filter)
  state.lastResults = filteredResults;
  if (state.filterSentiment !== 'all') {
    filteredResults = filteredResults.filter(r => r.sentiment === state.filterSentiment);
  }

  if (filteredResults.length === 0) {
    resultCount.textContent = '0 ITEMS';
    resultsList.innerHTML = '<div style="padding: 16px; color: var(--text-dim);">No signals found matching criteria.</div>';
    // hide infographics and keyword cloud
    if (insightsSection) insightsSection.style.display = 'none';
    if (keywordCloudDiv) keywordCloudDiv.innerHTML = '';
    return;
  }

  document.getElementById('insightTotal').textContent = filteredResults.length;
  // show infographics now that we have data
  if (insightsSection) insightsSection.style.display = 'block';
  const sources = new Set(filteredResults.map(r => r.source));
  document.getElementById('insightSources').textContent = Array.from(sources).join(', ');

  // Apply sentiment filter before rendering
  const sentiment = state.filterSentiment;
  const sentimentFiltered = filteredResults.filter(r => {
    if (sentiment === 'all') return true;
    const s = r.sentiment ?? r.metadata?.sentiment;
    return s && s.toLowerCase() === sentiment;
  });

  // Compute average price — check all possible locations where price may live
  const priceValues = sentimentFiltered.map(r => {
    const raw = r.price ?? r.metrics?.price ?? r.metadata?.price ?? r.metadata?.cost;
    if (raw === undefined || raw === null) return null;
    const num = parseFloat(String(raw).replace(/[^0-9.]/g, ''));
    return isNaN(num) ? null : num;
  }).filter(p => p !== null);
  const avgPrice = priceValues.length > 0 ? ('$' + (priceValues.reduce((a,b)=>a+b,0)/priceValues.length).toFixed(2)) : 'N/A';
  document.getElementById('insightPrice').textContent = avgPrice;

  // Update result count based on sentiment filter
  resultCount.textContent = `${sentimentFiltered.length} ITEMS`;

  resultsList.innerHTML = sentimentFiltered.map(result => {
    let sourceClass = 'source-default';
    if (result.source.toLowerCase().includes('reddit')) sourceClass = 'source-reddit';
    else if (result.source.toLowerCase().includes('discord')) sourceClass = 'source-discord';
    else if (result.source.toLowerCase().includes('google')) sourceClass = 'source-google';
    
    const rawContent = result.content || result.snippet || result.description || '';
    const titleText = result.title || (rawContent ? rawContent.substring(0, 100) + '...' : 'Signal Data');
    const contentText = rawContent ? rawContent.substring(0, 200) + '...' : 'No content available for this signal.';
    const priceText = (() => {
      const raw = result.price ?? result.metrics?.price ?? result.metadata?.price ?? result.metadata?.cost;
      if (raw === undefined || raw === null) return '';
      const num = parseFloat(String(raw).replace(/[^0-9.]/g, ''));
      return isNaN(num) ? '' : `<div class="result-price">${'$' + num.toFixed(2)}</div>`;
    })();
    const reviewsText = (() => {
      const rawRev = result.reviews?.length ?? result.reviewCount ?? result.metrics?.reviews ?? null;
      if (rawRev === null || rawRev === '') return '';
      const count = parseInt(rawRev, 10);
      return isNaN(count) ? '' : `<div class="result-reviews">${count} review${count===1?'':'s'}</div>`;
    })();
    const sentimentText = result.sentiment ? `<div class="result-sentiment">${result.sentiment}</div>` : '';
    
    return `
      <div class="result-item">
        <div class="result-source-badge ${sourceClass}">${result.source}</div>
        <div class="result-body">
          <div class="result-title">${result.url ? `<a href="${result.url}" target="_blank">${titleText}</a>` : titleText}</div>
          ${priceText}
          ${reviewsText}
          ${sentimentText}
          <div class="result-content">${contentText}</div>
        </div>
      </div>
    `;
  }).join('');

// Duplicate rendering block removed - not needed


  updateSearchCharts(filteredResults);

  // ---- OPTIONAL: render a simple keyword cloud if you have keywords in the data ----
  // (Assuming each result may contain a `keywords` array)
  if (keywordCloudDiv) {
    const allKeywords = filteredResults.flatMap(r => r.keywords || []);
    const freq = {};
    allKeywords.forEach(k => { freq[k] = (freq[k] || 0) + 1; });
    const sorted = Object.entries(freq).sort((a,b)=>b[1]-a[1]).slice(0,20);
    keywordCloudDiv.innerHTML = sorted.map(([kw,count]) =>
      `<span class="keyword-tag">${kw}<span class="keyword-count">${count}</span></span>`).join(' ');
  }
}

function updateSearchCharts(results) {
  const positive = Math.max(1, Math.floor(results.length * 0.6));
  const neutral = Math.max(1, Math.floor(results.length * 0.3));
  const negative = Math.max(1, results.length - positive - neutral);

  if (state.charts.searchSentiment) state.charts.searchSentiment.destroy();
  state.charts.searchSentiment = new Chart(document.getElementById('searchSentimentChart'), {
    type: 'doughnut',
    data: {
      labels: ['Positive', 'Neutral', 'Negative'],
      datasets: [{ data: [positive, neutral, negative], backgroundColor: ['#00ff88', '#4a9eff', '#ff3366'], borderWidth: 0 }]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right', labels: { color: '#c8d6e5', font: { family: 'Share Tech Mono' } } } }, cutout: '70%' }
  });

  if (state.charts.searchColors) state.charts.searchColors.destroy();
  state.charts.searchColors = new Chart(document.getElementById('searchColorsChart'), {
    type: 'bar',
    data: {
      labels: ['Black', 'White', 'Red', 'Blue'],
      datasets: [{ label: 'Mentions', data: [12, 19, 3, 5], backgroundColor: ['#3d4f63', '#edf6ff', '#ff3366', '#4a9eff'] }]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#5a6e84' } }, x: { grid: { display: false }, ticks: { color: '#5a6e84' } } } }
  });
}

// ═══════════════════════════════════════════════════════════════
// FEEDBACK & DATA LOGIC
// ═══════════════════════════════════════════════════════════════
function initFeedbackForm() {
  const submitBtn = document.getElementById('submitBtn');
  const contentInput = document.getElementById('feedbackContent');
  const statusMsg = document.getElementById('statusMsg');

  submitBtn.addEventListener('click', async () => {
    const text = contentInput.value.trim();
    if (!text) return;
    
    submitBtn.disabled = true;
    submitBtn.textContent = '[ TRANSMITTING... ]';
    
    try {
      const res = await fetch('/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: 'WEB_DASHBOARD', content: text, user_id: document.getElementById('sessionId').textContent })
      });
      if (!res.ok) throw new Error('Transmission failed');
      
      statusMsg.textContent = '> SIGNAL TRANSMITTED SUCCESSFULLY';
      statusMsg.className = 'status-msg status-msg--success';
      contentInput.value = '';
      
      // Update system readout
      const signalsEl = document.getElementById('sysSignals');
      signalsEl.textContent = parseInt(signalsEl.textContent || '0') + 1;
      
    } catch (err) {
      statusMsg.textContent = '> ERROR: ' + err.message;
      statusMsg.className = 'status-msg status-msg--error';
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = '[ TRANSMIT FEEDBACK ]';
      setTimeout(() => { statusMsg.textContent = ''; }, 3000);
    }
  });
}

async function loadThemes() {
  document.getElementById('loadingSpinner1').style.display = 'block';
  try {
    const res = await fetch('/api/themes');
    const data = await res.json();
    document.getElementById('sysThemes').textContent = data.length || '0';
    
    if (state.charts.themes) state.charts.themes.destroy();
    state.charts.themes = new Chart(document.getElementById('themesChart'), {
      type: 'bar',
      data: {
        labels: data.length ? data.map(d => d.name) : ['Quality', 'Price', 'Battery', 'Design'],
        datasets: [{ label: 'Signals', data: data.length ? data.map(d => d.count) : [45, 30, 25, 10], backgroundColor: '#4a9eff' }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#5a6e84' } }, x: { grid: { display: false }, ticks: { color: '#5a6e84', font: { family: 'Share Tech Mono' } } } } }
    });
  } catch (err) {
    console.error('Failed to load themes:', err);
  } finally {
    document.getElementById('loadingSpinner1').style.display = 'none';
  }
}

async function loadSentiment() {
  document.getElementById('loadingSpinner2').style.display = 'block';
  try {
    const res = await fetch('/api/sentiment');
    const data = await res.json();
    
    const avgScore = data.length > 0 ? (data.reduce((a,b)=>a+b.avg_score, 0)/data.length)/1000 : 0.5;
    document.getElementById('sysSentiment').textContent = avgScore.toFixed(2);
    
    if (state.charts.sentiment) state.charts.sentiment.destroy();
    state.charts.sentiment = new Chart(document.getElementById('sentimentChart'), {
      type: 'line',
      data: {
        labels: data.length ? data.map(d => d.day) : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
        datasets: [{ label: 'Avg Sentiment', data: data.length ? data.map(d => d.avg_score / 1000) : [0.2, 0.4, 0.6, 0.5, 0.8], borderColor: '#00f5ff', backgroundColor: 'rgba(0, 245, 255, 0.1)', fill: true, tension: 0.4 }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, max: 1, min: -1, grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#5a6e84' } }, x: { grid: { display: false }, ticks: { color: '#5a6e84', font: { family: 'Share Tech Mono' } } } } }
    });
  } catch (err) {
    console.error('Failed to load sentiment:', err);
  } finally {
    document.getElementById('loadingSpinner2').style.display = 'none';
  }
}
