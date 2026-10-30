"use strict";
/* ===========================================================
   core.js - helpers, icons, charts, modals, Excel-style grid
   =========================================================== */
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const inr = n => "₹" + Number(n || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 });
const num = n => Number(n).toLocaleString("en-IN", { maximumFractionDigits: 1 });
const initials = n => String(n).replace(/^Dr\.?\s*/i, "").split(/\s+/).slice(0, 2).map(w => w[0]).join("").toUpperCase();
const cssv = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const seriesColors = () => [1, 2, 3, 4, 5, 6, 7, 8].map(i => cssv("--s" + i));
const store = {
  get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* private mode */ } },
};

async function api(url, opt = {}) {
  if (opt.json !== undefined) {
    opt.method = opt.method || "POST";
    opt.headers = { "Content-Type": "application/json" };
    opt.body = JSON.stringify(opt.json);
  }
  let r;
  try { r = await fetch(url, opt); } catch (e) { throw new Error("Cannot reach the server. Is app.py still running?"); }
  let data = null;
  try { data = await r.json(); } catch (e) { /* not json */ }
  if (!r.ok) throw new Error((data && data.error) || `Request failed (${r.status})`);
  return data;
}

const P = {
  users: "M16 20v-1.5a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4V20M9.5 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7M21 20v-1.5a4 4 0 0 0-3-3.9M15.5 4.2a3.5 3.5 0 0 1 0 6.6",
  steth: "M6 3v6a4 4 0 0 0 8 0V3M10 13v2a5 5 0 0 0 10 0v-2M20 11a2 2 0 1 0 0 4 2 2 0 0 0 0-4M4.5 3h3M12.5 3h3",
  calendar: "M7 3v3M17 3v3M4 9h16M5 5h14a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1M8 14h3",
  bed: "M3 19V6M3 15h18v4M21 15v-3a3 3 0 0 0-3-3h-7v6M7 12.5a1.8 1.8 0 1 0 0-3.6 1.8 1.8 0 0 0 0 3.6",
  box: "M21 8 12 3 3 8v8l9 5 9-5zM3 8l9 5 9-5M12 13v8",
  building: "M4 21V5a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v16M14 10h5a1 1 0 0 1 1 1v10M2 21h20M8 8h2M8 12h2M8 16h2M17 14h1M17 17h1",
  home: "M3 11 12 3l9 8M5 10v10h5v-6h4v6h5V10",
  map: "M9 4 3 6v14l6-2 6 2 6-2V4l-6 2zM9 4v14M15 6v14",
  chart: "M4 20V4M4 20h16M8 16v-4M12 16V8M16 16v-6",
  db: "M12 8c4.4 0 8-1.1 8-2.5S16.4 3 12 3 4 4.1 4 5.5 7.6 8 12 8M4 5.5v13C4 19.9 7.6 21 12 21s8-1.1 8-2.5v-13M4 12c0 1.4 3.6 2.5 8 2.5s8-1.1 8-2.5",
  code: "M8 8l-5 4 5 4M16 8l5 4-5 4M14 5l-4 14",
  clip: "M9 4h6a1 1 0 0 1 1 1v1H8V5a1 1 0 0 1 1-1M8 6H6a1 1 0 0 0-1 1v13a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V7a1 1 0 0 0-1-1h-2M9 13h6M9 17h4",
  syringe: "M18 3l3 3M20 5l-9 9M15 7l4 4M11 14l-6 6M9 12l3 3M5 20H3v-2",
  plus: "M12 5v14M5 12h14",
  search: "M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14M21 21l-4.3-4.3",
  edit: "M4 20h4L19 9a2.1 2.1 0 0 0-4-4L4 16zM14 6l4 4",
  trash: "M4 7h16M10 11v6M14 11v6M6 7l1 12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1l1-12M9 7V4h6v3",
  download: "M12 4v11M7 11l5 5 5-5M4 20h16",
  upload: "M12 16V5M7 9l5-5 5 5M4 20h16",
  sheet: "M5 3h14a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1M4 9h16M4 15h16M10 3v18",
  moon: "M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5",
  sun: "M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4",
  menu: "M4 6h16M4 12h16M4 18h16",
  x: "M6 6l12 12M18 6 6 18",
  play: "M7 4v16l13-8z",
  logout: "M10 4H5a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h5M15 8l4 4-4 4M19 12H9",
  wrench: "M14.7 6.3a4 4 0 0 0 5 5L21 12.6 12.6 21 3 11.4 11.4 3zM7 15l2 2",
  cross: "M12 5v14M5 12h14",
  reset: "M4 4v6h6M20 20v-6h-6M20 9A8 8 0 0 0 6 6.3L4 10M4 15a8 8 0 0 0 14 2.7L20 14",
};
const icon = n => `<svg class="i" viewBox="0 0 24 24" aria-hidden="true"><path d="${P[n] || ""}"/></svg>`;

