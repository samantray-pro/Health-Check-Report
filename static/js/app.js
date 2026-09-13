/**
 * Local Health Checkup Tracker - Frontend Client Logic
 */

let activeProfileId = null;
let currentProfiles = [];
let detectedOcrPayload = null;
let sparklineCharts = {};
let detailedChartInstance = null;

// View Mode & Filter State
let rawCards = [];
let currentCategories = [];
let currentCategory = "all";
let currentViewMode = localStorage.getItem("health_tracker_view_mode") || "grid";
let currentFilter = "all"; // 'all', 'abnormal', 'normal', 'frequent'
let currentSort = "recent"; // 'recent', 'abnormal_first', 'name_asc', 'name_desc'
let searchQuery = "";
let expandedCategories = new Set();

const CATEGORY_ICONS = {
  "all": "🧬",
  "Diabetes & Glycemic": "🩸",
  "Complete Blood Count (CBC)": "🔬",
  "Lipid Profile": "🫀",
  "Liver Function (LFT)": "🧪",
  "Kidney Function (KFT)": "💧",
  "Thyroid Profile": "🦋",
  "Vitamins & Minerals": "💊",
  "Iron Studies": "🧲",
  "Cardiac & Inflammation": "❤️‍🔥",
  "Hormones & Immunology": "🛡️",
  "Coagulation & Hemostasis": "🩸",
  "Blood Smear & Morphology": "🔬",
  "Urine Routine Examination": "🧪",
  "General / Other": "📋"
};

document.addEventListener("DOMContentLoaded", () => {
  fetchSystemInfo();
  loadProfiles();
  setupEventListeners();
});

// --- System & Local LAN Detection ---
async function fetchSystemInfo() {
  try {
    const res = await fetch("/api/system/info");
    const data = await res.json();
    const lanElement = document.getElementById("lan-ip-display");
    if (lanElement) {
      lanElement.textContent = data.network_url;
      lanElement.dataset.url = data.network_url;
    }
  } catch (err) {
    console.warn("Could not fetch network IP", err);
  }
}

function copyLanUrl() {
  const lanElement = document.getElementById("lan-ip-display");
  const url = lanElement ? lanElement.dataset.url : "";
  if (url) {
    navigator.clipboard.writeText(url).then(() => {
      const btn = document.getElementById("btn-copy-lan");
      const orig = btn.textContent;
      btn.textContent = "✓ Copied!";
      setTimeout(() => (btn.textContent = orig), 2000);
    });
  }
}

// --- Profiles Management ---
async function loadProfiles(selectProfileId = null) {
  try {
    const res = await fetch("/api/profiles");
    currentProfiles = await res.json();
    const select = document.getElementById("profile-select");
    select.innerHTML = "";

    if (currentProfiles.length === 0) {
      document.getElementById("no-profiles-state").style.display = "block";
      document.getElementById("main-dashboard-content").style.display = "none";
      return;
    }

    document.getElementById("no-profiles-state").style.display = "none";
    document.getElementById("main-dashboard-content").style.display = "block";

    currentProfiles.forEach((p) => {
      const opt = document.createElement("option");
      opt.value = p.id;
      opt.textContent = `${p.name} (${p.age}y, ${p.gender})`;
      select.appendChild(opt);
    });

    // Select specified or first profile
    activeProfileId = selectProfileId || currentProfiles[0].id;
    select.value = activeProfileId;
    loadDashboard(activeProfileId);
  } catch (err) {
    console.error("Failed to load profiles:", err);
  }
}

function switchProfile(profileId) {
  activeProfileId = parseInt(profileId);
  currentCategory = "all";
  loadDashboard(activeProfileId);
}

// --- Dashboard Loading ---
async function loadDashboard(profileId) {
  try {
    const res = await fetch(`/api/profiles/${profileId}/dashboard`);
    const data = await res.json();

    renderActiveProfileHeader(data.profile);
    renderStats(data.stats);

    rawCards = data.cards || [];
    currentCategories = data.categories || [];
    renderCategoryTabs(currentCategories);
    applyFiltersAndRender();
  } catch (err) {
    console.error("Error loading dashboard:", err);
  }
}

function renderCategoryTabs(categories) {
  const container = document.getElementById("category-tabs-scroll");
  if (!container) return;

  const totalAbnormal = rawCards.filter((c) => ["HIGH", "LOW", "BORDERLINE"].includes(c.latest_flag)).length;

  let html = `
    <button class="category-tab ${currentCategory === 'all' ? 'active' : ''}" data-category="all" onclick="selectCategory('all')">
      <span class="category-tab-icon">🧬</span>
      <span class="category-tab-name">All Panels</span>
      <span class="category-tab-count">${rawCards.length}</span>
      ${totalAbnormal > 0 ? `<span class="category-tab-alert">⚠️ ${totalAbnormal}</span>` : ''}
    </button>
  `;

  (categories || []).forEach((cat) => {
    const icon = CATEGORY_ICONS[cat.name] || "📋";
    const isActive = currentCategory === cat.name ? "active" : "";
    html += `
      <button class="category-tab ${isActive}" data-category="${escapeHtml(cat.name)}" onclick="selectCategory('${escapeHtml(cat.name)}')">
        <span class="category-tab-icon">${icon}</span>
        <span class="category-tab-name">${escapeHtml(cat.name)}</span>
        <span class="category-tab-count">${cat.count}</span>
        ${cat.abnormal_count > 0 ? `<span class="category-tab-alert">⚠️ ${cat.abnormal_count}</span>` : ''}
      </button>
    `;
  });

  container.innerHTML = html;
}

function selectCategory(catName) {
  currentCategory = catName;
  document.querySelectorAll(".category-tab").forEach((btn) => {
    if (btn.dataset.category === catName) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });
  applyFiltersAndRender();
}

