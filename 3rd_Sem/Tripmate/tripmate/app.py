"""TripMate - Travel Planning and Booking System (Flask + SQLite)."""
import os
import sqlite3
from datetime import date, datetime
from functools import wraps

from flask import (Flask, g, jsonify, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("TRIPMATE_DB", os.path.join(BASE_DIR, "tripmate.db"))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS destinations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    location TEXT NOT NULL,
    category TEXT NOT NULL,
    price INTEGER NOT NULL,          -- per person, INR
    days INTEGER NOT NULL,           -- recommended stay
    rating REAL NOT NULL,
    image_url TEXT NOT NULL,
    description TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    title TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS trip_destinations (
    trip_id INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    destination_id INTEGER NOT NULL REFERENCES destinations(id),
    position INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (trip_id, destination_id)
);
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    destination_id INTEGER NOT NULL REFERENCES destinations(id),
    trip_id INTEGER REFERENCES trips(id) ON DELETE SET NULL,
    travel_date TEXT NOT NULL,
    travelers INTEGER NOT NULL,
    total_price INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'confirmed',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def img(keywords, lock):
    return f"https://loremflickr.com/800/520/{keywords}?lock={lock}"


SEED = [
    ("Goa Beaches", "Goa", "Beach", 12000, 4, 4.6, img("goa,beach", 1),
     "Golden sands, beach shacks, Portuguese-era churches and a lively nightlife scene."),
    ("Manali", "Himachal Pradesh", "Mountain", 14000, 5, 4.7, img("manali,mountains", 2),
     "Snow-capped peaks, Solang Valley adventure sports and cosy Himalayan cafes."),
    ("Jaipur", "Rajasthan", "Heritage", 9000, 3, 4.5, img("jaipur,palace", 3),
     "The Pink City: Amber Fort, City Palace, Hawa Mahal and vibrant bazaars."),
    ("Rishikesh", "Uttarakhand", "Adventure", 8000, 3, 4.6, img("rishikesh,river", 4),
     "River rafting, bungee jumping, yoga retreats and Ganga aarti at sunset."),
    ("Kerala Backwaters", "Kerala", "Nature", 16000, 5, 4.8, img("kerala,backwaters", 5),
     "Houseboat cruises through Alleppey's palm-lined canals and spice plantations."),
    ("Varanasi", "Uttar Pradesh", "Spiritual", 7000, 3, 4.4, img("varanasi,ghat", 6),
     "Ancient ghats, evening aarti and one of the world's oldest living cities."),
    ("Leh Ladakh", "Ladakh", "Adventure", 28000, 7, 4.9, img("ladakh,mountain", 7),
     "High-altitude passes, turquoise Pangong Lake and Buddhist monasteries."),
    ("Udaipur", "Rajasthan", "Heritage", 13000, 3, 4.7, img("udaipur,lake", 8),
     "The City of Lakes: Lake Pichola, royal palaces and sunset boat rides."),
    ("Andaman Islands", "Andaman & Nicobar", "Beach", 26000, 6, 4.8, img("andaman,island", 9),
     "Crystal-clear water, scuba diving at Havelock and the white sands of Radhanagar."),
    ("Darjeeling", "West Bengal", "Nature", 11000, 4, 4.5, img("darjeeling,tea", 10),
     "Tea gardens, the toy train and sunrise views of Kanchenjunga."),
    ("Hampi", "Karnataka", "Heritage", 6500, 2, 4.6, img("hampi,ruins", 11),
     "Boulder-strewn landscapes and the ruins of the Vijayanagara empire."),
    ("Amritsar", "Punjab", "Spiritual", 5500, 2, 4.7, img("amritsar,golden-temple", 12),
     "The Golden Temple, Wagah Border ceremony and legendary Punjabi food."),
    ("Spiti Valley", "Himachal Pradesh", "Adventure", 18000, 6, 4.8, img("spiti,valley", 13),
     "Cold-desert landscapes, ancient monasteries and starry skies."),
    ("Munnar", "Kerala", "Nature", 10500, 3, 4.5, img("munnar,tea", 14),
     "Rolling tea estates, misty hills and waterfalls in the Western Ghats."),
]

CATEGORIES = ["Beach", "Mountain", "Heritage", "Adventure", "Spiritual", "Nature"]


# --------------------------------------------------------------------------
# Database helpers
# --------------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript(SCHEMA)
    if db.execute("SELECT COUNT(*) FROM destinations").fetchone()[0] == 0:
        db.executemany(
            "INSERT INTO destinations (name, location, category, price, days, rating, image_url, description) "
            "VALUES (?,?,?,?,?,?,?,?)", SEED)
    db.commit()
    db.close()


# --------------------------------------------------------------------------
# Auth helpers
# --------------------------------------------------------------------------
def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return get_db().execute("SELECT id, name, email FROM users WHERE id = ?", (uid,)).fetchone()


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify(error="Please log in first."), 401
        return fn(*args, **kwargs)
    return wrapper


def page_login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login_page", next=request.path))
        return fn(*args, **kwargs)
    return wrapper


@app.context_processor
def inject_user():
    return {"user": current_user()}


def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/register")
def register_page():
    return render_template("register.html")


@app.route("/plan")
@page_login_required
def plan_page():
    return render_template("plan.html")


@app.route("/dashboard")
@page_login_required
def dashboard_page():
    return render_template("dashboard.html")


# --------------------------------------------------------------------------
# Auth API
# --------------------------------------------------------------------------
@app.post("/api/register")
def api_register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not name or not email or "@" not in email:
        return jsonify(error="Enter your name and a valid email."), 400
    if len(password) < 6:
        return jsonify(error="Password must be at least 6 characters."), 400
    db = get_db()
    if db.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
        return jsonify(error="An account with this email already exists."), 409
    cur = db.execute("INSERT INTO users (name, email, password_hash) VALUES (?,?,?)",
                     (name, email, generate_password_hash(password)))
    db.commit()
    session["user_id"] = cur.lastrowid
    return jsonify(id=cur.lastrowid, name=name, email=email), 201


@app.post("/api/login")
def api_login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    row = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not row or not check_password_hash(row["password_hash"], password):
        return jsonify(error="Invalid email or password."), 401
    session["user_id"] = row["id"]
    return jsonify(id=row["id"], name=row["name"], email=row["email"])


@app.post("/api/logout")
def api_logout():
    session.clear()
    return jsonify(ok=True)


@app.get("/api/me")
def api_me():
    u = current_user()
    if not u:
        return jsonify(error="Not logged in."), 401
    return jsonify(dict(u))


# --------------------------------------------------------------------------
# Destinations API
# --------------------------------------------------------------------------
@app.get("/api/categories")
def api_categories():
    row = get_db().execute("SELECT MAX(price) AS mx, MIN(price) AS mn FROM destinations").fetchone()
    return jsonify(categories=CATEGORIES, max_price=row["mx"], min_price=row["mn"])


@app.get("/api/destinations")
def api_destinations():
    sql, params = "SELECT * FROM destinations WHERE 1=1", []
    category = request.args.get("category")
    if category and category != "All":
        sql += " AND category = ?"
        params.append(category)
    max_price = request.args.get("max_price", type=int)
    if max_price is not None:
        sql += " AND price <= ?"
        params.append(max_price)
    min_price = request.args.get("min_price", type=int)
    if min_price is not None:
        sql += " AND price >= ?"
        params.append(min_price)
    q = (request.args.get("q") or "").strip()
    if q:
        sql += " AND (name LIKE ? OR location LIKE ? OR description LIKE ?)"
        params += [f"%{q}%"] * 3
    order = {"price_asc": "price ASC", "price_desc": "price DESC",
             "rating": "rating DESC"}.get(request.args.get("sort"), "rating DESC")
    sql += f" ORDER BY {order}, name"
    rows = get_db().execute(sql, params).fetchall()
    return jsonify([dict(r) for r in rows])


@app.get("/api/destinations/<int:dest_id>")
def api_destination(dest_id):
    row = get_db().execute("SELECT * FROM destinations WHERE id = ?", (dest_id,)).fetchone()
    if not row:
        return jsonify(error="Destination not found."), 404
    return jsonify(dict(row))


# --------------------------------------------------------------------------
# Trips API
# --------------------------------------------------------------------------
def trip_to_dict(db, trip):
    dests = db.execute(
        "SELECT d.* FROM trip_destinations td JOIN destinations d ON d.id = td.destination_id "
        "WHERE td.trip_id = ? ORDER BY td.position", (trip["id"],)).fetchall()
    d = dict(trip)
    d["destinations"] = [dict(x) for x in dests]
    d["estimated_cost_per_person"] = sum(x["price"] for x in dests)
    return d


@app.get("/api/trips")
@login_required
def api_trips_list():
    db = get_db()
    rows = db.execute("SELECT * FROM trips WHERE user_id = ? ORDER BY start_date",
                      (session["user_id"],)).fetchall()
    return jsonify([trip_to_dict(db, r) for r in rows])


@app.post("/api/trips")
@login_required
def api_trips_create():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    start, end = parse_date(data.get("start_date")), parse_date(data.get("end_date"))
    ids = data.get("destination_ids") or []
    if not title:
        return jsonify(error="Give your trip a title."), 400
    if not start or not end:
        return jsonify(error="Choose valid start and end dates."), 400
    if start < date.today():
        return jsonify(error="Start date cannot be in the past."), 400
    if end < start:
        return jsonify(error="End date cannot be before the start date."), 400
    if not isinstance(ids, list) or not ids:
        return jsonify(error="Select at least one destination."), 400
    db = get_db()
    ids = list(dict.fromkeys(int(i) for i in ids if str(i).isdigit()))
    found = db.execute(
        f"SELECT id FROM destinations WHERE id IN ({','.join('?' * len(ids))})", ids).fetchall()
    if len(found) != len(ids):
        return jsonify(error="One or more destinations do not exist."), 400
    cur = db.execute(
        "INSERT INTO trips (user_id, title, start_date, end_date, notes) VALUES (?,?,?,?,?)",
        (session["user_id"], title, start.isoformat(), end.isoformat(), (data.get("notes") or "").strip()))
    trip_id = cur.lastrowid
    db.executemany("INSERT INTO trip_destinations (trip_id, destination_id, position) VALUES (?,?,?)",
                   [(trip_id, did, pos) for pos, did in enumerate(ids)])
    db.commit()
    trip = db.execute("SELECT * FROM trips WHERE id = ?", (trip_id,)).fetchone()
    return jsonify(trip_to_dict(db, trip)), 201


@app.delete("/api/trips/<int:trip_id>")
@login_required
def api_trips_delete(trip_id):
    db = get_db()
    row = db.execute("SELECT 1 FROM trips WHERE id = ? AND user_id = ?",
                     (trip_id, session["user_id"])).fetchone()
    if not row:
        return jsonify(error="Trip not found."), 404
    db.execute("DELETE FROM trip_destinations WHERE trip_id = ?", (trip_id,))
    db.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
    db.commit()
    return jsonify(ok=True)


# --------------------------------------------------------------------------
# Bookings API
# --------------------------------------------------------------------------
BOOKING_SQL = (
    "SELECT b.*, d.name AS destination_name, d.location, d.image_url, t.title AS trip_title "
    "FROM bookings b JOIN destinations d ON d.id = b.destination_id "
    "LEFT JOIN trips t ON t.id = b.trip_id WHERE b.user_id = ? ")


@app.get("/api/bookings")
@login_required
def api_bookings_list():
    rows = get_db().execute(BOOKING_SQL + "ORDER BY b.travel_date DESC, b.id DESC",
                            (session["user_id"],)).fetchall()
    return jsonify([dict(r) for r in rows])


@app.post("/api/bookings")
@login_required
def api_bookings_create():
    data = request.get_json(silent=True) or {}
    db = get_db()
    dest = db.execute("SELECT * FROM destinations WHERE id = ?",
                      (data.get("destination_id"),)).fetchone()
    if not dest:
        return jsonify(error="Destination not found."), 404
    travel = parse_date(data.get("travel_date"))
    if not travel or travel < date.today():
        return jsonify(error="Choose a valid travel date (today or later)."), 400
    try:
        travelers = int(data.get("travelers"))
    except (TypeError, ValueError):
        travelers = 0
    if not 1 <= travelers <= 20:
        return jsonify(error="Travelers must be between 1 and 20."), 400
    trip_id = data.get("trip_id") or None
    if trip_id is not None and not db.execute(
            "SELECT 1 FROM trips WHERE id = ? AND user_id = ?", (trip_id, session["user_id"])).fetchone():
        return jsonify(error="Trip not found."), 404
    total = dest["price"] * travelers  # always computed server-side
    cur = db.execute(
        "INSERT INTO bookings (user_id, destination_id, trip_id, travel_date, travelers, total_price) "
        "VALUES (?,?,?,?,?,?)",
        (session["user_id"], dest["id"], trip_id, travel.isoformat(), travelers, total))
    db.commit()
    row = db.execute(BOOKING_SQL + "AND b.id = ?", (session["user_id"], cur.lastrowid)).fetchone()
    return jsonify(dict(row)), 201


@app.post("/api/bookings/<int:booking_id>/cancel")
@login_required
def api_bookings_cancel(booking_id):
    db = get_db()
    row = db.execute("SELECT * FROM bookings WHERE id = ? AND user_id = ?",
                     (booking_id, session["user_id"])).fetchone()
    if not row:
        return jsonify(error="Booking not found."), 404
    if row["status"] == "cancelled":
        return jsonify(error="Booking is already cancelled."), 400
    db.execute("UPDATE bookings SET status = 'cancelled' WHERE id = ?", (booking_id,))
    db.commit()
    return jsonify(ok=True, status="cancelled")


# --------------------------------------------------------------------------
# Dashboard API
# --------------------------------------------------------------------------
@app.get("/api/dashboard")
@login_required
def api_dashboard():
    db = get_db()
    uid, today = session["user_id"], date.today().isoformat()
    u = current_user()
    stats = db.execute(
        "SELECT "
        "SUM(CASE WHEN status='confirmed' THEN 1 ELSE 0 END) AS confirmed, "
        "SUM(CASE WHEN status='confirmed' AND travel_date >= ? THEN 1 ELSE 0 END) AS upcoming, "
        "COALESCE(SUM(CASE WHEN status='confirmed' THEN total_price END), 0) AS spent "
        "FROM bookings WHERE user_id = ?", (today, uid)).fetchone()
    trips = db.execute("SELECT * FROM trips WHERE user_id = ? ORDER BY start_date", (uid,)).fetchall()
    return jsonify(
        user=dict(u),
        stats={"trips": len(trips), "confirmed_bookings": stats["confirmed"] or 0,
               "upcoming_bookings": stats["upcoming"] or 0, "total_spent": stats["spent"]},
        trips=[trip_to_dict(db, t) for t in trips],
        bookings=[dict(r) for r in db.execute(
            BOOKING_SQL + "ORDER BY b.travel_date DESC, b.id DESC", (uid,)).fetchall()],
    )


init_db()

if __name__ == "__main__":
    app.run(debug=True)
