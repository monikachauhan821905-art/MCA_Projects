"use strict";
/* ===========================================================
   pages.js - navigation, router and every page
   =========================================================== */
let META = null;
let CURRENT = null;

const NAV = [
  ["Overview", [["dashboard", "Dashboard", "home"], ["bedmap", "Ward map", "map"], ["analytics", "Analytics", "chart"]]],
  ["Patient care", [["patients", "Patients", "users"], ["appointments", "Appointments", "calendar"], ["admissions", "Admissions", "clip"]]],
  ["Hospital", [["doctors", "Doctors", "steth"], ["beds", "Beds", "bed"], ["resources", "Resources", "box"], ["usage", "Issue log", "syringe"], ["departments", "Departments", "building"]]],
  ["Database", [["sqllab", "SQL lab", "code"], ["schema", "Tables & triggers", "db"]]],
];
const TITLES = {
  dashboard: ["Dashboard", () => `${new Date().toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long" })}`],
  bedmap: ["Ward map", () => "Every bed, live. Click one to admit, discharge or release it."],
  analytics: ["Analytics", () => "Build your own pivot table and chart, the way you would in Excel."],
  patients: ["Patients", () => "Registered patients"],
  appointments: ["Appointments", () => "Bookings across all doctors"],
  admissions: ["Admissions", () => "Bed allocation and discharge. Beds update by trigger."],
  doctors: ["Doctors", () => "Medical staff and consultation fees"],
  beds: ["Beds", () => "Bed inventory and daily charges"],
  resources: ["Resources", () => "Equipment, medicines and consumables in stock"],
  usage: ["Issue log", () => "Every resource handed to a patient. Stock reduces by trigger."],
  departments: ["Departments", () => "Hospital departments"],
  sqllab: ["SQL lab", () => "Run the project's report queries, or write your own."],
  schema: ["Tables & triggers", () => "The relational design behind the app"],
};

function buildSide() {
  $("#side").innerHTML = `
    <div class="brand"><div class="brand-mark">${icon("cross")}</div><div><b>CareDesk</b><small>Patient &amp; resource management</small></div></div>
    <nav class="nav">${NAV.map(([g, items]) => `<div class="nav-group">${g}</div>` +
      items.map(([id, t, ic]) => `<a href="#/${id}" data-id="${id}">${icon(ic)}<span>${t}</span><span class="badge" data-badge="${id}" hidden></span></a>`).join("")).join("")}</nav>
    <div class="side-foot">SQLite ${META.sqlite}<br><a href="#" id="reset" style="color:inherit">Reset sample data</a></div>`;
  $("#reset").onclick = async e => {
    e.preventDefault();
    if (!await confirmBox("Reset sample data?", "This deletes hospital.db and rebuilds it with fresh sample data. Any records you added will be lost.", "Reset database", true)) return;
    await api("/api/reset", { method: "POST" }); toast("Sample data restored"); route();
  };
  $("#menu").innerHTML = icon("menu");
  $("#menu").onclick = () => document.body.classList.toggle("nav-open");
}

function topActions() {
  const dark = document.documentElement.dataset.theme === "dark";
  $("#top-actions").innerHTML = `
    <button class="btn" id="wb" title="All tables + dashboard charts as one Excel file">${icon("sheet")}<span class="lbl">Export workbook</span></button>
    <button class="btn icon" id="theme" aria-label="Toggle dark mode">${icon(dark ? "sun" : "moon")}</button>`;
  $("#wb").onclick = () => { location.href = "/api/export/workbook.xlsx"; toast("Building workbook with charts..."); };
  $("#theme").onclick = () => {
    const d = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = d; store.set("theme", d); topActions(); route();
  };
}

async function badges() {
  try {
    const r = await api("/api/t/resources");
    const i = r.columns.indexOf("Stock"), n = r.rows.filter(x => x[i] === "LOW").length;
    const b = $('[data-badge="resources"]'); if (b) { b.hidden = !n; b.textContent = n; }
  } catch (e) { /* badge is optional */ }
}