/* ---------- toast / modal ---------- */
function toast(msg, bad) {
  const t = document.createElement("div");
  t.className = "toast" + (bad ? " bad" : "");
  t.textContent = msg;
  $("#toasts").appendChild(t);
  setTimeout(() => t.remove(), bad ? 5200 : 2800);
}

function modal({ title, body, footer, wide, onMount }) {
  const v = document.createElement("div");
  v.className = "veil";
  v.innerHTML = `<div class="modal ${wide ? "wide" : ""}" role="dialog" aria-modal="true" aria-label="${esc(title)}">
    <div class="modal-h"><h2>${esc(title)}</h2><button class="btn icon ghost" data-close aria-label="Close">${icon("x")}</button></div>
    <div class="modal-b">${body || ""}</div><div class="modal-f">${footer || ""}</div></div>`;
  document.body.appendChild(v);
  const close = () => { v.remove(); document.removeEventListener("keydown", onKey); };
  const onKey = e => { if (e.key === "Escape") close(); };
  document.addEventListener("keydown", onKey);
  v.addEventListener("mousedown", e => { if (e.target === v) close(); });
  $$("[data-close]", v).forEach(b => b.onclick = close);
  if (onMount) onMount(v, close);
  const first = $("input,select,textarea", v); if (first) first.focus();
  return { el: v, close };
}

function confirmBox(title, message, okLabel, danger) {
  return new Promise(res => {
    const m = modal({
      title, body: `<p class="muted" style="margin:6px 0 4px;white-space:pre-line">${message}</p>`,
      footer: `<button class="btn" data-close>Cancel</button><button class="btn ${danger ? "danger solid" : "primary"}" id="ok">${esc(okLabel)}</button>`,
      onMount: (v, close) => { $("#ok", v).onclick = () => { close(); res(true); }; $$("[data-close]", v).forEach(b => b.addEventListener("click", () => res(false))); },
    });
    $("#ok", m.el).focus();
  });
}

/* ---------- charts ---------- */
const charts = [];
function killCharts() { while (charts.length) charts.pop().destroy(); }
function chartDefaults() {
  const C = Chart.defaults;
  C.font.family = '"Plus Jakarta Sans","Segoe UI",system-ui,sans-serif';
  C.font.size = 12;
  C.color = cssv("--ink-2");
  C.borderColor = cssv("--grid");
  C.plugins.tooltip.backgroundColor = cssv("--ink");
  C.plugins.tooltip.titleColor = cssv("--bg");
  C.plugins.tooltip.bodyColor = cssv("--bg");
  C.plugins.tooltip.padding = 10;
  C.plugins.tooltip.cornerRadius = 8;
  C.plugins.tooltip.boxPadding = 4;
}
function merge(a, b) {
  for (const k in b) a[k] = (b[k] && typeof b[k] === "object" && !Array.isArray(b[k]) && a[k] && typeof a[k] === "object") ? merge(a[k], b[k]) : b[k];
  return a;
}
function chart(canvas, type, data, extra = {}) {
  chartDefaults();
  const noAxes = type === "doughnut" || type === "pie";
  const opts = {
    responsive: true, maintainAspectRatio: false, animation: { duration: 450 },
    plugins: { legend: { display: (data.datasets || []).length > 1 || noAxes, position: "bottom",
      labels: { usePointStyle: true, pointStyle: "rectRounded", boxWidth: 9, boxHeight: 9, padding: 14 } } },
  };
  if (!noAxes) {
    opts.scales = {
      x: { grid: { display: false }, border: { color: cssv("--line") }, ticks: { maxRotation: 0, autoSkip: true } },
      y: { beginAtZero: true, grid: { color: cssv("--grid") }, border: { display: false }, ticks: { precision: 0 } },
    };
  }
  const c = new Chart(canvas, { type, data, options: merge(opts, extra) });
  charts.push(c);
  return c;
}

/* ---------- Excel-style data grid ---------- */
const PILL = { Completed: "ok", Scheduled: "info", Cancelled: "mute", Available: "ok", Occupied: "hot", Maintenance: "warn",
  LOW: "bad", OK: "ok", "IN HOSPITAL": "hot", "In hospital": "hot", Discharged: "ok" };
