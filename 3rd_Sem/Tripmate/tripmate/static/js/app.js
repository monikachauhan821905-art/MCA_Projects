/* TripMate frontend: talks to the Flask JSON API. */
const LOGGED_IN = document.body.dataset.loggedIn === "true";
const PAGE = document.body.dataset.page;

const inr = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 });
const todayISO = () => new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 10);
const DESTINATION_PHOTOS = {
  1: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
  2: "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80",
  3: "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=1200&q=80",
  4: "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80",
  5: "https://images.unsplash.com/photo-1519046904884-53103b34b206?auto=format&fit=crop&w=1200&q=80",
  6: "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=1200&q=80",
  7: "https://images.unsplash.com/photo-1470770841072-f978cf4d019e?auto=format&fit=crop&w=1200&q=80",
  8: "https://images.unsplash.com/photo-1516483638261-f4dbaf036963?auto=format&fit=crop&w=1200&q=80",
  9: "https://images.unsplash.com/photo-1533105079780-92b9be482077?auto=format&fit=crop&w=1200&q=80",
  10: "https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=1200&q=80",
  11: "https://images.unsplash.com/photo-1567593810070-7a3d471af022?auto=format&fit=crop&w=1200&q=80",
  12: "https://images.unsplash.com/photo-1587474260584-136574528ed5?auto=format&fit=crop&w=1200&q=80",
  13: "https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=1200&q=80",
  14: "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80",
};

