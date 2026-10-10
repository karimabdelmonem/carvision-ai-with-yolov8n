/* ====== CarScan - History page logic ====== */

// ===== State =====
let currentOffset = 0;
const PAGE_SIZE = 10;
let totalScans = 0;

// ===== Elements =====
const listEl       = document.getElementById("historyList");
const loadingEl    = document.getElementById("loading");
const errorEl      = document.getElementById("error");
const emptyEl      = document.getElementById("empty");
const pagination   = document.getElementById("pagination");
const prevBtn      = document.getElementById("prevBtn");
const nextBtn      = document.getElementById("nextBtn");
const pageInfo     = document.getElementById("pageInfo");

// Details modal
const detailsModal    = document.getElementById("detailsModal");
const detailsBody     = document.getElementById("detailsBody");
const closeModalBtn   = document.getElementById("closeModal");
const modalImage      = document.getElementById("modalImage");
const modalCanvas     = document.getElementById("modalCanvas");
const modalTitle      = document.getElementById("modalTitle");

// Delete confirm modal
const confirmModal    = document.getElementById("confirmModal");
const confirmText     = document.getElementById("confirmText");
const confirmDeleteBtn= document.getElementById("confirmDeleteBtn");
const cancelDeleteBtn = document.getElementById("cancelDeleteBtn");

let pendingDeleteId = null;

// ===== Initial load =====
loadPage(0);

// ===== Load page from API =====
async function loadPage(offset) {
  currentOffset = offset;
  loadingEl.classList.add("active");
  errorEl.classList.remove("active");
  listEl.innerHTML = "";
  emptyEl.style.display = "none";
  pagination.style.display = "none";

  try {
    const data = await API.get(`/scans?limit=${PAGE_SIZE}&offset=${offset}`);
    totalScans = data.total;

    if (totalScans === 0) {
      emptyEl.style.display = "block";
      loadingEl.classList.remove("active");
      return;
    }

    renderList(data.items);
    renderPagination();
    loadingEl.classList.remove("active");
    pagination.style.display = "flex";
  } catch (err) {
    loadingEl.classList.remove("active");
    showError(err.message);
  }
}

// ===== Render list =====
function renderList(items) {
  listEl.innerHTML = items.map((s) => {
    const summaryLine = Object.entries(s.summary || {})
      .map(([k, v]) => `${k}: ${v}`)
      .join(" • ") || "بدون تفاصيل";

    const countText = s.damage_count === 0
      ? "✅ نضيفة"
      : `${s.damage_count} ضرر`;

    return `
      <div class="history-item">
        <img class="history-thumb" src="${s.image_url}" alt="scan" loading="lazy" />
        <div class="history-info">
          <div class="count">${countText}</div>
          <div class="date">${formatDate(s.created_at)}</div>
          <div class="summary-line">${escapeHtml(summaryLine)}</div>
        </div>
        <div class="history-actions">
          <button class="btn btn-secondary btn-icon" data-action="details" data-id="${s.scan_id}">
            👁️ تفاصيل
          </button>
          <button class="btn btn-danger btn-icon" data-action="delete" data-id="${s.scan_id}">
            🗑️ حذف
          </button>
        </div>
      </div>
    `;
  }).join("");

  // Attach events via delegation
  listEl.querySelectorAll("[data-action]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.id;
      if (btn.dataset.action === "details") openDetails(id);
      else if (btn.dataset.action === "delete") openDeleteConfirm(id);
    });
  });
}

// ===== Pagination =====
function renderPagination() {
  const start = totalScans === 0 ? 0 : currentOffset + 1;
  const end   = Math.min(currentOffset + PAGE_SIZE, totalScans);
  pageInfo.textContent = `${start} - ${end} من ${totalScans}`;

  prevBtn.disabled = currentOffset === 0;
  nextBtn.disabled = (currentOffset + PAGE_SIZE) >= totalScans;
}

prevBtn.addEventListener("click", () => {
  if (currentOffset > 0) loadPage(Math.max(0, currentOffset - PAGE_SIZE));
});