function renderActiveProfileHeader(p) {
  document.getElementById("active-profile-name").textContent = p.name;
  document.getElementById("active-profile-age-gender").textContent = `${p.age} Years • ${p.gender}`;
  document.getElementById("active-profile-avatar").textContent = p.name.charAt(0).toUpperCase();

  const issuesEl = document.getElementById("active-profile-issues");
  if (p.health_issues && p.health_issues.trim()) {
    issuesEl.textContent = `Monitored conditions: ${p.health_issues}`;
    issuesEl.style.display = "block";
  } else {
    issuesEl.style.display = "none";
  }
}

function renderStats(stats) {
  document.getElementById("stat-unique-tests").textContent = stats.unique_tests;
  document.getElementById("stat-total-readings").textContent = stats.total_readings;
  document.getElementById("stat-abnormal-flags").textContent = stats.abnormal_flags;
  document.getElementById("stat-last-checkup").textContent = stats.last_checkup ? formatDate(stats.last_checkup) : "No records";
}

function applyFiltersAndRender() {
  // 1. Clear previous sparkline Chart.js instances
  Object.values(sparklineCharts).forEach((c) => {
    try {
      c.destroy();
    } catch (e) {}
  });
  sparklineCharts = {};

  // 2. Update status counts on filter buttons based on active category
  const categorySubset = currentCategory === "all"
    ? rawCards
    : rawCards.filter((c) => c.category === currentCategory);

  const countAll = categorySubset.length;
  const countAbnormal = categorySubset.filter((c) => ["HIGH", "LOW", "BORDERLINE"].includes(c.latest_flag)).length;
  const countNormal = categorySubset.filter((c) => c.latest_flag === "NORMAL").length;
  const countFrequent = categorySubset.filter((c) => c.last_5_records && c.last_5_records.length > 1).length;

  const countAllEl = document.getElementById("count-all");
  const countAbnormalEl = document.getElementById("count-abnormal");
  const countNormalEl = document.getElementById("count-normal");
  const countFrequentEl = document.getElementById("count-frequent");
  
  if (countAllEl) countAllEl.textContent = countAll;
  if (countAbnormalEl) countAbnormalEl.textContent = countAbnormal;
  if (countNormalEl) countNormalEl.textContent = countNormal;
  if (countFrequentEl) countFrequentEl.textContent = countFrequent;

  // 3. Filter rawCards
  let filtered = [...rawCards];

  // Category filter
  if (currentCategory !== "all") {
    filtered = filtered.filter((c) => c.category === currentCategory);
  }

  // Search filter
  if (searchQuery.trim() !== "") {
    const q = searchQuery.toLowerCase().trim();
    filtered = filtered.filter((c) => {
      const nameMatch = c.test_name && c.test_name.toLowerCase().includes(q);
      const catMatch = c.category && c.category.toLowerCase().includes(q);
      const unitMatch = c.unit && c.unit.toLowerCase().includes(q);
      const refMatch = c.reference_range && c.reference_range.toLowerCase().includes(q);
      return nameMatch || catMatch || unitMatch || refMatch;
    });
  }

  // Status filter
  if (currentFilter === "abnormal") {
    filtered = filtered.filter((c) => ["HIGH", "LOW", "BORDERLINE"].includes(c.latest_flag));
  } else if (currentFilter === "normal") {
    filtered = filtered.filter((c) => c.latest_flag === "NORMAL");
  } else if (currentFilter === "frequent") {
    filtered = filtered.filter((c) => c.last_5_records && c.last_5_records.length > 1);
  }

  // 4. Sort
  filtered.sort((a, b) => {
    // Primary sort: Group by Category when in 'all' view
    if (currentCategory === "all") {
      const catA = a.category || "General / Other";
      const catB = b.category || "General / Other";
      if (catA !== catB) return catA.localeCompare(catB);
    }

    // Secondary sort: User's preference within the group/category
    if (currentSort === "abnormal_first") {
      const aAb = ["HIGH", "LOW", "BORDERLINE"].includes(a.latest_flag) ? 1 : 0;
      const bAb = ["HIGH", "LOW", "BORDERLINE"].includes(b.latest_flag) ? 1 : 0;
      if (aAb !== bAb) return bAb - aAb;
      return (b.latest_date || "").localeCompare(a.latest_date || "");
    } else if (currentSort === "name_asc") {
      return a.test_name.localeCompare(b.test_name);
    } else if (currentSort === "name_desc") {
      return b.test_name.localeCompare(a.test_name);
    } else {
      // 'recent'
      return (b.latest_date || "").localeCompare(a.latest_date || "");
    }
  });

  // 5. Update container layout class
  const container = document.getElementById("tests-grid");
  if (currentViewMode === "linear") {
    container.className = "tests-linear-container";
  } else {
    container.className = "tests-grid";
  }

  // 6. Update view toggle buttons active state
  const btnGrid = document.getElementById("btn-view-grid");
  const btnLinear = document.getElementById("btn-view-linear");
  if (btnGrid && btnLinear) {
    btnGrid.classList.toggle("active", currentViewMode === "grid");
    btnLinear.classList.toggle("active", currentViewMode === "linear");
  }

  // 7. Render cards or rows
  container.innerHTML = "";
  
  // Trigger CSS reflow to restart fade-in animation
  container.classList.remove("fade-in");
  void container.offsetWidth;
  container.classList.add("fade-in");

  if (filtered.length === 0) {
    if (rawCards.length === 0) {
      container.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
          <div class="empty-state-icon">📋</div>
          <h3>No Medical Tests Recorded Yet</h3>
          <p>Upload a lab report PDF or image to extract test results automatically, or enter a test manually.</p>
          <button class="btn btn-primary" onclick="openUploadModal()" style="margin-top: 1rem;">Upload First Report</button>
        </div>
      `;
    } else {
      container.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1; padding: 2.5rem 1.5rem;">
          <div class="empty-state-icon">🔍</div>
          <h3>No Tests Match Your Filter</h3>
          <p>Try clearing your search query or selecting a different panel or status filter.</p>
          <button class="btn btn-secondary btn-sm" onclick="resetFilters()" style="margin-top: 0.8rem;">Reset All Filters</button>
        </div>
      `;
    }
    return;
  }

  let lastRenderedCategory = null;

  filtered.forEach((t, idx) => {
    // Determine if this item should be hidden due to collapsed category
    const cat = t.category || "General / Other";
    const isHidden = (currentCategory === "all" && !expandedCategories.has(cat));

    // Inject Category Header if in "all" view
    if (currentCategory === "all") {
      if (cat !== lastRenderedCategory) {
        lastRenderedCategory = cat;
        const header = document.createElement("div");
        const isCollapsed = !expandedCategories.has(cat);
        header.className = `category-group-header ${isCollapsed ? 'collapsed' : ''}`;
        header.style.cursor = "pointer";
        
        const icon = CATEGORY_ICONS[cat] || "📋";
        header.innerHTML = `
          <span style="display: flex; align-items: center; gap: 0.5rem; flex-grow: 1;">
            <span>${icon}</span> 
            <span>${escapeHtml(cat)}</span>
          </span>
          <span class="collapse-icon" style="transition: transform 0.2s; font-size: 0.8rem; opacity: 0.7; transform: ${isCollapsed ? 'rotate(-90deg)' : 'rotate(0)'};">
            ▼
          </span>
        `;
        
        header.addEventListener("click", () => {
          if (expandedCategories.has(cat)) {
            expandedCategories.delete(cat);
          } else {
            expandedCategories.add(cat);
          }
          // Save scroll position to prevent jumping
          const scrollPos = window.scrollY || document.documentElement.scrollTop;
          // Re-render to apply the display logic properly
          applyFiltersAndRender();
          // Restore scroll position
          window.scrollTo(0, scrollPos);
        });
        
        container.appendChild(header);
      }
    }

    // Flag pill
    let pillClass = "pill-normal";
    if (t.latest_flag === "HIGH") pillClass = "pill-high";
    else if (t.latest_flag === "LOW") pillClass = "pill-low";
    else if (t.latest_flag === "BORDERLINE") pillClass = "pill-borderline";

    // Trend badge
    let trendClass = "trend-stable";
    let trendIcon = "•";
    let trendText = "Stable";

    if (t.trend_direction === "up") {
      trendClass = "trend-up";
      trendIcon = "↑";
      trendText = `${trendIcon} ${t.change_str}`;
    } else if (t.trend_direction === "down") {
      trendClass = "trend-down";
      trendIcon = "↓";
      trendText = `${trendIcon} ${t.change_str}`;
    }

    // Last 5 history pills
    let historyPillsHtml = "";
    if (t.last_5_records && t.last_5_records.length > 0) {
      historyPillsHtml = t.last_5_records
        .map(
          (h) => `
          <div class="history-chip">
            <span class="chip-val">${escapeHtml(h.value_str || String(h.value))}</span>
            <span class="chip-date">${formatShortDate(h.test_date)}</span>
          </div>
        `
        )
        .join("");
    }

    const canvasId = `sparkline-${idx}`;

    if (currentViewMode === "linear") {
      // --- LINEAR VIEW ---
      const row = document.createElement("div");
      row.className = "test-linear-row";
      if (isHidden) row.style.display = "none";
      
      row.innerHTML = `
        <div class="linear-col-info">
          <div style="display: flex; align-items: center; gap: 0.4rem; margin-bottom: 3px;">
            <span class="category-micro-tag">${escapeHtml(t.category || "General")}</span>
          </div>
          <div class="linear-test-name">${t.test_name}</div>
          <div class="linear-test-unit">${t.unit ? t.unit : ""} • Ref: ${t.reference_range || "N/A"}</div>
          <div style="font-size: 0.72rem; color: var(--text-dim); margin-top: 2px;">Tested: ${t.latest_date ? formatDate(t.latest_date) : "N/A"}</div>
        </div>

        <div class="linear-col-reading">
          <div class="linear-reading-val">${escapeHtml(t.latest_value_str || (t.latest_value !== null ? String(t.latest_value) : "--"))}</div>
          <div style="display: flex; flex-direction: column; gap: 0.2rem;">
            <span class="pill ${pillClass}">${t.latest_flag}</span>
            <span class="reading-trend-badge ${trendClass}">${trendText}</span>
          </div>
        </div>

        <div class="linear-col-sparkline">
          <canvas id="${canvasId}"></canvas>
        </div>

        <div class="linear-col-history">
          <div class="linear-history-label">Last 5 Readings</div>
          <div class="linear-history-chips">
            ${historyPillsHtml}
          </div>
        </div>

        <div class="linear-col-action">
          <button class="btn-card-action" onclick="openTestDetailModal('${escapeHtml(t.test_name)}')">
            View History →
          </button>
        </div>
      `;
      container.appendChild(row);
    } else {
      // --- GRID VIEW ---
      const card = document.createElement("div");
      card.className = "test-card";
      if (isHidden) card.style.display = "none";
      
      card.innerHTML = `
        <div>
          <div class="test-card-top">
            <div>
              <div style="display: flex; align-items: center; gap: 0.4rem; margin-bottom: 3px;">
                <span class="category-micro-tag">${escapeHtml(t.category || "General")}</span>
              </div>
              <div class="test-name">${t.test_name}</div>
              <div class="test-unit">${t.unit ? t.unit : ""} • Ref: ${t.reference_range || "N/A"}</div>
            </div>
            <span class="pill ${pillClass}">${t.latest_flag}</span>
          </div>

          <div class="reading-showcase">
            <div class="reading-val">${escapeHtml(t.latest_value_str || (t.latest_value !== null ? String(t.latest_value) : "--"))}</div>
            <div class="reading-trend-badge ${trendClass}">${trendText}</div>
          </div>

          <div class="reading-meta">
            Last tested: <strong>${t.latest_date ? formatDate(t.latest_date) : "N/A"}</strong>
          </div>

          <!-- Mini Sparkline Chart -->
          <div class="sparkline-container">
            <canvas id="${canvasId}"></canvas>
          </div>

          <!-- Last 5 History Strip (1mg Style) -->
          <div class="history-strip">
            <div class="history-strip-title">Recent 5 Readings History</div>
            <div class="history-pills">
              ${historyPillsHtml}
            </div>
          </div>
        </div>

        <div class="test-card-footer">
          <button class="btn-card-action" onclick="openTestDetailModal('${t.test_name}')">
            View Detailed Trend & Full History →
          </button>
        </div>
      `;
      container.appendChild(card);
    }

    // Render Canvas Sparkline
    setTimeout(() => {
      renderSparkline(canvasId, t.last_5_records, t.latest_flag);
    }, 15);
  });
}