/* ---------- router ---------- */
async function route() {
  document.body.classList.remove("nav-open");
  const id = (location.hash.replace(/^#\//, "") || "dashboard");
  const pg = PAGES[id] ? id : "dashboard";
  CURRENT = pg;
  $$(".nav a").forEach(a => a.classList.toggle("on", a.dataset.id === pg));
  const [t, sub] = TITLES[pg];
  $("#title").textContent = t; $("#subtitle").textContent = sub();
  document.title = `${t} - CareDesk`;
  killCharts();
  const view = $("#view");
  view.innerHTML = `<div class="loader">Loading...</div>`;
  try { await PAGES[pg](view); } catch (e) { view.innerHTML = `<div class="panel panel-b empty"><b>Something went wrong</b>${esc(e.message)}</div>`; }
  badges();
}
const refresh = () => route();

/* ---------- record forms ---------- */
async function optionsFor(key) { return api("/api/options/" + key); }
function selectHtml(id, opts, val, placeholder) {
  return `<select class="in" id="${id}"><option value="">${esc(placeholder || "Select...")}</option>${opts.map(o => `<option value="${esc(o.id)}" ${String(o.id) === String(val) ? "selected" : ""}>${esc(o.label)}</option>`).join("")}</select>`;
}

async function openForm(table, id) {
  const cfg = META.tables[table];
  const rec = id ? await api(`/api/t/${table}/${id}`) : {};
  const opts = {};
  for (const f of cfg.fields) if (f.kind === "fk") opts[f.col] = await optionsFor(f.options);
  const field = f => {
    let v = rec[f.col];
    if (v === undefined || v === null) v = f.default === "@today" ? META.today : (f.default ?? "");
    const inp = f.kind === "choice" ? `<select class="in" id="f_${f.col}"><option value="">Select...</option>${f.choices.map(c => `<option ${c === v ? "selected" : ""}>${esc(c)}</option>`).join("")}</select>`
      : f.kind === "fk" ? selectHtml("f_" + f.col, opts[f.col], v)
      : `<input class="in" id="f_${f.col}" type="${f.kind === "number" ? "number" : f.kind === "date" ? "date" : f.kind === "time" ? "time" : "text"}" ${f.min !== undefined ? `min="${f.min}"` : ""} ${f.max !== undefined ? `max="${f.max}"` : ""} step="any" value="${esc(v)}">`;
    return `<div class="field ${f.wide ? "wide" : ""}"><label for="f_${f.col}">${esc(f.label)}${f.req ? " <i>*</i>" : ""}</label>${inp}</div>`;
  };
  modal({
    title: (id ? "Edit " : "New ") + cfg.title.replace(/s$/, "").toLowerCase(),
    body: `<div class="form"><div class="form-err" id="err"></div>${cfg.fields.map(field).join("")}</div>`,
    footer: `<button class="btn" data-close>Cancel</button><button class="btn primary" id="save">${id ? "Save changes" : "Add " + cfg.title.replace(/s$/, "").toLowerCase()}</button>`,
    onMount(v, close) {
      const go = async () => {
        const data = {}; cfg.fields.forEach(f => data[f.col] = $("#f_" + f.col, v).value);
        try {
          await api(`/api/t/${table}${id ? "/" + id : ""}`, { method: id ? "PUT" : "POST", json: data });
          close(); toast(id ? "Changes saved" : "Added"); refresh();
        } catch (e) { const er = $("#err", v); er.textContent = e.message; er.style.display = "block"; }
      };
      $("#save", v).onclick = go;
      v.addEventListener("keydown", e => { if (e.key === "Enter" && e.target.tagName === "INPUT") go(); });
    },
  });
}

async function removeRecord(table, id) {
  if (!await confirmBox("Delete this record?", "This cannot be undone. Records linked to other tables cannot be deleted.", "Delete", true)) return;
  try { await api(`/api/t/${table}/${id}`, { method: "DELETE" }); toast("Deleted"); refresh(); } catch (e) { toast(e.message, true); }
}

async function admitDialog(bedId) {
  const [pat, bed, doc] = await Promise.all([optionsFor("patients"), optionsFor("free_beds"), optionsFor("doctors")]);
  if (!bed.length) return toast("No beds are free right now.", true);
  modal({
    title: "Admit a patient",
    body: `<div class="form"><div class="form-err" id="err"></div>
      <div class="field"><label>Patient <i>*</i></label>${selectHtml("a_p", pat)}</div>
      <div class="field"><label>Available bed <i>*</i></label>${selectHtml("a_b", bed, bedId)}</div>
      <div class="field"><label>Doctor <i>*</i></label>${selectHtml("a_d", doc)}</div>
      <div class="field"><label>Diagnosis</label><input class="in" id="a_g" placeholder="e.g. Pneumonia"></div></div>`,
    footer: `<button class="btn" data-close>Cancel</button><button class="btn primary" id="go">Admit patient</button>`,
    onMount(v, close) {
      $("#go", v).onclick = async () => {
        try {
          await api("/api/admit", { json: { patient_id: $("#a_p", v).value, bed_id: $("#a_b", v).value, doctor_id: $("#a_d", v).value, diagnosis: $("#a_g", v).value } });
          close(); toast("Patient admitted. Bed marked Occupied."); refresh();
        } catch (e) { const er = $("#err", v); er.textContent = e.message; er.style.display = "block"; }
      };
    },
  });
}

async function dischargeDialog(admId) {
  const p = await api("/api/discharge/" + admId);
  if (p.already) return toast("This patient is already discharged.", true);
  modal({
    title: "Discharge " + p.patient,
    body: `<dl class="dl"><dt>Bed</dt><dd>${esc(p.bed)}</dd><dt>Admitted</dt><dd>${esc(p.admitted)}</dd><dt>Days stayed</dt><dd>${p.days}</dd>
      <dt>Daily charge</dt><dd>${inr(p.charge)}</dd><dt>Bed charges to bill</dt><dd style="font-size:18px">${inr(p.bill)}</dd></dl>`,
    footer: `<button class="btn" data-close>Cancel</button><button class="btn primary" id="go">Discharge patient</button>`,
    onMount(v, close) {
      $("#go", v).onclick = async () => {
        try { await api("/api/discharge/" + admId, { method: "POST" }); close(); toast("Discharged. Bed is available again."); refresh(); }
        catch (e) { toast(e.message, true); }
      };
    },
  });
}

async function issueDialog() {
  const [res, pat] = await Promise.all([optionsFor("stock"), optionsFor("patients")]);
  modal({
    title: "Issue a resource to a patient",
    body: `<div class="form"><div class="form-err" id="err"></div>
      <div class="field wide"><label>Resource <i>*</i></label>${selectHtml("i_r", res)}</div>
      <div class="field"><label>Patient <i>*</i></label>${selectHtml("i_p", pat)}</div>
      <div class="field"><label>Quantity <i>*</i></label><input class="in" id="i_q" type="number" min="1" value="1"></div></div>`,
    footer: `<button class="btn" data-close>Cancel</button><button class="btn primary" id="go">Issue resource</button>`,
    onMount(v, close) {
      $("#go", v).onclick = async () => {
        try {
          await api("/api/issue", { json: { res_id: $("#i_r", v).value, patient_id: $("#i_p", v).value, qty: $("#i_q", v).value } });
          close(); toast("Issued. Stock reduced."); refresh();
        } catch (e) { const er = $("#err", v); er.textContent = e.message; er.style.display = "block"; }
      };
    },
  });
}

/* ---------- bed tile + drawer ---------- */
function bedTile(b, big) {
  const cls = b.status === "Occupied" ? "occ" : b.status === "Maintenance" ? "mnt" : "free";
  const who = b.status === "Occupied" ? `${esc(b.patient)}<small>Day ${b.days}</small>` : b.status === "Maintenance" ? "Under service" : "Free";
  const tip = `${b.ward}-${b.bed_no} · ${b.bed_type} · ${b.status}` + (b.patient ? ` · ${b.patient}` : "");
  return `<button class="bed ${cls} ${big ? "big" : ""}" data-bed="${b.bed_id}" title="${esc(tip)}">
    <span class="no">${esc(b.bed_no)}${b.bed_type !== "General" ? `<em>${b.bed_type === "ICU" ? "ICU" : "PVT"}</em>` : ""}</span><span class="who">${who}</span></button>`;
}
function wardMap(beds, big) {
  const wards = {};
  beds.forEach(b => (wards[b.ward] = wards[b.ward] || []).push(b));
  return `<div class="ward-wrap">${Object.entries(wards).map(([w, bs]) => {
    const occ = bs.filter(b => b.status === "Occupied").length;
    return `<div class="ward"><div class="ward-h"><b>${esc(w)}</b><span>${occ}/${bs.length} occupied</span></div><div class="beds">${bs.map(b => bedTile(b, big)).join("")}</div></div>`;
  }).join("")}</div>`;
}
function wireBeds(root, beds) {
  root.addEventListener("click", e => {
    const t = e.target.closest("[data-bed]"); if (!t) return;
    const b = beds.find(x => x.bed_id === +t.dataset.bed);
    const pill = b.status === "Available" ? "ok" : b.status === "Occupied" ? "hot" : "warn";
    const body = `<dl class="dl"><dt>Status</dt><dd><span class="pill ${pill}">${b.status}</span></dd><dt>Type</dt><dd>${esc(b.bed_type)}</dd>
      <dt>Department</dt><dd>${esc(b.department || "-")}</dd><dt>Daily charge</dt><dd>${inr(b.daily_charge)}</dd>
      ${b.patient ? `<dt>Patient</dt><dd>${esc(b.patient)}</dd><dt>Doctor</dt><dd>${esc(b.doctor)}</dd><dt>Diagnosis</dt><dd>${esc(b.diagnosis || "-")}</dd><dt>Stay so far</dt><dd>${b.days} day(s) · ${inr(b.days * b.daily_charge)}</dd>` : ""}</dl>`;
    const foot = `<button class="btn" data-close>Close</button>` +
      (b.status === "Available" ? `<button class="btn" id="mnt">Send for maintenance</button><button class="btn primary" id="adm">Admit patient here</button>` : "") +
      (b.status === "Occupied" ? `<button class="btn primary" id="dis">Discharge ${esc(b.patient.split(" ")[0])}</button>` : "") +
      (b.status === "Maintenance" ? `<button class="btn primary" id="rel">Mark as available</button>` : "");
    modal({
      title: `${b.ward} · Bed ${b.bed_no}`, body, footer: foot,
      onMount(v, close) {
        const setStatus = async s => {
          const rec = await api(`/api/t/beds/${b.bed_id}`); rec.status = s;
          try { await api(`/api/t/beds/${b.bed_id}`, { method: "PUT", json: rec }); close(); toast(`Bed ${b.bed_no} is now ${s}`); refresh(); } catch (er) { toast(er.message, true); }
        };
        const a = $("#adm", v); if (a) a.onclick = () => { close(); admitDialog(b.bed_id); };
        const d = $("#dis", v); if (d) d.onclick = () => { close(); dischargeDialog(b.adm_id); };
        const m = $("#mnt", v); if (m) m.onclick = () => setStatus("Maintenance");
        const r = $("#rel", v); if (r) r.onclick = () => setStatus("Available");
      },
    });
  });
}

/* ===========================================================
   PAGES
   =========================================================== */
const PAGES = {};

PAGES.dashboard = async view => {
  const [d, beds] = await Promise.all([api("/api/dashboard"), api("/api/bedmap")]);
  const k = d.kpi, cs = seriesColors();
  const pct = k.beds_total ? Math.round(100 * k.beds_occ / k.beds_total) : 0;
  const kp = [
    ["Patients", k.patients, "", `<b>+${k.patients_week}</b> registered this week`, cs[0], ""],
    ["Doctors", k.doctors, "", "on the roster", cs[6], ""],
    ["Appointments today", k.appt_today, "", `<b>${k.appt_today_done}</b> done, ${k.appt_today - k.appt_today_done} to go`, cs[2], ""],
    ["Beds free", k.beds_free, ` / ${k.beds_total}`, `${k.beds_mnt} under maintenance`, cs[3], ""],
    ["Admitted now", k.admitted, "", `<b>${inr(k.bed_bill_running)}</b> running bed bill`, cs[1], ""],
    ["Low-stock items", k.low_stock, "", "at or below minimum level", cs[7], k.low_stock ? "alert" : ""],
  ];
  view.innerHTML = `
    <div class="kpis">${kp.map(([l, v, s, dd, c, a]) => `<div class="kpi ${a}"><div class="l"><span class="dot" style="background:${c}"></span>${l}</div>
      <div class="v"><span data-count="${v}">0</span><small>${s}</small></div><div class="d">${dd}</div></div>`).join("")}</div>
    <div class="grid g-12" style="margin-top:16px">
      <section class="panel span-8"><div class="panel-h"><h3>Ward map</h3><span class="note">${k.beds_occ} of ${k.beds_total} beds occupied. Click a bed to act on it.</span><span class="grow"></span>
        <div class="legend"><span><i style="background:var(--free)"></i>Available</span><span><i style="background:var(--occ)"></i>Occupied</span><span><i style="background:var(--mnt)"></i>Maintenance</span></div></div>
        <div class="panel-b" id="map">${wardMap(beds)}</div></section>
      <section class="panel span-4"><div class="panel-h"><h3>Bed occupancy by department</h3></div>
        <div class="panel-b"><div class="chart-box" style="height:400px"><canvas id="c_occ"></canvas></div></div></section>

      <section class="panel span-8"><div class="panel-h"><h3>Appointments</h3><span class="note">last 14 days and the next 3</span></div>
        <div class="panel-b"><div class="chart-box"><canvas id="c_days"></canvas></div></div></section>
      <section class="panel span-4"><div class="panel-h"><h3>Today's schedule</h3><span class="grow"></span><a class="note" href="#/appointments">All appointments</a></div>
        <div class="panel-b" style="max-height:290px;overflow:auto">${d.schedule.length ? `<div class="rows">${d.schedule.map(s => `<div class="row"><span class="time">${s.time}</span>
          <div style="min-width:0"><div class="t">${esc(s.patient)}</div><div class="s">${esc(s.doctor)} · ${esc(s.reason || "")}</div></div>
          <span class="r"><span class="pill ${PILL[s.status] || "mute"}">${s.status}</span></span></div>`).join("")}</div>` :
          `<div class="empty"><b>No appointments today</b>Book one from the Appointments page.</div>`}</div></section>

      <section class="panel span-4"><div class="panel-h"><h3>Consultation revenue</h3><span class="note">completed visits, by department</span></div>
        <div class="panel-b"><div class="chart-box"><canvas id="c_rev"></canvas></div></div></section>
      <section class="panel span-4"><div class="panel-h"><h3>Stock against minimum level</h3><span class="grow"></span><a class="note" href="#/resources">All resources</a></div>
        <div class="panel-b"><div class="rows">${d.stock.map(s => {
          const low = s.quantity <= s.min_level;
          return `<div class="row" style="gap:10px"><div style="flex:1;min-width:0"><div class="t" style="font-size:13px">${esc(s.name)}</div>
            <div class="meter ${low ? "low" : ""}" style="margin-top:5px"><i style="width:${Math.min(100, s.pct / 2)}%"></i></div></div>
            <div class="r" style="min-width:74px"><b>${s.quantity}</b> <span class="faint">/ min ${s.min_level}</span></div></div>`;
        }).join("")}</div></div></section>
      <section class="panel span-4"><div class="panel-h"><h3>Patients by age group</h3><span class="note">${d.gender.map(g => `${g.n} ${g.label.toLowerCase()}`).join(", ")}</span></div>
        <div class="panel-b"><div class="chart-box"><canvas id="c_age"></canvas></div></div></section>

      <section class="panel span-6"><div class="panel-h"><h3>Currently admitted</h3><span class="grow"></span><a class="note" href="#/admissions">All admissions</a></div>
        <div class="panel-b">${d.inpatients.length ? `<div class="rows">${d.inpatients.map((p, i) => `<div class="row"><span class="avatar" style="background:${cs[i % 8]}">${initials(p.patient)}</span>
          <div style="min-width:0"><div class="t">${esc(p.patient)}</div><div class="s">${esc(p.diagnosis || "-")} · ${esc(p.doctor)}</div></div>
          <span class="r"><b>${esc(p.bed)}</b><div class="s">day ${p.days}</div></span></div>`).join("")}</div>` : `<div class="empty"><b>No inpatients</b>Admit a patient from the ward map.</div>`}</div></section>
      <section class="panel span-6"><div class="panel-h"><h3>Doctor workload</h3><span class="note">completed and upcoming appointments</span></div>
        <div class="panel-b"><div class="chart-box"><canvas id="c_doc"></canvas></div></div></section>
    </div>`;

  // one orchestrated moment: the KPI numbers count up once
  $$("[data-count]", view).forEach(el => {
    const to = +el.dataset.count, t0 = performance.now();
    const step = t => { const p = Math.min(1, (t - t0) / 650); el.textContent = Math.round(to * (1 - Math.pow(1 - p, 3))); if (p < 1) requestAnimationFrame(step); };
    requestAnimationFrame(step);
  });
  wireBeds($("#map"), beds);

  // occupancy: stacked horizontal bars (status colours + full labels in tooltip)
  const oc = d.occupancy;
  chart($("#c_occ"), "bar", { labels: oc.map(o => o.department), datasets: [
    { label: "Occupied", data: oc.map(o => o.occupied), backgroundColor: cssv("--occ"), borderSkipped: false },
    { label: "Available", data: oc.map(o => o.available), backgroundColor: cssv("--free"), borderSkipped: false },
    { label: "Maintenance", data: oc.map(o => o.maintenance), backgroundColor: cssv("--mnt"), borderSkipped: false }] },
    { indexAxis: "y", scales: { x: { stacked: true, ticks: { precision: 0 } }, y: { stacked: true, grid: { display: false } } },
      datasets: { bar: { borderRadius: 3, maxBarThickness: 20 } },
      plugins: { tooltip: { callbacks: { footer: i => `Occupancy ${oc[i[0].dataIndex].occupancy_pct}%` } } } });

  chart($("#c_days"), "bar", { labels: d.days.map(x => new Date(x.day + "T00:00").toLocaleDateString("en-IN", { day: "numeric", month: "short" })), datasets: [
    { label: "Completed", data: d.days.map(x => x.Completed), backgroundColor: cs[0] },
    { label: "Scheduled", data: d.days.map(x => x.Scheduled), backgroundColor: cs[2] },
    { label: "Cancelled", data: d.days.map(x => x.Cancelled), backgroundColor: cssv("--ink-3") }] },
    { scales: { x: { stacked: true }, y: { stacked: true } }, datasets: { bar: { borderRadius: 3, maxBarThickness: 30 } } });

  chart($("#c_rev"), "bar", { labels: d.revenue.map(r => r.department), datasets: [{ label: "Revenue", data: d.revenue.map(r => r.revenue), backgroundColor: cs[6], borderRadius: 4, maxBarThickness: 22 }] },
    { indexAxis: "y", scales: { x: { ticks: { callback: v => "₹" + (v >= 1000 ? v / 1000 + "k" : v) } }, y: { grid: { display: false } } },
      plugins: { tooltip: { callbacks: { label: c => `${inr(c.parsed.x)} from ${d.revenue[c.dataIndex].visits} visits` } } } });

  chart($("#c_age"), "bar", { labels: d.ages.map(a => a.label), datasets: [{ label: "Patients", data: d.ages.map(a => a.n), backgroundColor: cs[0], borderRadius: 4, maxBarThickness: 40 }] });

  chart($("#c_doc"), "bar", { labels: d.top_docs.map(x => x.doctor.replace("Dr. ", "")), datasets: [
    { label: "Completed", data: d.top_docs.map(x => x.done), backgroundColor: cs[0] },
    { label: "Upcoming", data: d.top_docs.map(x => x.upcoming), backgroundColor: cs[2] }] },
    { indexAxis: "y", scales: { x: { stacked: true }, y: { stacked: true, grid: { display: false } } }, datasets: { bar: { borderRadius: 3, maxBarThickness: 22 } } });
};

PAGES.bedmap = async view => {
  const beds = await api("/api/bedmap");
  const c = s => beds.filter(b => b.status === s).length;
  view.innerHTML = `<div class="panel"><div class="panel-h"><h3>${beds.length} beds</h3><span class="grow"></span>
    <div class="legend"><span><i style="background:var(--free)"></i>Available ${c("Available")}</span><span><i style="background:var(--occ)"></i>Occupied ${c("Occupied")}</span><span><i style="background:var(--mnt)"></i>Maintenance ${c("Maintenance")}</span></div>
    <button class="btn primary" id="adm-top" style="margin-left:14px">${icon("plus")}Admit patient</button></div>
    <div class="panel-b" id="map" style="padding-top:20px">${wardMap(beds, true)}</div></div>`;
  wireBeds($("#map"), beds);
  $("#adm-top").onclick = () => admitDialog();
};

function tablePage(table, extra = {}) {
  return async view => {
    const d = await api("/api/t/" + table);
    const cfg = META.tables[table];
    view.innerHTML = `<div id="g"></div>`;
    const g = makeGrid($("#g", view), Object.assign({
      title: d.title, exportUrl: `/api/export/${table}.xlsx`, onChange: refresh,
      onNew: cfg ? () => openForm(table) : null, newLabel: cfg ? "New " + cfg.title.replace(/s$/, "").toLowerCase() : "",
      onEdit: cfg ? id => openForm(table, id) : null, onDelete: cfg ? id => removeRecord(table, id) : null,
    }, extra));
    g.set(d.columns, d.rows);
  };
}
PAGES.patients = tablePage("patients", { importTable: "patients" });
PAGES.doctors = tablePage("doctors", { importTable: "doctors" });
PAGES.appointments = tablePage("appointments");
PAGES.beds = tablePage("beds");
PAGES.departments = tablePage("departments");
PAGES.resources = tablePage("resources", { importTable: "resources", extra: [{ label: "Issue to patient", icon: "syringe", fn: () => issueDialog() }] });
PAGES.admissions = tablePage("admissions", {
  onNew: () => admitDialog(), newLabel: "Admit patient",
  rowAction: r => r[6] === "IN HOSPITAL" ? `<button class="btn sm" data-act="discharge" data-id="${r[0]}">Discharge</button>` : "",
  onAct: (a, id) => a === "discharge" && dischargeDialog(id),
});
PAGES.usage = tablePage("usage", { onNew: () => issueDialog(), newLabel: "Issue resource" });

/* ---------- analytics: pivot builder ---------- */
PAGES.analytics = async view => {
  const meta = await api("/api/analytics/meta");
  const S = { ds: store.get("an_ds") || "appointments", dim: null, dim2: "", mea: null, type: "bar" };
  if (!meta[S.ds]) S.ds = "appointments";
  const opt = (arr, v) => arr.map(o => `<option value="${o.key}" ${o.key === v ? "selected" : ""}>${esc(o.label)}</option>`).join("");

  view.innerHTML = `<div class="panel"><div class="builder">
      <div class="field"><label>Data</label><select class="in" id="ds">${Object.entries(meta).map(([k, v]) => `<option value="${k}" ${k === S.ds ? "selected" : ""}>${v.label}</option>`).join("")}</select></div>
      <div class="field"><label>Rows</label><select class="in" id="dim"></select></div>
      <div class="field"><label>Columns (optional)</label><select class="in" id="dim2"></select></div>
      <div class="field"><label>Values</label><select class="in" id="mea"></select></div></div>
    <div style="padding:0 18px 4px;display:flex;gap:12px;align-items:center;flex-wrap:wrap"><div class="seg" id="ct"></div><span class="grow" style="flex:1"></span>
      <button class="btn sm" id="csv">${icon("download")}Download CSV</button></div>
    <div class="panel-b"><div class="chart-box tall"><canvas id="cv"></canvas></div></div></div>
    <div class="panel" style="margin-top:16px"><div class="panel-h"><h3 id="pt">Pivot table</h3><span class="note">cell shading shows relative size, like Excel's colour scale</span></div>
    <div class="scroller" style="max-height:none;padding:12px 18px 18px" id="pv"></div></div>`;

  let last = null;
  const fillSelects = () => {
    const m = meta[S.ds];
    S.dim = m.dims.some(x => x.key === S.dim) ? S.dim : m.dims[0].key;
    S.mea = m.measures.some(x => x.key === S.mea) ? S.mea : m.measures[0].key;
    if (S.dim2 === S.dim || !m.dims.some(x => x.key === S.dim2)) S.dim2 = "";
    $("#dim").innerHTML = opt(m.dims, S.dim);
    $("#dim2").innerHTML = `<option value="">None</option>` + opt(m.dims.filter(x => x.key !== S.dim), S.dim2);
    $("#mea").innerHTML = opt(m.measures, S.mea);
  };
  const types = () => {
    const list = last && last.series.length > 1 ? ["bar", "stacked", "line"] : ["bar", "line", "pie", "doughnut"];
    if (!list.includes(S.type)) S.type = list[0];
    $("#ct").innerHTML = list.map(t => `<button data-t="${t}" class="${t === S.type ? "on" : ""}">${t === "doughnut" ? "Donut" : t[0].toUpperCase() + t.slice(1)}</button>`).join("");
    $$("#ct button").forEach(b => b.onclick = () => { S.type = b.dataset.t; draw(); types(); });
  };
  const draw = () => {
    killCharts();
    const cs = seriesColors(), multi = last.series.length > 1;
    const pie = S.type === "pie" || S.type === "doughnut";
    let data;
    if (pie) data = { labels: last.labels, datasets: [{ data: last.series[0].data, backgroundColor: last.labels.map((_, i) => cs[i % 8]), borderColor: cssv("--surface"), borderWidth: 2 }] };
    else data = { labels: last.labels, datasets: last.series.map((s, i) => ({ label: s.name, data: s.data, backgroundColor: cs[i % 8], borderColor: cs[i % 8], tension: .3, pointRadius: 3, borderRadius: S.type === "line" ? 0 : 3, maxBarThickness: 44 })) };
    const stacked = S.type === "stacked";
    chart($("#cv"), S.type === "stacked" ? "bar" : S.type, data, Object.assign({
      plugins: { legend: { display: multi || pie }, title: { display: false } },
    }, pie ? {} : { scales: { x: { stacked, title: { display: true, text: last.dim } }, y: { stacked, title: { display: true, text: last.measure } } } }));
  };
  const pivotTable = () => {
    const L = last, multi = L.series.length > 1, avg = /avg|average/i.test(L.measure);
    const all = L.series.flatMap(s => s.data), max = Math.max(1, ...all);
    const fmt = v => /Rs|cost|revenue|charges/i.test(L.measure) ? inr(v) : num(v);
    const shade = v => `background:color-mix(in srgb, var(--s1) ${Math.round(8 + 42 * v / max)}%, var(--surface))`;
    const rowTot = L.labels.map((_, i) => L.series.reduce((s, x) => s + x.data[i], 0));
    let h = `<table class="xl pv"><thead><tr><th class="rn" style="cursor:default">#</th><th style="cursor:default">${esc(L.dim)}</th>` +
      L.series.map(s => `<th class="num" style="cursor:default">${esc(multi ? s.name : L.measure)}</th>`).join("") + (multi && !avg ? `<th class="num" style="cursor:default">Total</th>` : "") + `</tr></thead><tbody>`;
    L.labels.forEach((l, i) => {
      h += `<tr><td class="rn">${i + 1}</td><td>${esc(l)}</td>` + L.series.map(s => `<td class="heat" style="${shade(s.data[i])}">${s.data[i] ? fmt(s.data[i]) : '<span class="faint">-</span>'}</td>`).join("") +
        (multi && !avg ? `<td class="num tot">${fmt(rowTot[i])}</td>` : "") + `</tr>`;
    });
    if (!avg) {
      h += `</tbody><tfoot><tr><td class="rn">Σ</td><td>Total</td>` + L.series.map(s => `<td class="num">${fmt(s.data.reduce((a, b) => a + b, 0))}</td>`).join("") +
        (multi ? `<td class="num">${fmt(rowTot.reduce((a, b) => a + b, 0))}</td>` : "") + `</tr></tfoot>`;
    } else h += `</tbody>`;
    $("#pv").innerHTML = h + `</table>`;
    $("#pt").textContent = `${L.measure} by ${L.dim.toLowerCase()}${L.dim2 ? " and " + L.dim2.toLowerCase() : ""}`;
  };
  const load = async () => {
    try {
      last = await api(`/api/analytics?dataset=${S.ds}&dim=${S.dim}&dim2=${S.dim2}&measure=${S.mea}`);
      if (/month|date/i.test(last.dim) && last.series.length === 1 && S.type === "bar" && !S.touched) S.type = "line";
      types(); draw(); pivotTable();
    } catch (e) { toast(e.message, true); }
  };
  fillSelects(); load();
  $("#ds").onchange = e => { S.ds = e.target.value; store.set("an_ds", S.ds); S.dim = S.mea = null; S.dim2 = ""; fillSelects(); load(); };
  $("#dim").onchange = e => { S.dim = e.target.value; fillSelects(); load(); };
  $("#dim2").onchange = e => { S.dim2 = e.target.value; load(); };
  $("#mea").onchange = e => { S.mea = e.target.value; load(); };
  $("#ct").addEventListener("click", () => { S.touched = true; });
  $("#csv").onclick = () => {
    const L = last, q = v => `"${String(v).replace(/"/g, '""')}"`;
    const rows = [[L.dim, ...L.series.map(s => s.name)], ...L.labels.map((l, i) => [l, ...L.series.map(s => s.data[i])])];
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob(["﻿" + rows.map(r => r.map(q).join(",")).join("\n")], { type: "text/csv" }));
    a.download = `pivot_${S.ds}.csv`; a.click();
  };
};

/* ---------- SQL lab ---------- */
PAGES.sqllab = async view => {
  const R = META.reports;
  view.innerHTML = `<div class="lab"><aside class="panel qlist">${R.map((r, i) => `<button class="qitem" data-i="${i}"><b>${esc(r.title)}</b><span>${esc(r.concept)}</span></button>`).join("")}</aside>
    <div><div class="panel" style="overflow:hidden"><textarea class="editor" id="sql" spellcheck="false" aria-label="SQL editor"></textarea>
      <div class="tools" style="border-top:1px solid var(--line-2);border-bottom:0"><button class="btn primary" id="run">${icon("play")}Run query</button><span class="faint">Ctrl + Enter</span>
      <span class="status" id="st"></span></div></div><div id="g" style="margin-top:16px"></div></div></div>`;
  const g = makeGrid($("#g", view), { title: "Query result", hideId: false, autoTotals: true, pageSize: 25,
    exportFn: async () => { try { await download("/api/export/query.xlsx", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ sql: $("#sql").value }) }, "query_result.xlsx"); toast("Excel file downloaded"); } catch (e) { toast(e.message, true); } } });
  let mutated = false;
  const run = async () => {
    const st = $("#st");
    try {
      const r = await api("/api/query", { json: { sql: $("#sql").value } });
      st.className = "status ok"; st.textContent = r.message;
      if (r.columns.length) g.set(r.columns, r.rows); else { g.set(["Result"], [[r.message]]); mutated = true; badges(); }
    } catch (e) { st.className = "status bad"; st.textContent = e.message; }
  };
  const pick = i => {
    $$(".qitem", view).forEach(b => b.classList.toggle("on", +b.dataset.i === i));
    $("#sql").value = R[i].sql; run();
  };
  $$(".qitem", view).forEach(b => b.onclick = () => pick(+b.dataset.i));
  $("#run").onclick = run;
  $("#sql").addEventListener("keydown", e => { if ((e.ctrlKey || e.metaKey) && e.key === "Enter") run(); });
  pick(2);
};

