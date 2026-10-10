/* ====== CarScan - Shared JS helpers ====== */

// --- API Wrappers ---
const API = {
  async get(path) {
    const res = await fetch(path);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },
  async del(path) {
    const res = await fetch(path, { method: "DELETE" });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },
};

// --- Colors for each damage class ---
const DAMAGE_COLORS = {
  "crack":         "#4299e1",
  "dent":          "#ed8936",
  "glass shatter": "#e53e3e",
  "lamp broken":   "#9f7aea",
  "scratch":       "#ecc94b",
  "tire flat":     "#4a5568",
};

function getDamageColor(class_name) {
  return DAMAGE_COLORS[class_name] || "#667eea";
}

// --- Formatters ---
function formatDate(iso) {
  try {
    return new Date(iso).toLocaleString("ar-EG", {
      year: "numeric", month: "short", day: "numeric",
      hour: "2-digit", minute: "2-digit",
    });
  } catch { return iso; }
}

function shortId(id) {
  return id ? id.slice(0, 8) : "";
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// --- Download helpers ---
function downloadJson(data, filename) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// --- Bounding boxes on canvas ---
function drawBoundingBoxes(imgEl, canvasEl, detections) {
  const rect = imgEl.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;

  // Set canvas size in device pixels for crisp rendering
  canvasEl.width  = rect.width  * dpr;
  canvasEl.height = rect.height * dpr;
  canvasEl.style.width  = rect.width  + "px";
  canvasEl.style.height = rect.height + "px";

  const ctx = canvasEl.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);   // scale all coordinates by dpr
  ctx.clearRect(0, 0, rect.width, rect.height);

  if (!imgEl.naturalWidth || !detections || !detections.length) return;

  const scaleX = rect.width  / imgEl.naturalWidth;
  const scaleY = rect.height / imgEl.naturalHeight;

  detections.forEach((d) => {
    const [x1, y1, x2, y2] = d.bbox;
    const color = getDamageColor(d.class_name);

    const rx = x1 * scaleX;
    const ry = y1 * scaleY;
    const rw = (x2 - x1) * scaleX;
    const rh = (y2 - y1) * scaleY;

    // Box
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.strokeRect(rx, ry, rw, rh);

    // Label
    const label = `${d.class_name_ar} ${(d.confidence * 100).toFixed(0)}%`;
    ctx.font = "bold 13px Segoe UI, Tahoma, sans-serif";
    const textW = ctx.measureText(label).width + 12;
    const labelY = ry < 24 ? ry + 4 : ry - 22;

    ctx.fillStyle = color;
    ctx.fillRect(rx, labelY, textW, 20);
    ctx.fillStyle = "#fff";
    ctx.fillText(label, rx + 6, labelY + 14);
  });
}