function resetFilters() {
  searchQuery = "";
  currentFilter = "all";
  currentSort = "recent";
  const searchInput = document.getElementById("test-search-input");
  const clearBtn = document.getElementById("search-clear-btn");
  const sortSelect = document.getElementById("test-sort-select");
  if (searchInput) searchInput.value = "";
  if (clearBtn) clearBtn.style.display = "none";
  if (sortSelect) sortSelect.value = "recent";

  document.querySelectorAll(".filter-pill").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.filter === "all");
  });

  applyFiltersAndRender();
}


function renderSparkline(canvasId, records, flag) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !records || records.length === 0) return;

  const labels = records.map((r) => formatShortDate(r.test_date));
  const values = records.map((r) => r.value);

  // Line color matching clinical flag
  let color = "#10b981"; // green
  let bgGradient = "rgba(16, 185, 129, 0.15)";
  if (flag === "HIGH") {
    color = "#ef4444";
    bgGradient = "rgba(239, 68, 68, 0.15)";
  } else if (flag === "LOW" || flag === "BORDERLINE") {
    color = "#f59e0b";
    bgGradient = "rgba(245, 158, 11, 0.15)";
  }

  if (typeof Chart !== "undefined") {
    const ctx = canvas.getContext("2d");
    sparklineCharts[canvasId] = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            data: values,
            borderColor: color,
            borderWidth: 2.5,
            pointBackgroundColor: color,
            pointRadius: values.length === 1 ? 4 : 3,
            fill: true,
            backgroundColor: bgGradient,
            tension: 0.35,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              title: (ctx) => `Date: ${labels[ctx[0].dataIndex]}`,
              label: (ctx) => `Value: ${ctx.parsed.y}`,
            },
          },
        },
        scales: {
          x: { display: false },
          y: {
            display: false,
            // Add padding so curve doesn't clip
            suggestedMin: Math.min(...values) * 0.95,
            suggestedMax: Math.max(...values) * 1.05,
          },
        },
      },
    });
  }
}

