/* ====== CarScan - Stats page logic ====== */

const statsContent = document.getElementById("statsContent");
const loadingEl    = document.getElementById("loading");
const errorEl      = document.getElementById("error");

loadStats();

async function loadStats() {
  loadingEl.classList.add("active");
  errorEl.classList.remove("active");

  try {
    const data = await API.get("/scans/stats");
    renderStats(data);
    loadingEl.classList.remove("active");
  } catch (err) {
    loadingEl.classList.remove("active");
    errorEl.textContent = "❌ " + err.message;
    errorEl.classList.add("active");
  }
}

function renderStats(data) {
  if (data.total_scans === 0) {
    statsContent.innerHTML = `
      <div class="empty">
        <div class="icon">📊</div>
        <div>لسه مفيش بيانات كفاية</div>
        <a href="/app/" class="btn btn-primary" style="margin-top:15px; display:inline-block;">
          ابدأ أول فحص
        </a>
      </div>
    `;
    return;
  }

  const mostCommon = data.most_common_damage || "—";

  let html = `
    <div class="stats-grid">
      <div class="stat-card">
        <div class="value">${data.total_scans}</div>
        <div class="label">إجمالي الفحوصات</div>
      </div>
      <div class="stat-card">
        <div class="value">${data.total_damages}</div>
        <div class="label">إجمالي الأضرار</div>
      </div>
      <div class="stat-card">
        <div class="value">${data.scans_with_damage}</div>
        <div class="label">فحوصات فيها أضرار</div>
      </div>
      <div class="stat-card">
        <div class="value">${data.scans_clean}</div>
        <div class="label">فحوصات نضيفة</div>
      </div>
      <div class="stat-card">
        <div class="value">${data.average_damages_per_scan}</div>
        <div class="label">متوسط الأضرار/فحص</div>
      </div>
      <div class="stat-card" style="border-top-color:#ed8936;">
        <div class="value" style="font-size:22px;">${escapeHtml(mostCommon)}</div>
        <div class="label">أكثر عيب متكرر</div>
      </div>
    </div>
  `;

  // Chart
  const breakdown = data.damage_breakdown || {};
  const entries = Object.entries(breakdown);

  if (entries.length > 0) {
    const maxCount = Math.max(...entries.map(([, c]) => c));

    html += `<h2 style="font-size:18px; margin:25px 0 15px;">توزيع الأضرار</h2>`;
    html += `<div class="chart">`;

    entries.sort((a, b) => b[1] - a[1]);
    entries.forEach(([name, count]) => {
      const widthPct = maxCount > 0 ? (count / maxCount) * 100 : 0;
      html += `
        <div class="chart-row">
          <div class="chart-label">${escapeHtml(name)}</div>
          <div class="chart-bar-wrap">
            <div class="chart-bar" style="width:${widthPct}%;"></div>
          </div>
          <div class="chart-value">${count}</div>
        </div>
      `;
    });

    html += `</div>`;
  }

  statsContent.innerHTML = html;
}