const MONEY = new Set(["Fee", "Charge", "UnitCost", "Cost", "BedBill", "bed_bill", "total_cost", "revenue", "daily_charge", "avg_fee", "bill"]);
const BARS = new Set(["Qty", "Charge", "Fee", "Cost", "BedBill", "Days", "bed_bill", "total_cost", "revenue", "units_used", "total_appointments"]);
const SUMS = new Set(["Qty", "Cost", "BedBill", "bed_bill", "total_cost", "revenue", "units_used", "issues", "total_appointments", "completed", "upcoming", "total_beds", "occupied", "available", "completed_visits", "discharges", "appointments"]);
const AVGS = new Set(["Age", "Fee", "Charge", "Days", "avg_fee", "avg_days_stay", "occupancy_pct", "days_stayed"]);
const label = c => /^[a-z0-9_]+$/.test(c) ? c.replace(/_/g, " ").replace(/^./, m => m.toUpperCase()) : c;

function makeGrid(host, cfg) {
  const st = { cols: [], rows: [], sort: -1, dir: 1, q: "", page: 0, chip: null, chipCol: -1, sel: null, size: cfg.pageSize || 20 };
  host.innerHTML = `<div class="panel sheet">
    <div class="tools">
      <div class="search">${icon("search")}<input class="in" data-q placeholder="${esc(cfg.searchPlaceholder || "Search every column...")}" aria-label="Search"></div>
      <div class="chips" data-chips></div><div class="grow"></div>
      <span class="faint" data-count></span>
      <button class="btn" data-chart>${icon("chart")}<span class="lbl">Chart</span></button>
      ${cfg.exportUrl || cfg.exportFn ? `<button class="btn" data-xl>${icon("sheet")}<span class="lbl">Export to Excel</span></button>` : ""}
      ${cfg.importTable ? `<button class="btn" data-imp>${icon("upload")}<span class="lbl">Import</span></button>` : ""}
      ${(cfg.extra || []).map((b, i) => `<button class="btn" data-extra="${i}">${icon(b.icon)}<span class="lbl">${esc(b.label)}</span></button>`).join("")}
      ${cfg.onNew ? `<button class="btn primary" data-new>${icon("plus")}${esc(cfg.newLabel || "New")}</button>` : ""}
    </div>
    <div class="scroller"></div><div class="pager"></div></div>`;
  const sc = $(".scroller", host), pager = $(".pager", host);

  const isNum = i => st.rows.length && st.rows.every(r => r[i] === null || typeof r[i] === "number");
  const hide0 = cfg.hideId !== false;
  const first = hide0 ? 1 : 0;

  function filtered() {
    let out = st.rows;
    if (st.chip !== null) out = out.filter(r => String(r[st.chipCol]) === st.chip);
    if (st.q) { const q = st.q.toLowerCase(); out = out.filter(r => r.some(v => v !== null && String(v).toLowerCase().includes(q))); }
    if (st.sort >= 0) {
      const i = st.sort, d = st.dir;
      out = [...out].sort((a, b) => {
        const x = a[i], y = b[i];
        if (x === y) return 0; if (x === null) return 1; if (y === null) return -1;
        return (typeof x === "number" && typeof y === "number" ? x - y : String(x).localeCompare(String(y), undefined, { numeric: true })) * d;
      });
    }
    return out;
  }

  function cell(ci, v, row, maxes) {
    const c = st.cols[ci];
    if (v === null || v === "") return `<td class="${isNum(ci) ? "num" : ""}"><span class="faint">-</span></td>`;
    if (typeof v === "string" && PILL[v]) return `<td><span class="pill ${PILL[v]}">${esc(v)}</span></td>`;
    if (typeof v === "number") {
      let t = MONEY.has(c) ? inr(v) : num(v);
      if (BARS.has(c) && maxes[ci] > 0) {
        const mi = st.cols.indexOf("Min");
        const low = c === "Qty" && mi >= 0 && v <= row[mi];
        return `<td class="num"><span class="cellbar ${low ? "low" : ""}" style="--w:${Math.max(2, v / maxes[ci] * 100).toFixed(0)}%"><span>${t}</span></span></td>`;
      }
      return `<td class="num">${t}</td>`;
    }
    return `<td title="${esc(v)}">${esc(v)}</td>`;
  }

  function render() {
    const all = filtered();
    const pages = Math.max(1, Math.ceil(all.length / st.size));
    st.page = Math.min(st.page, pages - 1);
    const slice = all.slice(st.page * st.size, (st.page + 1) * st.size);
    const maxes = st.cols.map((c, i) => isNum(i) ? Math.max(0, ...st.rows.map(r => r[i] || 0)) : 0);
    const showFoot = cfg.totals !== false && all.length > 0;
    const sumCol = i => {
      const c = st.cols[i]; if (!isNum(i)) return null;
      if (SUMS.has(c)) return "sum"; if (AVGS.has(c)) return "avg";
      if (cfg.autoTotals && !/(^|_)id$|pct|avg|age|rate|^id$/i.test(c)) return "sum";
      return null;
    };
    let h = `<table class="xl"><thead><tr><th class="rn">#</th>`;
    for (let i = first; i < st.cols.length; i++)
      h += `<th data-sort="${i}" class="${isNum(i) ? "num" : ""} ${st.sort === i ? "sorted" : ""}">${esc(label(st.cols[i]))}<span class="arr">${st.sort === i ? (st.dir > 0 ? "▲" : "▼") : "▲"}</span></th>`;
    if (cfg.onEdit || cfg.onDelete || cfg.rowAction) h += `<th class="act"></th>`;
    h += `</tr></thead><tbody>`;
    slice.forEach((r, n) => {
      const key = hide0 ? r[0] : n;
      h += `<tr data-key="${esc(key)}" class="${String(st.sel) === String(key) ? "sel" : ""}"><td class="rn">${st.page * st.size + n + 1}</td>`;
      for (let i = first; i < st.cols.length; i++) h += cell(i, r[i], r, maxes);
      if (cfg.onEdit || cfg.onDelete || cfg.rowAction) {
        h += `<td class="act">${cfg.rowAction ? cfg.rowAction(r, st.cols) : ""}
          ${cfg.onEdit ? `<button class="btn sm icon ghost" data-edit="${esc(key)}" aria-label="Edit">${icon("edit")}</button>` : ""}
          ${cfg.onDelete ? `<button class="btn sm icon ghost danger" data-del="${esc(key)}" aria-label="Delete">${icon("trash")}</button>` : ""}</td>`;
      }
      h += `</tr>`;
    });
    if (!slice.length) h += `<tr><td colspan="${st.cols.length + 2}"><div class="empty"><b>${st.rows.length ? "Nothing matches your search" : "No records yet"}</b>${st.rows.length ? "Clear the search box or pick another filter." : "Use the button above to add the first one."}</div></td></tr>`;
    h += `</tbody>`;
    if (showFoot) {
      h += `<tfoot><tr><td class="rn">Σ</td>`;
      for (let i = first; i < st.cols.length; i++) {
        const m = sumCol(i); let t = "";
        if (m) {
          const vals = all.map(r => r[i]).filter(v => typeof v === "number");
          const s = vals.reduce((a, b) => a + b, 0);
          const val = m === "sum" ? s : s / (vals.length || 1);
          t = `<span class="faint" style="font-weight:600">${m === "sum" ? "sum" : "avg"}</span> ${MONEY.has(st.cols[i]) ? inr(val) : num(val)}`;
        }
        h += `<td class="${isNum(i) ? "num" : ""}">${t}</td>`;
      }
      if (cfg.onEdit || cfg.onDelete || cfg.rowAction) h += `<td class="act"></td>`;
      h += `</tr></tfoot>`;
    }
    h += `</table>`;
    sc.innerHTML = h;
    $("[data-count]", host).textContent = `${all.length} of ${st.rows.length} record${st.rows.length === 1 ? "" : "s"}`;
    pager.innerHTML = pages > 1 ? `<span class="grow">Page ${st.page + 1} of ${pages}</span>
      <button class="btn sm" data-pg="-1" ${st.page === 0 ? "disabled" : ""}>Previous</button>
      <button class="btn sm" data-pg="1" ${st.page >= pages - 1 ? "disabled" : ""}>Next</button>` : `<span class="grow faint">Click a column heading to sort. The bottom row totals whatever is filtered.</span>`;
  }

  function chips() {
    const cands = ["Status", "Stock", "Type", "Category", "Gender", "Event", "state"];
    st.chipCol = st.cols.findIndex(c => cands.includes(c));
    const box = $("[data-chips]", host);
    if (st.chipCol < 0) { box.innerHTML = ""; return; }
    const counts = {};
    st.rows.forEach(r => { const k = String(r[st.chipCol]); counts[k] = (counts[k] || 0) + 1; });
    const keys = Object.keys(counts);
    if (keys.length > 6 || keys.length < 2) { box.innerHTML = ""; st.chipCol = -1; return; }
    box.innerHTML = `<button class="chip ${st.chip === null ? "on" : ""}" data-chip="">All<b>${st.rows.length}</b></button>` +
      keys.map(k => `<button class="chip ${st.chip === k ? "on" : ""}" data-chip="${esc(k)}">${esc(k)}<b>${counts[k]}</b></button>`).join("");
  }

  host.addEventListener("click", e => {
    const t = e.target.closest("[data-sort],[data-pg],[data-chip],[data-edit],[data-del],[data-new],[data-chart],[data-xl],[data-imp],[data-extra],[data-act],tr[data-key]");
    if (!t) return;
    if (t.dataset.sort !== undefined) { const i = +t.dataset.sort; st.dir = st.sort === i ? -st.dir : 1; st.sort = i; render(); }
    else if (t.dataset.pg) { st.page += +t.dataset.pg; render(); }
    else if (t.dataset.chip !== undefined) { st.chip = t.dataset.chip === "" ? null : t.dataset.chip; st.page = 0; chips(); render(); }
    else if (t.dataset.edit !== undefined) cfg.onEdit(t.dataset.edit);
    else if (t.dataset.del !== undefined) cfg.onDelete(t.dataset.del);
    else if (t.dataset.new !== undefined) cfg.onNew();
    else if (t.dataset.chart !== undefined) chartBuilder(st.cols.slice(first), filtered().map(r => r.slice(first)), cfg.title || "Chart");
    else if (t.dataset.xl !== undefined) (cfg.exportFn ? cfg.exportFn() : (location.href = cfg.exportUrl));
    else if (t.dataset.imp !== undefined) importDialog(cfg.importTable, cfg.onChange);
    else if (t.dataset.extra !== undefined) cfg.extra[+t.dataset.extra].fn();
    else if (t.dataset.act !== undefined) cfg.onAct && cfg.onAct(t.dataset.act, t.dataset.id);
    else if (t.dataset.key !== undefined) { st.sel = t.dataset.key; $$("tr.sel", sc).forEach(r => r.classList.remove("sel")); t.classList.add("sel"); }
  });
  $("[data-q]", host).addEventListener("input", e => { st.q = e.target.value; st.page = 0; render(); });

  return {
    set(cols, rows) { st.cols = cols; st.rows = rows; st.chip = null; st.sort = -1; chips(); render(); },
    filtered, state: st,
  };
}