// --- Detailed Test History Modal with Chart.js ---
async function openTestDetailModal(testName) {
  try {
    const res = await fetch(`/api/profiles/${activeProfileId}/test-detail?test_name=${encodeURIComponent(testName)}`);
    const data = await res.json();

    document.getElementById("detail-test-name").textContent = data.test_name;
    const records = data.records;

    if (!records || records.length === 0) return;

    const unit = records[0].unit || "";
    const refRange = records[0].reference_range || "N/A";
    document.getElementById("detail-test-meta").textContent = `Unit: ${unit} | Physiological Reference: ${refRange}`;

    // Render Table
    const tbody = document.getElementById("detail-table-body");
    tbody.innerHTML = "";

    records
      .slice()
      .reverse()
      .forEach((r, idx, arr) => {
        let changeText = "--";
        if (idx < arr.length - 1) {
          const prev = arr[idx + 1].value;
          const diff = r.value - prev;
          if (diff > 0) changeText = `<span style="color:#f87171;">+${diff.toFixed(2)} ↑</span>`;
          else if (diff < 0) changeText = `<span style="color:#34d399;">${diff.toFixed(2)} ↓</span>`;
          else changeText = `<span style="color:#94a3b8;">0.00 •</span>`;
        }

        let flagPill = `<span class="pill pill-normal">Normal</span>`;
        if (r.flag === "HIGH") flagPill = `<span class="pill pill-high">High</span>`;
        else if (r.flag === "LOW") flagPill = `<span class="pill pill-low">Low</span>`;
        else if (r.flag === "BORDERLINE") flagPill = `<span class="pill pill-borderline">Borderline</span>`;

        const tr = document.createElement("tr");
        tr.innerHTML = `
        <td><strong>${formatDate(r.test_date)}</strong></td>
        <td><span style="font-size: 1.1rem; font-weight:700;">${escapeHtml(r.value_str || String(r.value))}</span> ${unit}</td>
        <td>${changeText}</td>
        <td>${flagPill}</td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="deleteRecord(${r.id}, '${testName}')" title="Delete entry">🗑️</button>
        </td>
      `;
        tbody.appendChild(tr);
      });

    // Render Detailed Chart
    renderDetailedChart(records, testName, unit);

    openModal("test-detail-modal");
  } catch (err) {
    console.error("Failed to load test details:", err);
  }
}