function destinationPhoto(id) {
  return DESTINATION_PHOTOS[id] || DESTINATION_PHOTOS[1];
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

async function api(url, options = {}) {
  const { body, ...rest } = options;
  const res = await fetch(url, {
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    ...rest,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  let data = {};
  try { data = await res.json(); } catch (_) { /* empty body */ }
  if (!res.ok) throw new Error(data.error || "Something went wrong. Please try again.");
  return data;
}

function toast(msg) {
  document.getElementById("tmToastBody").textContent = msg;
  bootstrap.Toast.getOrCreateInstance(document.getElementById("tmToast")).show();
}

function showError(el, msg) { el.textContent = msg; el.classList.remove("d-none"); }
function hideError(el) { el.classList.add("d-none"); }

function safeNext() {
  const n = new URLSearchParams(location.search).get("next");
  return n && n.startsWith("/") && !n.startsWith("//") ? n : "/dashboard";
}

function fmtDate(iso) {
  return new Date(iso + "T00:00:00").toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

function imgTag(src, alt, cls) {
  return `<img class="${cls}" src="${esc(src)}" alt="${esc(alt)}" loading="lazy" onerror="this.removeAttribute('src')">`;
}

/* ---------- shared: logout ---------- */
document.getElementById("logoutBtn")?.addEventListener("click", async () => {
  await api("/api/logout", { method: "POST" });
  location.href = "/";
});

/* ---------- auth pages ---------- */
function initAuth() {
  const err = document.getElementById("authError");
  const login = document.getElementById("loginForm");
  const reg = document.getElementById("registerForm");
  login?.addEventListener("submit", async e => {
    e.preventDefault(); hideError(err);
    try {
      await api("/api/login", { method: "POST", body: {
        email: document.getElementById("email").value, password: document.getElementById("password").value } });
      location.href = safeNext();
    } catch (ex) { showError(err, ex.message); }
  });
  reg?.addEventListener("submit", async e => {
    e.preventDefault(); hideError(err);
    try {
      await api("/api/register", { method: "POST", body: {
        name: document.getElementById("name").value,
        email: document.getElementById("email").value,
        password: document.getElementById("password").value } });
      location.href = "/dashboard";
    } catch (ex) { showError(err, ex.message); }
  });
}

/* ---------- home: destinations ---------- */
function initHome() {
  const grid = document.getElementById("destGrid");
  const empty = document.getElementById("emptyState");
  const count = document.getElementById("resultCount");
  const search = document.getElementById("searchBox");
  const cat = document.getElementById("categorySelect");
  const sort = document.getElementById("sortSelect");
  const range = document.getElementById("budgetRange");
  const label = document.getElementById("budgetLabel");
  let maxPrice = 0, minPrice = 0, destinations = [], timer;

  const modalEl = document.getElementById("bookModal");
  const modal = new bootstrap.Modal(modalEl);
  const form = document.getElementById("bookForm");
  const bookErr = document.getElementById("bookError");
  const dateIn = document.getElementById("bookDate");
  const travIn = document.getElementById("bookTravelers");
  const tripSel = document.getElementById("bookTrip");
  const totalEl = document.getElementById("bookTotal");
  let selected = null;

  function card(d) {
    return `<div class="col-sm-6 col-lg-4"><div class="card dest-card shadow-sm h-100">
      <div class="position-relative">${imgTag(destinationPhoto(d.id), d.name, "card-img-top dest-img")}
        <span class="badge badge-cat">${esc(d.category)}</span></div>
      <div class="card-body d-flex flex-column">
        <div class="d-flex justify-content-between align-items-start">
          <h3 class="h5 mb-0">${esc(d.name)}</h3>
          <span class="small"><i class="bi bi-star-fill text-warning"></i> ${d.rating.toFixed(1)}</span>
        </div>
        <div class="text-muted small mb-2"><i class="bi bi-geo-alt"></i> ${esc(d.location)} · ${d.days} days</div>
        <p class="small flex-grow-1">${esc(d.description)}</p>
        <div class="d-flex justify-content-between align-items-center">
          <div><span class="price">${inr.format(d.price)}</span><span class="text-muted small"> / person</span></div>
          <div class="btn-group btn-group-sm">
            <a class="btn btn-outline-secondary" href="/plan?dest=${d.id}">Plan</a>
            <button class="btn btn-primary" data-book="${d.id}">Book</button>
          </div>
        </div></div></div></div>`;
  }

  function render() {
    grid.innerHTML = destinations.map(card).join("");
    empty.classList.toggle("d-none", destinations.length > 0);
    count.textContent = `(${destinations.length})`;
  }

  function updateBudgetSlider() {
    const min = Number(range.min), max = Number(range.max), value = Number(range.value);
    const progress = max > min ? ((value - min) / (max - min)) * 100 : 100;
    range.style.setProperty("--range-progress", `${progress}%`);
  }

  async function load() {
    const p = new URLSearchParams({ category: cat.value, sort: sort.value, max_price: range.value });
    if (search.value.trim()) p.set("q", search.value.trim());
    try { destinations = await api("/api/destinations?" + p); render(); }
    catch (ex) { toast(ex.message); }
  }

  function updateTotal() {
    const n = parseInt(travIn.value, 10) || 0;
    totalEl.textContent = selected ? inr.format(selected.price * Math.max(n, 0)) : "";
  }

  grid.addEventListener("click", async e => {
    const btn = e.target.closest("[data-book]");
    if (!btn) return;
    if (!LOGGED_IN) { location.href = "/login?next=/"; return; }
    selected = destinations.find(d => d.id === Number(btn.dataset.book));
    document.getElementById("bookDestName").textContent = selected.name;
    hideError(bookErr);
    dateIn.min = todayISO(); dateIn.value = ""; travIn.value = 1;
    tripSel.innerHTML = '<option value="">None</option>';
    try {
      (await api("/api/trips")).forEach(t =>
        tripSel.insertAdjacentHTML("beforeend", `<option value="${t.id}">${esc(t.title)}</option>`));
    } catch (_) { /* optional */ }
    updateTotal(); modal.show();
  });

  travIn.addEventListener("input", updateTotal);
  form.addEventListener("submit", async e => {
    e.preventDefault(); hideError(bookErr);
    try {
      await api("/api/bookings", { method: "POST", body: {
        destination_id: selected.id, travel_date: dateIn.value,
        travelers: parseInt(travIn.value, 10), trip_id: tripSel.value ? Number(tripSel.value) : null } });
      modal.hide();
      toast("Booking confirmed! View it on your dashboard.");
    } catch (ex) { showError(bookErr, ex.message); }
  });

  [cat, sort].forEach(el => el.addEventListener("change", load));
  range.addEventListener("input", () => {
    label.textContent = inr.format(range.value);
    updateBudgetSlider();
    clearTimeout(timer); timer = setTimeout(load, 200);
  });
  search.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(load, 250); });
  document.getElementById("resetFilters").addEventListener("click", () => {
    search.value = ""; cat.value = "All"; sort.value = "rating"; range.value = maxPrice;
    label.textContent = inr.format(maxPrice); updateBudgetSlider(); load();
  });

  (async () => {
    try {
      const meta = await api("/api/categories");
      maxPrice = meta.max_price; minPrice = meta.min_price;
      meta.categories.forEach(c => cat.insertAdjacentHTML("beforeend", `<option>${esc(c)}</option>`));
      range.min = Math.floor(minPrice / 500) * 500; range.max = maxPrice; range.value = maxPrice;
      label.textContent = inr.format(maxPrice); updateBudgetSlider();
      load();
    } catch (ex) { toast(ex.message); }
  })();
}

/* ---------- trip list rendering (plan + dashboard) ---------- */
function tripCard(t) {
  const stops = t.destinations.map(d => `<span class="badge text-bg-light border">${esc(d.name)}</span>`).join(" ");
  return `<div class="card shadow-sm mb-3"><div class="card-body">
    <div class="d-flex justify-content-between">
      <h3 class="h6 mb-1">${esc(t.title)}</h3>
      <button class="btn btn-sm btn-outline-danger" data-del-trip="${t.id}" aria-label="Delete trip"><i class="bi bi-trash"></i></button>
    </div>
    <div class="small text-muted mb-2"><i class="bi bi-calendar-event"></i> ${fmtDate(t.start_date)} → ${fmtDate(t.end_date)}</div>
    <div class="mb-2">${stops}</div>
    ${t.notes ? `<p class="small mb-2">${esc(t.notes)}</p>` : ""}
    <div class="small">Est. cost: <strong>${inr.format(t.estimated_cost_per_person)}</strong> per person</div>
  </div></div>`;
}

function bindTripDelete(container, reload) {
  container.addEventListener("click", async e => {
    const btn = e.target.closest("[data-del-trip]");
    if (!btn || !confirm("Delete this trip plan?")) return;
    try { await api(`/api/trips/${btn.dataset.delTrip}`, { method: "DELETE" }); toast("Trip deleted."); reload(); }
    catch (ex) { toast(ex.message); }
  });
}

/* ---------- plan page ---------- */
function initPlan() {
  const picker = document.getElementById("destPicker");
  const list = document.getElementById("tripList");
  const est = document.getElementById("tripEstimate");
  const err = document.getElementById("tripError");
  const startIn = document.getElementById("tripStart");
  const endIn = document.getElementById("tripEnd");
  let dests = [];

  startIn.min = endIn.min = todayISO();
  startIn.addEventListener("change", () => { endIn.min = startIn.value || todayISO(); });

  const updateEstimate = () => {
    const ids = [...picker.querySelectorAll("input:checked")].map(i => Number(i.value));
    est.textContent = inr.format(dests.filter(d => ids.includes(d.id)).reduce((s, d) => s + d.price, 0));
  };
  picker.addEventListener("change", updateEstimate);

  async function loadTrips() {
    try {
      const trips = await api("/api/trips");
      list.innerHTML = trips.length ? trips.map(tripCard).join("")
        : '<p class="text-muted">No trip plans yet. Create your first one!</p>';
    } catch (ex) { toast(ex.message); }
  }
  bindTripDelete(list, loadTrips);

  document.getElementById("tripForm").addEventListener("submit", async e => {
    e.preventDefault(); hideError(err);
    try {
      await api("/api/trips", { method: "POST", body: {
        title: document.getElementById("tripTitle").value,
        start_date: startIn.value, end_date: endIn.value,
        notes: document.getElementById("tripNotes").value,
        destination_ids: [...picker.querySelectorAll("input:checked")].map(i => Number(i.value)) } });
      e.target.reset(); updateEstimate(); toast("Trip plan saved."); loadTrips();
    } catch (ex) { showError(err, ex.message); }
  });

  (async () => {
    try {
      dests = await api("/api/destinations?sort=price_asc");
      const pre = Number(new URLSearchParams(location.search).get("dest"));
      picker.innerHTML = dests.map(d => `<div class="form-check">
        <input class="form-check-input" type="checkbox" value="${d.id}" id="dp${d.id}" ${d.id === pre ? "checked" : ""}>
        <label class="form-check-label d-flex justify-content-between" for="dp${d.id}">
          <span>${esc(d.name)} <small class="text-muted">${esc(d.location)}</small></span>
          <small>${inr.format(d.price)}</small></label></div>`).join("");
      updateEstimate();
    } catch (ex) { toast(ex.message); }
    loadTrips();
  })();
}

/* ---------- dashboard ---------- */
function bookingRow(b) {
  const upcoming = b.status === "confirmed" && b.travel_date >= todayISO();
  return `<div class="card shadow-sm mb-3"><div class="card-body d-flex gap-3">
    ${imgTag(destinationPhoto(b.destination_id), b.destination_name, "booking-thumb flex-shrink-0")}
    <div class="flex-grow-1">
      <div class="d-flex justify-content-between align-items-start">
        <h3 class="h6 mb-1">${esc(b.destination_name)}</h3>
        <span class="badge status-${esc(b.status)} text-capitalize">${esc(b.status)}</span>
      </div>
      <div class="small text-muted">${esc(b.location)} · ${fmtDate(b.travel_date)} · ${b.travelers} traveler${b.travelers > 1 ? "s" : ""}</div>
      ${b.trip_title ? `<div class="small">Trip: ${esc(b.trip_title)}</div>` : ""}
      <div class="d-flex justify-content-between align-items-center mt-1">
        <strong>${inr.format(b.total_price)}</strong>
        ${upcoming ? `<button class="btn btn-sm btn-outline-danger" data-cancel="${b.id}">Cancel</button>` : ""}
      </div>
    </div></div></div>`;
}

function initDashboard() {
  const stats = document.getElementById("statCards");
  const bookings = document.getElementById("bookingList");
  const trips = document.getElementById("tripList");

  async function load() {
    try {
      const d = await api("/api/dashboard");
      const s = d.stats;
      stats.innerHTML = [
        ["Trip plans", s.trips], ["Upcoming bookings", s.upcoming_bookings],
        ["Confirmed bookings", s.confirmed_bookings], ["Total spent", inr.format(s.total_spent)],
      ].map(([l, v]) => `<div class="col-6 col-md-3"><div class="card stat-card shadow-sm"><div class="card-body">
        <div class="small text-muted">${l}</div><div class="value">${v}</div></div></div></div>`).join("");
      bookings.innerHTML = d.bookings.length ? d.bookings.map(bookingRow).join("")
        : '<p class="text-muted">No bookings yet. <a href="/">Browse destinations</a>.</p>';
      trips.innerHTML = d.trips.length ? d.trips.map(tripCard).join("")
        : '<p class="text-muted">No trip plans yet.</p>';
    } catch (ex) { toast(ex.message); }
  }

  bindTripDelete(trips, load);
  bookings.addEventListener("click", async e => {
    const btn = e.target.closest("[data-cancel]");
    if (!btn || !confirm("Cancel this booking?")) return;
    try { await api(`/api/bookings/${btn.dataset.cancel}/cancel`, { method: "POST" }); toast("Booking cancelled."); load(); }
    catch (ex) { toast(ex.message); }
  });
  load();
}

({ home: initHome, login: initAuth, register: initAuth, plan: initPlan, dashboard: initDashboard }[PAGE] || (() => {}))();