/* ---------- "Insert chart" for any grid ---------- */
function chartBuilder(cols, rows, title) {
  if (!rows.length) return toast("There is nothing to chart yet.", true);
  const isNum = i => rows.every(r => r[i] === null || typeof r[i] === "number");
  const catCols = cols.map((c, i) => i).filter(i => new Set(rows.map(r => r[i])).size <= 60 && new Set(rows.map(r => r[i])).size > 1);
  const numCols = cols.map((c, i) => i).filter(i => isNum(i) && !/(^|_)id$|^id$/i.test(cols[i]));
  if (!catCols.length) return toast("No column has a useful set of categories to group by.", true);
  const distinct = i => new Set(rows.map(r => r[i])).size;
  const bestX = catCols.find(i => !isNum(i) && distinct(i) >= 2 && distinct(i) <= 12) ?? catCols[0];
  const m = modal({
    title: "Chart this view", wide: true,
    body: `<div class="builder" style="padding:0 0 12px;grid-template-columns:repeat(4,minmax(0,1fr))">
      <div class="field"><label>Group by (X axis)</label><select class="in" id="cx">${catCols.map(i => `<option value="${i}" ${i === bestX ? "selected" : ""}>${esc(label(cols[i]))}</option>`).join("")}</select></div>
      <div class="field"><label>Measure</label><select class="in" id="cy"><option value="-1">Count of records</option>${numCols.map(i => `<option value="${i}">${esc(label(cols[i]))}</option>`).join("")}</select></div>
      <div class="field"><label>Calculation</label><select class="in" id="ca"><option value="sum">Sum</option><option value="avg">Average</option><option value="max">Maximum</option></select></div>
      <div class="field"><label>Chart type</label><div class="seg" id="ct">${["bar", "line", "pie", "doughnut"].map((t, i) => `<button data-t="${t}" class="${i ? "" : "on"}">${t === "doughnut" ? "Donut" : t[0].toUpperCase() + t.slice(1)}</button>`).join("")}</div></div>
    </div><div class="chart-box tall"><canvas id="cv"></canvas></div>`,
    footer: `<button class="btn" data-close>Close</button>`,
    onMount(v) {
      let type = "bar", cv;
      const draw = () => {
        const x = +$("#cx", v).value, y = +$("#cy", v).value, agg = $("#ca", v).value;
        $("#ca", v).disabled = y < 0;
        const g = new Map();
        rows.forEach(r => { const k = r[x] === null ? "-" : String(r[x]); const a = g.get(k) || []; a.push(y < 0 ? 1 : (r[y] || 0)); g.set(k, a); });
        let pts = [...g].map(([k, a]) => [k, y < 0 ? a.length : agg === "sum" ? a.reduce((p, q) => p + q, 0) : agg === "avg" ? a.reduce((p, q) => p + q, 0) / a.length : Math.max(...a)]);
        const dateLike = pts.every(p => /^\d{4}-\d{2}/.test(p[0]));
        pts.sort((a, b) => dateLike ? a[0].localeCompare(b[0]) : b[1] - a[1]);
        if (type === "pie" || type === "doughnut") { if (pts.length > 8) { const rest = pts.slice(7).reduce((s, p) => s + p[1], 0); pts = [...pts.slice(0, 7), ["Other", rest]]; } }
        else pts = pts.slice(0, 30);
        const cols8 = seriesColors();
        const name = y < 0 ? "Records" : `${agg === "sum" ? "Sum" : agg === "avg" ? "Average" : "Max"} of ${label(cols[y])}`;
        const ds = type === "pie" || type === "doughnut"
          ? [{ data: pts.map(p => +p[1].toFixed(2)), backgroundColor: pts.map((_, i) => cols8[i % 8]), borderColor: cssv("--surface"), borderWidth: 2 }]
          : [{ label: name, data: pts.map(p => +p[1].toFixed(2)), backgroundColor: cols8[0], borderColor: cols8[0], borderRadius: 4, maxBarThickness: 36, tension: .3, pointRadius: 3 }];
        const old = charts.findIndex(c => c.canvas && c.canvas.id === "cv"); if (old >= 0) charts.splice(old, 1)[0].destroy();
        cv = $("#cv", v);
        chart(cv, type, { labels: pts.map(p => p[0]), datasets: ds }, { plugins: { legend: { display: type === "pie" || type === "doughnut" } } });
      };
      $$("select", v).forEach(s => s.onchange = draw);
      $$("#ct button", v).forEach(b => b.onclick = () => { $$("#ct button", v).forEach(x => x.classList.remove("on")); b.classList.add("on"); type = b.dataset.t; draw(); });
      draw();
    },
  });
}