function renderDetailedChart(records, testName, unit) {
  const canvas = document.getElementById("detail-chart-canvas");
  if (!canvas) return;

  if (detailedChartInstance) {
    detailedChartInstance.destroy();
  }

  const labels = records.map((r) => formatDate(r.test_date));
  const values = records.map((r) => r.value);

  const ctx = canvas.getContext("2d");
  detailedChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: `${testName} (${unit})`,
          data: values,
          borderColor: "#0284c7",
          backgroundColor: "rgba(2, 132, 199, 0.15)",
          fill: true,
          tension: 0.3,
          borderWidth: 3,
          pointRadius: 6,
          pointHoverRadius: 8,
          pointBackgroundColor: "#38bdf8",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: { color: "rgba(255, 255, 255, 0.06)" },
          ticks: { color: "#9ca3af" },
        },
        y: {
          grid: { color: "rgba(255, 255, 255, 0.06)" },
          ticks: { color: "#9ca3af" },
        },
      },
      plugins: {
        legend: {
          labels: { color: "#f3f4f6" },
        },
        tooltip: {
          callbacks: {
            label: (ctx) => `Reading: ${ctx.parsed.y} ${unit}`,
          },
        },
      },
    },
  });
}

async function deleteRecord(recordId, testName) {
  if (!confirm("Are you sure you want to delete this specific test reading?")) return;
  try {
    const res = await fetch(`/api/records/${recordId}`, { method: "DELETE" });
    if (res.ok) {
      openTestDetailModal(testName);
      loadDashboard(activeProfileId);
    }
  } catch (err) {
    alert("Error deleting record: " + err);
  }
}

// --- Upload & OCR Extraction Pipeline ---
function openUploadModal() {
  detectedOcrPayload = null;
  document.getElementById("ocr-step-upload").style.display = "block";
  document.getElementById("ocr-step-verify").style.display = "none";
  document.getElementById("upload-file-input").value = "";
  document.getElementById("upload-spinner").style.display = "none";
  openModal("upload-modal");
}

async function handleFileSelect(file) {
  if (!file) return;

  const spinner = document.getElementById("upload-spinner");
  const uploadStep = document.getElementById("ocr-step-upload");
  spinner.style.display = "block";

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch(`/api/profiles/${activeProfileId}/upload`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) throw new Error("Server error processing report");

    detectedOcrPayload = await res.json();
    spinner.style.display = "none";
    uploadStep.style.display = "none";
    showVerificationStep(detectedOcrPayload);
  } catch (err) {
    spinner.style.display = "none";
    alert("Extraction error: " + err.message);
  }
}

function showVerificationStep(payload) {
  const verifyStep = document.getElementById("ocr-step-verify");
  verifyStep.style.display = "block";

  document.getElementById("ocr-filename").textContent = payload.filename;
  document.getElementById("ocr-test-date").value = payload.extracted_date || new Date().toISOString().split("T")[0];

  const tbody = document.getElementById("ocr-verification-body");
  tbody.innerHTML = "";

  const tests = payload.detected_tests || [];
  if (tests.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:1.5rem; color:#9ca3af;">No standard tests automatically detected. You can add tests manually below.</td></tr>`;
  } else {
    tests.forEach((t) => {
      addVerificationRow(t.test_name, t.value, t.unit, t.reference_range, t.flag, t.value_str, t.panel, t.category);
    });
  }

  updateVerificationStats();
}

function addVerificationRow(name = "", val = "", unit = "", ref = "", flag = "NORMAL", valStr = "", panel = "", category = "") {
  const tbody = document.getElementById("ocr-verification-body");
  const tr = document.createElement("tr");
  tr.dataset.flag = flag || "NORMAL";
  tr.dataset.category = category || "";
  const displayPanel = panel || "General / Other";

  tr.innerHTML = `
    <td><input type="text" class="table-input row-name" value="${escapeHtml(name)}" placeholder="Test Name" oninput="updateVerificationStats()" /></td>
    <td><input type="text" class="table-input row-panel" value="${escapeHtml(displayPanel)}" placeholder="Panel" style="width:160px;" oninput="updateVerificationStats()" /></td>
    <td><input type="text" class="table-input row-value" value="${escapeHtml(String(valStr || val))}" placeholder="Value" style="width:110px;" /></td>
    <td><input type="text" class="table-input row-unit" value="${escapeHtml(unit)}" placeholder="Unit" style="width:80px;" /></td>
    <td><input type="text" class="table-input row-ref" value="${escapeHtml(ref)}" placeholder="Ref Range" /></td>
    <td style="text-align:center;">
      <button type="button" class="btn btn-secondary btn-sm" onclick="removeVerificationRow(this)" title="Remove row">✕</button>
    </td>
  `;
  tbody.appendChild(tr);
  updateVerificationStats();
}

function removeVerificationRow(btn) {
  const tr = btn.closest("tr");
  if (tr) {
    tr.remove();
    updateVerificationStats();
  }
}

function updateVerificationStats() {
  const rows = document.querySelectorAll("#ocr-verification-body tr");
  const distinctPanels = new Set();
  let paramCount = 0;

  rows.forEach((tr) => {
    const nameInput = tr.querySelector(".row-name");
    const panelInput = tr.querySelector(".row-panel");
    if (nameInput && nameInput.value.trim() !== "") {
      paramCount++;
      const panelName = panelInput && panelInput.value.trim() ? panelInput.value.trim() : "General / Other";
      distinctPanels.add(panelName);
    }
  });

  const panelCountEl = document.getElementById("ocr-panel-count");
  const paramCountEl = document.getElementById("ocr-param-count");
  if (panelCountEl) panelCountEl.textContent = distinctPanels.size;
  if (paramCountEl) paramCountEl.textContent = paramCount;
}