/* ---------- schema ---------- */
PAGES.schema = async view => {
  const s = await api("/api/schema");
  view.innerHTML = `<div class="schema">${s.map(t => `<section class="panel tcard"><h4>${t.name}<span>${t.rows} rows</span></h4>${t.columns.map(c =>
    `<div class="c"><code>${c.name}</code>${c.pk ? '<span class="tag pk">PK</span>' : ""}${c.fk ? `<span class="tag fk" title="references ${c.fk}">FK → ${c.fk.split(".")[0]}</span>` : ""}<span class="ty">${c.type}${c.notnull && !c.pk ? " · required" : ""}</span></div>`).join("")}</section>`).join("")}</div>
    <div class="panel" style="margin-top:16px"><div class="panel-h"><h3>Triggers keep the data consistent</h3></div><div class="panel-b"><div class="rows">
      <div class="row"><span class="pill ok">trg_admit</span><div><div class="t">After a patient is admitted</div><div class="s">The bed becomes Occupied automatically.</div></div></div>
      <div class="row"><span class="pill ok">trg_discharge</span><div><div class="t">After a discharge date is set</div><div class="s">The bed becomes Available automatically.</div></div></div>
      <div class="row"><span class="pill ok">trg_usage</span><div><div class="t">After a resource is issued to a patient</div><div class="s">Stock quantity reduces by the issued amount.</div></div></div>
      <div class="row"><span class="pill info">v_current_inpatients</span><div><div class="t">View</div><div class="s">Joins admissions, patients, beds and doctors for everyone still in hospital.</div></div></div></div></div></div>`;
};

/* ---------- boot ---------- */
(async function boot() {
  const saved = store.get("theme");
  document.documentElement.dataset.theme = saved || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  try { META = await api("/api/meta"); } catch (e) { $("#view").innerHTML = `<div class="panel panel-b empty"><b>Cannot reach the server</b>${esc(e.message)}</div>`; return; }
  buildSide(); topActions();
  window.addEventListener("hashchange", route);
  route();
})();