/* ---------- import dialog ---------- */
function importDialog(table, done) {
  modal({
    title: "Import from Excel or CSV",
    body: `<p class="muted" style="margin:4px 0 12px">Pick an <b>.xlsx</b> or <b>.csv</b> file. The first row must hold column headings that match the table (for example the file you get from <i>Export to Excel</i>). Invalid rows are skipped and reported.</p>
      <input type="file" id="f" accept=".xlsx,.csv" class="in" style="padding-top:7px"><div class="form-err" id="e" style="margin-top:12px"></div>`,
    footer: `<button class="btn" data-close>Cancel</button><button class="btn primary" id="go">${icon("upload")}Import file</button>`,
    onMount(v, close) {
      $("#go", v).onclick = async () => {
        const f = $("#f", v).files[0];
        if (!f) { const e = $("#e", v); e.textContent = "Choose a file first."; e.style.display = "block"; return; }
        const fd = new FormData(); fd.append("file", f);
        try {
          const r = await api(`/api/import/${table}`, { method: "POST", body: fd });
          close();
          toast(`Imported ${r.imported} record(s)` + (r.skipped ? `, skipped ${r.skipped}: ${r.problems[0]}` : ""), !!r.skipped && !r.imported);
          done && done();
        } catch (err) { const e = $("#e", v); e.textContent = err.message; e.style.display = "block"; }
      };
    },
  });
}

async function download(url, opt, name) {
  const r = await fetch(url, opt);
  if (!r.ok) { let m = "Export failed"; try { m = (await r.json()).error; } catch (e) { /* */ } throw new Error(m); }
  const b = await r.blob(), a = document.createElement("a");
  a.href = URL.createObjectURL(b); a.download = name; document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}