async function confirmAndSaveReport() {
  if (!detectedOcrPayload && !activeProfileId) return;

  const testDate = document.getElementById("ocr-test-date").value;
  if (!testDate) {
    alert("Please specify the test collection date.");
    return;
  }

  const rows = document.querySelectorAll("#ocr-verification-body tr");
  const records = [];

  rows.forEach((tr) => {
    const nameEl = tr.querySelector(".row-name");
    const panelEl = tr.querySelector(".row-panel");
    const valEl = tr.querySelector(".row-value");
    const unitEl = tr.querySelector(".row-unit");
    const refEl = tr.querySelector(".row-ref");

    if (nameEl && valEl && valEl.value.trim() !== "") {
      const rawVal = valEl.value.trim();
      let numVal = parseFloat(rawVal.replace(/[^0-9.-]/g, ""));
      if (isNaN(numVal)) {
        numVal = 0.0;
      }
      records.push({
        test_name: nameEl.value.trim(),
        panel: panelEl ? panelEl.value.trim() : "General / Other",
        category: tr.dataset.category || "",
        value: numVal,
        value_str: rawVal,
        unit: unitEl ? unitEl.value.trim() : "",
        reference_range: refEl ? refEl.value.trim() : "",
        flag: tr.dataset.flag || "NORMAL",
      });
    }
  });

  if (records.length === 0) {
    alert("No valid test records to save. Please enter at least one test name and numeric value.");
    return;
  }

  const payload = {
    test_date: testDate,
    filename: detectedOcrPayload ? detectedOcrPayload.filename : "Manual Entry",
    file_path: detectedOcrPayload ? detectedOcrPayload.file_path : "",
    records: records,
  };

  try {
    const res = await fetch(`/api/profiles/${activeProfileId}/confirm`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (res.ok) {
      closeModal("upload-modal");
      loadDashboard(activeProfileId);
    } else {
      const err = await res.json();
      alert("Save failed: " + err.detail);
    }
  } catch (err) {
    alert("Failed to save records: " + err.message);
  }
}

// --- Profile Creation Modal ---
function openNewProfileModal() {
  document.getElementById("new-profile-form").reset();
  openModal("profile-modal");
}

async function handleProfileSubmit(e) {
  e.preventDefault();
  const name = document.getElementById("profile-name-input").value.trim();
  const age = parseInt(document.getElementById("profile-age-input").value);
  const gender = document.getElementById("profile-gender-input").value;
  const health_issues = document.getElementById("profile-issues-input").value.trim();

  if (!name || isNaN(age)) return;

  try {
    const res = await fetch("/api/profiles", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, age, gender, health_issues }),
    });

    if (res.ok) {
      const created = await res.json();
      closeModal("profile-modal");
      loadProfiles(created.id);
    }
  } catch (err) {
    alert("Failed to create profile: " + err);
  }
}

// --- Data Export to CSV ---
function exportActiveProfileCsv() {
  if (!activeProfileId) return;
  window.location.href = `/api/profiles/${activeProfileId}/export-csv`;
}

function resetFilters() {
  currentCategory = "all";
  currentFilter = "all";
  searchQuery = "";
  const searchInput = document.getElementById("test-search-input");
  if (searchInput) searchInput.value = "";
  const clearBtn = document.getElementById("search-clear-btn");
  if (clearBtn) clearBtn.style.display = "none";
  document.querySelectorAll(".filter-pill").forEach((b) => {
    b.classList.toggle("active", b.dataset.filter === "all");
  });
  renderCategoryTabs(currentCategories);
  applyFiltersAndRender();
}

// --- Event Listeners Setup ---
function setupEventListeners() {
  // Profile selector change
  document.getElementById("profile-select").addEventListener("change", (e) => {
    switchProfile(e.target.value);
  });

  // Profile modal submit
  document.getElementById("new-profile-form").addEventListener("submit", handleProfileSubmit);

  // View mode toggle buttons (Grid vs Linear)
  const btnGrid = document.getElementById("btn-view-grid");
  const btnLinear = document.getElementById("btn-view-linear");
  if (btnGrid) {
    btnGrid.addEventListener("click", () => {
      currentViewMode = "grid";
      localStorage.setItem("health_tracker_view_mode", "grid");
      applyFiltersAndRender();
    });
  }
  if (btnLinear) {
    btnLinear.addEventListener("click", () => {
      currentViewMode = "linear";
      localStorage.setItem("health_tracker_view_mode", "linear");
      applyFiltersAndRender();
    });
  }

  // Search input & clear button
  const searchInput = document.getElementById("test-search-input");
  const clearBtn = document.getElementById("search-clear-btn");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      searchQuery = e.target.value;
      if (clearBtn) {
        clearBtn.style.display = searchQuery.trim() ? "block" : "none";
      }
      applyFiltersAndRender();
    });
  }
  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      if (searchInput) searchInput.value = "";
      searchQuery = "";
      clearBtn.style.display = "none";
      applyFiltersAndRender();
    });
  }

  // Filter pills (All, Attention Needed, Normal)
  document.querySelectorAll(".filter-pill").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".filter-pill").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentFilter = btn.dataset.filter;
      applyFiltersAndRender();
    });
  });

  // Sort dropdown
  const sortSelect = document.getElementById("test-sort-select");
  if (sortSelect) {
    sortSelect.addEventListener("change", (e) => {
      currentSort = e.target.value;
      applyFiltersAndRender();
    });
  }

  // Drag and drop zone
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("upload-file-input");

  if (dropzone && fileInput) {
    dropzone.addEventListener("click", () => fileInput.click());
    dropzone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });
    dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
    dropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        handleFileSelect(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
      }
    });
  }
}

// --- Utility Helpers ---
function openModal(modalId) {
  document.getElementById(modalId).classList.add("active");
}

function closeModal(modalId) {
  document.getElementById(modalId).classList.remove("active");
}

function formatDate(dateStr) {
  if (!dateStr) return "";
  const parts = dateStr.split("-");
  if (parts.length === 3) {
    const d = new Date(parts[0], parts[1] - 1, parts[2]);
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  }
  return dateStr;
}

function formatShortDate(dateStr) {
  if (!dateStr) return "";
  const parts = dateStr.split("-");
  if (parts.length === 3) {
    const d = new Date(parts[0], parts[1] - 1, parts[2]);
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  }
  return dateStr;
}