nextBtn.addEventListener("click", () => {
  if (currentOffset + PAGE_SIZE < totalScans) loadPage(currentOffset + PAGE_SIZE);
});

// ===== Details modal =====
async function openDetails(scanId) {
  detailsModal.classList.add("active");
  detailsBody.innerHTML = `<div class="loading active"><div class="spinner"></div></div>`;
  modalTitle.textContent = `فحص ${shortId(scanId)}`;

  try {
    const data = await API.get(`/scans/${scanId}`);
    renderDetails(data);
  } catch (err) {
    detailsBody.innerHTML = `<div class="error active">❌ ${escapeHtml(err.message)}</div>`;
  }
}

function renderDetails(data) {
  // Image
  modalImage.src = data.image_url;

  // Detections
  let bodyHtml = "";

  if (data.damage_count === 0) {
    bodyHtml += `
      <div class="clean-message" style="margin-top:15px;">
        ✅ العربية نضيفة! مفيش أضرار مكتشفة.
      </div>
    `;
  } else {
    bodyHtml += `<div class="summary-grid" style="margin-top:15px;">`;
    for (const [name, count] of Object.entries(data.summary)) {
      bodyHtml += `
        <div class="summary-card">
          <div class="name">${escapeHtml(name)}</div>
          <div class="count">${count}</div>
        </div>
      `;
    }
    bodyHtml += `</div>`;

    bodyHtml += `<div class="detection-list">`;
    data.detections.forEach((d) => {
      const color = getDamageColor(d.class_name);
      bodyHtml += `
        <div class="detection-item">
          <span>${escapeHtml(d.class_name_ar)}</span>
          <span class="badge" style="background:${color};">
            ${(d.confidence * 100).toFixed(0)}%
          </span>
        </div>
      `;
    });
    bodyHtml += `</div>`;
  }

  bodyHtml += `
    <div class="meta">
      رقم الفحص: ${shortId(data.scan_id)} | ${formatDate(data.created_at)}
    </div>
  `;

  detailsBody.innerHTML = bodyHtml;

  // Draw bboxes after image loads
  modalImage.onload = () => {
    const wrap = modalImage.parentElement;
    const rect = modalImage.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    modalCanvas.width  = rect.width  * dpr;
    modalCanvas.height = rect.height * dpr;
    modalCanvas.style.width  = rect.width  + "px";
    modalCanvas.style.height = rect.height + "px";
    const ctx = modalCanvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    drawBoundingBoxes(modalImage, modalCanvas, data.detections);
  };
}

closeModalBtn.addEventListener("click", () => {
  detailsModal.classList.remove("active");
});

detailsModal.addEventListener("click", (e) => {
  if (e.target === detailsModal) detailsModal.classList.remove("active");
});

// ===== Delete confirm =====
function openDeleteConfirm(scanId) {
  pendingDeleteId = scanId;
  confirmText.textContent = `متأكد إنك عايز تحذف الفحص ${shortId(scanId)}؟`;
  confirmModal.classList.add("active");
}

cancelDeleteBtn.addEventListener("click", () => {
  pendingDeleteId = null;
  confirmModal.classList.remove("active");
});

confirmModal.addEventListener("click", (e) => {
  if (e.target === confirmModal) {
    pendingDeleteId = null;
    confirmModal.classList.remove("active");
  }
});

confirmDeleteBtn.addEventListener("click", async () => {
  if (!pendingDeleteId) return;
  confirmDeleteBtn.disabled = true;

  try {
    await API.del(`/scans/${pendingDeleteId}`);
    confirmModal.classList.remove("active");
    pendingDeleteId = null;
    // Reload current page
    loadPage(currentOffset);
  } catch (err) {
    alert("فشل الحذف: " + err.message);
  } finally {
    confirmDeleteBtn.disabled = false;
  }
});

// ===== Error helper =====
function showError(msg) {
  errorEl.textContent = "❌ " + msg;
  errorEl.classList.add("active");
}

// ===== Auto-open details from URL query (?id=xxx) =====
const urlParams = new URLSearchParams(window.location.search);
const autoId = urlParams.get("id");
if (autoId) {
  openDetails(autoId);
}