function escapeHtml(text) {
  if (!text) return "";
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}


/* ========================================= 
   AI CHATBOT LOGIC 
========================================= */

function toggleChatWidget() {
  const widget = document.getElementById('chat-widget');
  widget.classList.toggle('active');
}

document.getElementById('ai-provider')?.addEventListener('change', (e) => {
  if (e.target.value === 'gemini') {
    document.getElementById('ai-gemini-config').style.display = 'block';
    document.getElementById('ai-local-config').style.display = 'none';
  } else {
    document.getElementById('ai-gemini-config').style.display = 'none';
    document.getElementById('ai-local-config').style.display = 'block';
  }
});

const RETIRED_GEMINI_MODELS = {
  'gemini-2.5-flash-lite': 'gemini-3.5-flash-lite',
  'gemini-2.0-flash': 'gemini-3.5-flash',
  'gemini-2.0-flash-001': 'gemini-3.5-flash',
  'gemini-2.0-flash-lite': 'gemini-3.5-flash-lite',
  'gemini-1.5-flash': 'gemini-3.5-flash',
  'gemini-1.5-pro': 'gemini-3.5-flash'
};

function getAIConfig() {
  const saved = localStorage.getItem('health_tracker_ai_config');
  let config = saved ? JSON.parse(saved) : {
    provider: 'local',
    localUrl: 'http://localhost:11434',
    localModel: 'phi3:3.8b',
    geminiModel: 'gemini-3.5-flash',
    geminiKey: ''
  };
  
  if (config.geminiModel && RETIRED_GEMINI_MODELS[config.geminiModel]) {
    config.geminiModel = RETIRED_GEMINI_MODELS[config.geminiModel];
    localStorage.setItem('health_tracker_ai_config', JSON.stringify(config));
  }
  if (!config.geminiModel) {
    config.geminiModel = 'gemini-3.5-flash';
  }
  return config;
}

document.getElementById('ai-settings-form')?.addEventListener('submit', (e) => {
  e.preventDefault();
  let modelVal = document.getElementById('ai-gemini-model')?.value || 'gemini-3.5-flash';
  if (RETIRED_GEMINI_MODELS[modelVal]) {
    modelVal = RETIRED_GEMINI_MODELS[modelVal];
  }
  const config = {
    provider: document.getElementById('ai-provider').value,
    geminiKey: document.getElementById('ai-gemini-key').value.trim(),
    geminiModel: modelVal,
    localUrl: document.getElementById('ai-local-url').value.trim() || 'http://localhost:11434',
    localModel: document.getElementById('ai-local-model').value.trim() || 'phi3:3.8b'
  };
  localStorage.setItem('health_tracker_ai_config', JSON.stringify(config));
  closeModal('ai-settings-modal');
  alert('AI Settings Saved Successfully');
});

// Load settings when modal opens
const originalOpenModal = window.openModal;
window.openModal = function(id) {
  if (id === 'ai-settings-modal') {
    const config = getAIConfig();
    document.getElementById('ai-provider').value = config.provider || 'local';
    document.getElementById('ai-gemini-key').value = config.geminiKey || '';
    if (document.getElementById('ai-gemini-model')) {
      document.getElementById('ai-gemini-model').value = config.geminiModel || 'gemini-3.5-flash';
    }
    document.getElementById('ai-local-url').value = config.localUrl || 'http://localhost:11434';
    document.getElementById('ai-local-model').value = config.localModel || 'phi3:3.8b';
    document.getElementById('ai-provider').dispatchEvent(new Event('change'));
  }
  originalOpenModal(id);
};

let chatMessagesHistory = [];

async function sendChatMessage() {
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if (!text) return;
  
  if (!activeProfileId) {
    alert('Please select a profile first.');
    return;
  }

  const msgContainer = document.getElementById('chat-messages');
  const sendBtn = document.querySelector('.chat-send-btn');
  const statusLabel = document.getElementById('chat-status');

  // Append User message
  const userDiv = document.createElement('div');
  userDiv.className = 'chat-message user-message';
  userDiv.textContent = text;
  msgContainer.appendChild(userDiv);
  
  chatMessagesHistory.push({role: 'user', content: text});
  input.value = '';
  msgContainer.scrollTop = msgContainer.scrollHeight;

  // Add AI thinking placeholder with animations
  const aiDiv = document.createElement('div');
  aiDiv.className = 'chat-message ai-message ai-thinking';
  aiDiv.innerHTML = `
    <div class="ai-thinking-container">
      <div class="ai-pulse-orb"></div>
      <span class="ai-thinking-text">Analyzing records &amp; trends...</span>
      <div class="ai-typing-dots">
        <span></span><span></span><span></span>
      </div>
    </div>
  `;
  msgContainer.appendChild(aiDiv);
  msgContainer.scrollTop = msgContainer.scrollHeight;

  input.disabled = true;
  sendBtn.disabled = true;
  statusLabel.innerHTML = '<span class="status-pulse-dot working"></span>Analyzing...';

  const config = getAIConfig();

  try {
    const response = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        messages: chatMessagesHistory,
        provider: config.provider,
        api_key: config.geminiKey || null,
        gemini_model: (config.geminiModel || 'gemini-3.5-flash').trim(),
        local_url: (config.localUrl || 'http://localhost:11434').trim(),
        local_model: (config.localModel || 'phi3:3.8b').trim(),
        profile_id: activeProfileId
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Network error');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let aiResponseText = '';
    let sseBuffer = '';
    let hasReceivedFirstToken = false;

    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      sseBuffer += decoder.decode(value, {stream: true});
      
      const lines = sseBuffer.split('\n');
      sseBuffer = lines.pop() || ''; // Keep partial trailing line in buffer
      
      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith('data: ')) {
          const dataStr = trimmed.slice(6).trim();
          if (!dataStr) continue;
          if (dataStr.startsWith('[ERROR]')) {
            aiDiv.classList.remove('ai-thinking');
            aiDiv.innerHTML = `<span style="color: var(--danger, #ef4444); font-weight: 500;">${dataStr}</span>`;
            aiResponseText += dataStr;
          } else {
            try {
              const data = JSON.parse(dataStr);
              if (data.content) {
                if (!hasReceivedFirstToken) {
                  aiDiv.classList.remove('ai-thinking');
                  aiDiv.textContent = '';
                  hasReceivedFirstToken = true;
                }
                statusLabel.innerHTML = '<span class="status-pulse-dot working"></span>Responding...';
                aiDiv.textContent += data.content;
                aiResponseText += data.content;
                msgContainer.scrollTop = msgContainer.scrollHeight;
              }
            } catch(e) {
              console.warn('Could not parse SSE JSON chunk:', dataStr, e);
            }
          }
        }
      }
    }
    
    chatMessagesHistory.push({role: 'model', content: aiResponseText});
  } catch(err) {
    aiDiv.classList.remove('ai-thinking');
    aiDiv.innerHTML = `<span style="color: red;">Error: ${err.message}</span>`;
  } finally {
    input.disabled = false;
    sendBtn.disabled = false;
    statusLabel.innerHTML = '<span class="status-pulse-dot"></span>Ready';
    input.focus();
  }
}

// --- Checkups & Data Management ---
async function openManageRecordsModal() {
  if (!activeProfileId) return;
  const profile = currentProfiles.find((p) => p.id === activeProfileId);
  const name = profile ? profile.name : "Active Profile";
  const subEl = document.getElementById("manage-records-subtitle");
  if (subEl) {
    subEl.textContent = `Review checkup history and manage data for ${name}`;
  }
  openModal("manage-records-modal");
  await loadProfileCheckups();
}

async function loadProfileCheckups() {
  const container = document.getElementById("checkups-list-container");
  if (!container) return;
  container.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--text-muted);">Loading checkups...</div>';

  try {
    const res = await fetch(`/api/profiles/${activeProfileId}/checkups`);
    if (!res.ok) throw new Error("Failed to load checkups");
    const checkups = await res.json();

    if (!checkups || checkups.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 2rem; background: var(--bg-card); border-radius: var(--radius-md); border: 1px dashed var(--border-color); color: var(--text-muted);">
          No medical checkup records found for this profile.
        </div>`;
      return;
    }

    let html = `<div style="display: flex; flex-direction: column; gap: 0.75rem;">`;

    checkups.forEach((c) => {
      const formattedDate = new Date(c.test_date + 'T00:00:00').toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
      const fileLabel = c.filename ? `📄 ${escapeHtml(c.filename)}` : "Manual Entry";

      html += `
        <div style="display: flex; justify-content: space-between; align-items: center; background: var(--bg-card); padding: 0.85rem 1.15rem; border-radius: var(--radius-md); border: 1px solid var(--border-color); gap: 1rem; flex-wrap: wrap;">
          <div>
            <div style="font-weight: 600; font-size: 0.95rem; color: var(--text-main); display: flex; align-items: center; gap: 0.5rem;">
              <span>📅 ${formattedDate}</span>
              <span style="font-size: 0.75rem; background: var(--primary-light); color: var(--primary); padding: 0.15rem 0.5rem; border-radius: var(--radius-sm); font-weight: 600;">
                ${c.records_count} tests
              </span>
            </div>
            <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.2rem;">
              Source: ${fileLabel}
            </div>
          </div>
          <button type="button" class="btn btn-danger-outline btn-sm" onclick="deleteCheckupDate('${c.test_date}')" title="Delete all tests recorded on this date">
            🗑️ Delete Checkup
          </button>
        </div>
      `;
    });

    html += `</div>`;
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = `<div style="color: #ef4444; padding: 1rem;">Failed to load checkup history: ${escapeHtml(err.message)}</div>`;
  }
}

async function deleteCheckupDate(testDate) {
  const formattedDate = new Date(testDate + 'T00:00:00').toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
  if (!confirm(`Are you sure you want to delete all medical records and reports for ${formattedDate}? This action cannot be undone.`)) {
    return;
  }

  try {
    const res = await fetch(`/api/profiles/${activeProfileId}/checkups/${testDate}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Failed to delete checkup records");
    
    await loadProfileCheckups();
    loadDashboard(activeProfileId);
  } catch (err) {
    alert("Error deleting checkup: " + err.message);
  }
}

async function clearProfileData() {
  const profile = currentProfiles.find((p) => p.id === activeProfileId);
  const name = profile ? profile.name : "this profile";

  if (!confirm(`⚠️ PERMANENT ACTION:\nAre you sure you want to delete ALL medical records and reports for ${name}?\n\nThe profile persona will remain, but all test history will be cleared to 0.`)) {
    return;
  }

  try {
    const res = await fetch(`/api/profiles/${activeProfileId}/data`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Failed to clear profile data");

    closeModal("manage-records-modal");
    loadDashboard(activeProfileId);
    alert(`All medical records for ${name} have been cleared.`);
  } catch (err) {
    alert("Error clearing data: " + err.message);
  }
}

async function deleteCurrentProfile() {
  const profile = currentProfiles.find((p) => p.id === activeProfileId);
  const name = profile ? profile.name : "this profile";

  if (!confirm(`🚨 DANGER:\nAre you sure you want to completely DELETE profile "${name}" and all its historical lab records?\n\nThis cannot be undone.`)) {
    return;
  }

  try {
    const res = await fetch(`/api/profiles/${activeProfileId}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Failed to delete profile");

    closeModal("manage-records-modal");
    activeProfileId = null;
    await loadProfiles();
  } catch (err) {
    alert("Error deleting profile: " + err.message);
  }
}


