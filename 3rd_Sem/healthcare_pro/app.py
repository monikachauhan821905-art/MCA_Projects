"""
Healthcare Resource & Patient Management System  -  "CareDesk"
---------------------------------------------------------------
Modern dashboard UI (runs in your browser, served locally by Flask)
DB   : SQLite  (DDL, DML, JOINs, subqueries, aggregates, triggers, views)
Excel: export any table / query / full workbook with native Excel charts,
       import patients & resources from .xlsx / .csv

Run :  python app.py        ->  opens http://127.0.0.1:5000
"""
import csv
import io
import os
import re
import sqlite3
import threading
import webbrowser
from datetime import date, datetime

from flask import Flask, jsonify, request, send_file, send_from_directory

import database as dbm

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, dbm.DB_FILE)

app = Flask(__name__, static_folder=os.path.join(BASE, "static"), static_url_path="/static")
conn = dbm.open_db(DB_PATH)
lock = threading.RLock()          # one shared SQLite connection -> serialise access


def today():
    return date.today().isoformat()


def rows(sql, args=()):
    cur = conn.execute(sql, args)
    cols = [d[0] for d in cur.description]
    return cols, [list(r) for r in cur.fetchall()]


def dicts(sql, args=()):
    cols, data = rows(sql, args)
    return [dict(zip(cols, r)) for r in data]


def one(sql, args=()):
    r = conn.execute(sql, args).fetchone()
    return r[0] if r else None


def friendly(e):
    msg = str(e)
    if "UNIQUE constraint failed: appointments.doctor_id" in msg:
        return "This doctor already has an appointment at that date and time."
    if "UNIQUE constraint failed: beds.ward" in msg:
        return "A bed with this ward and bed number already exists."
    if "UNIQUE constraint failed" in msg:
        return "That value already exists - it must be unique."
    if "FOREIGN KEY" in msg:
        return "Blocked: this record is linked to other records (appointments, admissions, usage...)."
    if "CHECK constraint failed" in msg:
        return "A value is outside the allowed range or list: " + msg.split("CHECK constraint failed:")[-1].strip()
    if "NOT NULL constraint failed" in msg:
        return "A required field is empty: " + msg.split("failed:")[-1].strip()
    return msg


def err(msg, code=400):
    return jsonify(error=msg), code


# =====================================================================
#  Table definitions (drive both the API and the generated forms)
# =====================================================================
BLOODS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

TABLES = {
    "patients": dict(
        title="Patients", pk="patient_id", icon="users",
        fields=[
            dict(col="name", label="Full name", kind="text", req=True),
            dict(col="age", label="Age", kind="number", min=0, max=120),
            dict(col="gender", label="Gender", kind="choice", choices=["Male", "Female", "Other"]),
            dict(col="phone", label="Phone", kind="text"),
            dict(col="blood_group", label="Blood group", kind="choice", choices=BLOODS),
            dict(col="address", label="Address", kind="text", wide=True),
        ],
        sql="SELECT patient_id AS ID, name AS Name, age AS Age, gender AS Gender, phone AS Phone, "
            "blood_group AS Blood, address AS Address, registered_on AS Registered "
            "FROM patients ORDER BY patient_id DESC"),
    "doctors": dict(
        title="Doctors", pk="doctor_id", icon="steth",
        fields=[
            dict(col="name", label="Name", kind="text", req=True),
            dict(col="specialization", label="Specialization", kind="text", req=True),
            dict(col="dept_id", label="Department", kind="fk", req=True, options="departments"),
            dict(col="phone", label="Phone", kind="text"),
            dict(col="fee", label="Consultation fee (Rs)", kind="number", min=0, default=500),
        ],
        sql="SELECT d.doctor_id AS ID, d.name AS Name, d.specialization AS Specialization, "
            "dep.name AS Department, d.phone AS Phone, d.fee AS Fee "
            "FROM doctors d JOIN departments dep ON dep.dept_id = d.dept_id ORDER BY d.doctor_id"),
    "appointments": dict(
        title="Appointments", pk="appt_id", icon="calendar",
        fields=[
            dict(col="patient_id", label="Patient", kind="fk", req=True, options="patients"),
            dict(col="doctor_id", label="Doctor", kind="fk", req=True, options="doctors"),
            dict(col="appt_date", label="Date", kind="date", req=True, default="@today"),
            dict(col="appt_time", label="Time", kind="time", req=True, default="10:00"),
            dict(col="reason", label="Reason", kind="text"),
            dict(col="status", label="Status", kind="choice", req=True, default="Scheduled",
                 choices=["Scheduled", "Completed", "Cancelled"]),
        ],
        sql="SELECT a.appt_id AS ID, a.appt_date AS Date, a.appt_time AS Time, p.name AS Patient, "
            "d.name AS Doctor, dep.name AS Department, a.reason AS Reason, a.status AS Status "
            "FROM appointments a JOIN patients p ON p.patient_id = a.patient_id "
            "JOIN doctors d ON d.doctor_id = a.doctor_id "
            "JOIN departments dep ON dep.dept_id = d.dept_id "
            "ORDER BY a.appt_date DESC, a.appt_time"),
    "beds": dict(
        title="Beds", pk="bed_id", icon="bed",
        fields=[
            dict(col="ward", label="Ward", kind="text", req=True),
            dict(col="bed_no", label="Bed no.", kind="text", req=True),
            dict(col="bed_type", label="Type", kind="choice", req=True, default="General",
                 choices=["General", "Private", "ICU"]),
            dict(col="dept_id", label="Department", kind="fk", options="departments"),
            dict(col="status", label="Status", kind="choice", req=True, default="Available",
                 choices=["Available", "Occupied", "Maintenance"]),
            dict(col="daily_charge", label="Daily charge (Rs)", kind="number", req=True, min=0),
        ],
        sql="SELECT b.bed_id AS ID, b.ward AS Ward, b.bed_no AS Bed, b.bed_type AS Type, "
            "dep.name AS Department, b.status AS Status, b.daily_charge AS Charge "
            "FROM beds b LEFT JOIN departments dep ON dep.dept_id = b.dept_id ORDER BY b.bed_id"),
    "resources": dict(
        title="Resources", pk="res_id", icon="box",
        fields=[
            dict(col="name", label="Name", kind="text", req=True),
            dict(col="category", label="Category", kind="choice", req=True,
                 choices=["Equipment", "Medicine", "Consumable"]),
            dict(col="quantity", label="Quantity in stock", kind="number", req=True, min=0),
            dict(col="min_level", label="Minimum level", kind="number", req=True, min=0, default=10),
            dict(col="unit_cost", label="Unit cost (Rs)", kind="number", min=0, default=0),
            dict(col="dept_id", label="Department", kind="fk", options="departments"),
        ],
        sql="SELECT r.res_id AS ID, r.name AS Name, r.category AS Category, r.quantity AS Qty, "
            "r.min_level AS Min, r.unit_cost AS UnitCost, dep.name AS Department, "
            "CASE WHEN r.quantity <= r.min_level THEN 'LOW' ELSE 'OK' END AS Stock "
            "FROM resources r LEFT JOIN departments dep ON dep.dept_id = r.dept_id ORDER BY r.res_id"),
    "departments": dict(
        title="Departments", pk="dept_id", icon="building",
        fields=[
            dict(col="name", label="Name", kind="text", req=True),
            dict(col="floor", label="Floor", kind="number", min=0),
        ],
        sql="SELECT dept_id AS ID, name AS Name, floor AS Floor FROM departments ORDER BY dept_id"),
}

# read-only lists (their own endpoints for write actions)
LISTS = {
    "admissions": ("Admissions",
                   """SELECT ad.adm_id AS ID, p.name AS Patient, b.ward || '-' || b.bed_no AS Bed,
        b.bed_type AS Type, d.name AS Doctor, ad.admit_date AS Admitted,
        COALESCE(ad.discharge_date, 'IN HOSPITAL') AS Discharged,
        CAST(julianday(COALESCE(ad.discharge_date, date('now','localtime'))) - julianday(ad.admit_date) AS INTEGER) + 1 AS Days,
        (CAST(julianday(COALESCE(ad.discharge_date, date('now','localtime'))) - julianday(ad.admit_date) AS INTEGER) + 1)
            * b.daily_charge AS BedBill,
        ad.diagnosis AS Diagnosis
      FROM admissions ad
      JOIN patients p ON p.patient_id = ad.patient_id
      JOIN beds b     ON b.bed_id     = ad.bed_id
      JOIN doctors d  ON d.doctor_id  = ad.doctor_id
      ORDER BY (ad.discharge_date IS NOT NULL), ad.adm_id DESC"""),
    "usage": ("Resource issues",
              """SELECT u.usage_id AS ID, u.used_on AS Date, r.name AS Resource,
        r.category AS Category, p.name AS Patient, u.qty AS Qty, u.qty * r.unit_cost AS Cost
      FROM resource_usage u
      JOIN resources r ON r.res_id = u.res_id
      JOIN patients p  ON p.patient_id = u.patient_id
      ORDER BY u.usage_id DESC"""),
}

OPTIONS = {
    "departments": "SELECT dept_id, name FROM departments ORDER BY name",
    "patients": "SELECT patient_id, name || '  (#' || patient_id || ')' FROM patients ORDER BY name",
    "doctors": "SELECT doctor_id, name || ' - ' || specialization FROM doctors ORDER BY name",
    "free_beds": "SELECT bed_id, ward || '-' || bed_no || '  ' || bed_type || ', Rs ' || CAST(daily_charge AS INTEGER) || '/day' "
                 "FROM beds WHERE status='Available' ORDER BY ward, bed_no",
    "stock": "SELECT res_id, name || '  [stock ' || quantity || ']' FROM resources WHERE quantity > 0 ORDER BY name",
}


# =====================================================================
#  Pages + meta
# =====================================================================
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/meta")
def meta():
    return jsonify(
        tables={k: {kk: vv for kk, vv in v.items() if kk != "sql"} for k, v in TABLES.items()},
        today=today(), sqlite=sqlite3.sqlite_version,
        reports=[dict(i=i, title=t, concept=c, sql=s) for i, (t, c, s) in enumerate(dbm.REPORTS)],
    )


@app.get("/api/options/<key>")
def options(key):
    if key not in OPTIONS:
        return err("unknown option list", 404)
    with lock:
        return jsonify([dict(id=r[0], label=r[1]) for r in conn.execute(OPTIONS[key])])


# =====================================================================
#  Generic CRUD
# =====================================================================
def clean_values(cfg, data):
    out = []
    for f in cfg["fields"]:
        v = data.get(f["col"])
        if isinstance(v, str):
            v = v.strip()
        if v in ("", None):
            if f.get("req"):
                raise ValueError(f"'{f['label']}' is required.")
            v = None
        elif f["kind"] == "number":
            try:
                v = float(v)
            except (TypeError, ValueError):
                raise ValueError(f"'{f['label']}' must be a number.")
            if v == int(v) and f["col"] not in ("fee", "unit_cost", "daily_charge"):
                v = int(v)
        elif f["kind"] == "fk":
            v = int(v)
        out.append(v)
    return out


@app.get("/api/t/<table>")
def list_table(table):
    if table in TABLES:
        sql, title = TABLES[table]["sql"], TABLES[table]["title"]
    elif table in LISTS:
        title, sql = LISTS[table]
    else:
        return err("unknown table", 404)
    with lock:
        cols, data = rows(sql)
    return jsonify(title=title, columns=cols, rows=data)


@app.get("/api/t/<table>/<int:rid>")
def get_record(table, rid):
    cfg = TABLES.get(table)
    if not cfg:
        return err("unknown table", 404)
    with lock:
        cols = ", ".join(f["col"] for f in cfg["fields"])
        cur = conn.execute(f"SELECT {cols} FROM {table} WHERE {cfg['pk']}=?", (rid,))
        r = cur.fetchone()
    if not r:
        return err("record not found", 404)
    return jsonify(dict(zip([f["col"] for f in cfg["fields"]], r)))


@app.post("/api/t/<table>")
def add_record(table):
    cfg = TABLES.get(table)
    if not cfg:
        return err("unknown table", 404)
    with lock:
        try:
            vals = clean_values(cfg, request.get_json())
            cols = [f["col"] for f in cfg["fields"]]
            cur = conn.execute(f"INSERT INTO {table}({', '.join(cols)}) VALUES({', '.join('?' * len(cols))})", vals)
            conn.commit()
        except ValueError as e:
            conn.rollback()
            return err(str(e))
        except sqlite3.Error as e:
            conn.rollback()
            return err(friendly(e))
    return jsonify(ok=True, id=cur.lastrowid)


@app.put("/api/t/<table>/<int:rid>")
def update_record(table, rid):
    cfg = TABLES.get(table)
    if not cfg:
        return err("unknown table", 404)
    with lock:
        try:
            vals = clean_values(cfg, request.get_json())
            sets = ", ".join(f"{f['col']}=?" for f in cfg["fields"])
            conn.execute(f"UPDATE {table} SET {sets} WHERE {cfg['pk']}=?", vals + [rid])
            conn.commit()
        except ValueError as e:
            conn.rollback()
            return err(str(e))
        except sqlite3.Error as e:
            conn.rollback()
            return err(friendly(e))
    return jsonify(ok=True)


@app.delete("/api/t/<table>/<int:rid>")
def delete_record(table, rid):
    cfg = TABLES.get(table)
    if not cfg:
        return err("unknown table", 404)
    with lock:
        try:
            conn.execute(f"DELETE FROM {table} WHERE {cfg['pk']}=?", (rid,))
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            return err(friendly(e))
    return jsonify(ok=True)


# =====================================================================
#  Admissions / discharge / issue resource  (these fire the triggers)
# =====================================================================
@app.post("/api/admit")
def admit():
    d = request.get_json()
    try:
        pid, bid, did = int(d.get("patient_id")), int(d.get("bed_id")), int(d.get("doctor_id"))
    except (TypeError, ValueError):
        return err("Choose a patient, a bed and a doctor.")
    with lock:
        if one("SELECT 1 FROM admissions WHERE patient_id=? AND discharge_date IS NULL", (pid,)):
            return err("This patient is already admitted. Discharge them first.")
        if one("SELECT status FROM beds WHERE bed_id=?", (bid,)) != "Available":
            return err("That bed is not available.")
        try:
            conn.execute("INSERT INTO admissions(patient_id,bed_id,doctor_id,admit_date,diagnosis) VALUES(?,?,?,?,?)",
                         (pid, bid, did, today(), (d.get("diagnosis") or "").strip() or None))
            conn.commit()        # trigger trg_admit marks the bed Occupied
        except sqlite3.Error as e:
            conn.rollback()
            return err(friendly(e))
    return jsonify(ok=True)


@app.get("/api/discharge/<int:adm_id>")
def discharge_preview(adm_id):
    with lock:
        r = conn.execute(
            """SELECT ad.discharge_date, p.name, b.ward||'-'||b.bed_no, ad.admit_date,
                      CAST(julianday(?) - julianday(ad.admit_date) AS INTEGER) + 1, b.daily_charge
               FROM admissions ad JOIN patients p ON p.patient_id = ad.patient_id
               JOIN beds b ON b.bed_id = ad.bed_id WHERE ad.adm_id = ?""", (today(), adm_id)).fetchone()
    if not r:
        return err("admission not found", 404)
    return jsonify(already=bool(r[0]), patient=r[1], bed=r[2], admitted=r[3], days=r[4],
                   charge=r[5], bill=r[4] * r[5])


@app.post("/api/discharge/<int:adm_id>")
def discharge(adm_id):
    with lock:
        if one("SELECT discharge_date FROM admissions WHERE adm_id=?", (adm_id,)) is not None:
            return err("This patient is already discharged.")
        conn.execute("UPDATE admissions SET discharge_date=? WHERE adm_id=?", (today(), adm_id))
        conn.commit()            # trigger trg_discharge frees the bed
    return jsonify(ok=True)


@app.post("/api/issue")
def issue():
    d = request.get_json()
    try:
        rid, pid, q = int(d.get("res_id")), int(d.get("patient_id")), int(d.get("qty"))
        assert q > 0
    except (TypeError, ValueError, AssertionError):
        return err("Choose a resource and a patient, and enter a quantity above zero.")
    with lock:
        stock = one("SELECT quantity FROM resources WHERE res_id=?", (rid,))
        if stock is None or q > stock:
            return err(f"Only {stock or 0} unit(s) in stock.")
        try:
            conn.execute("INSERT INTO resource_usage(res_id,patient_id,qty,used_on) VALUES(?,?,?,?)",
                         (rid, pid, q, today()))
            conn.commit()        # trigger trg_usage reduces stock
        except sqlite3.Error as e:
            conn.rollback()
            return err(friendly(e))
    return jsonify(ok=True)


# =====================================================================
#  Dashboard data
# =====================================================================
def dashboard_data():
    T = "date('now','localtime')"
    k = {}
    k["patients"] = one("SELECT COUNT(*) FROM patients")
    k["patients_week"] = one(f"SELECT COUNT(*) FROM patients WHERE registered_on >= date('now','localtime','-7 day')")
    k["doctors"] = one("SELECT COUNT(*) FROM doctors")
    k["appt_today"] = one(f"SELECT COUNT(*) FROM appointments WHERE appt_date={T} AND status!='Cancelled'")
    k["appt_today_done"] = one(f"SELECT COUNT(*) FROM appointments WHERE appt_date={T} AND status='Completed'")
    k["beds_total"] = one("SELECT COUNT(*) FROM beds")
    k["beds_free"] = one("SELECT COUNT(*) FROM beds WHERE status='Available'")
    k["beds_occ"] = one("SELECT COUNT(*) FROM beds WHERE status='Occupied'")
    k["beds_mnt"] = one("SELECT COUNT(*) FROM beds WHERE status='Maintenance'")
    k["admitted"] = one("SELECT COUNT(*) FROM admissions WHERE discharge_date IS NULL")
    k["low_stock"] = one("SELECT COUNT(*) FROM resources WHERE quantity <= min_level")
    k["revenue_30"] = one(f"""SELECT COALESCE(SUM(d.fee),0) FROM appointments a JOIN doctors d ON d.doctor_id=a.doctor_id
                              WHERE a.status='Completed' AND a.appt_date >= date('now','localtime','-30 day')""")
    k["bed_bill_running"] = one(f"""SELECT COALESCE(SUM((CAST(julianday({T}) - julianday(ad.admit_date) AS INTEGER)+1)*b.daily_charge),0)
                                   FROM admissions ad JOIN beds b ON b.bed_id=ad.bed_id WHERE ad.discharge_date IS NULL""")

    # last 14 days + next 3 : appointments by status
    days = dicts(f"""WITH RECURSIVE n(i) AS (SELECT -13 UNION ALL SELECT i+1 FROM n WHERE i < 3)
        SELECT date('now','localtime', i||' day') AS day,
          (SELECT COUNT(*) FROM appointments WHERE appt_date=date('now','localtime', i||' day') AND status='Completed') AS Completed,
          (SELECT COUNT(*) FROM appointments WHERE appt_date=date('now','localtime', i||' day') AND status='Scheduled') AS Scheduled,
          (SELECT COUNT(*) FROM appointments WHERE appt_date=date('now','localtime', i||' day') AND status='Cancelled') AS Cancelled
        FROM n""")
    occ = dicts(dbm.REPORTS[2][2])
    rev = dicts("""SELECT dep.name AS department, SUM(d.fee) AS revenue, COUNT(*) AS visits
                   FROM appointments a JOIN doctors d ON d.doctor_id=a.doctor_id
                   JOIN departments dep ON dep.dept_id=d.dept_id
                   WHERE a.status='Completed' GROUP BY dep.dept_id ORDER BY revenue DESC""")
    gender = dicts("SELECT COALESCE(gender,'Unknown') AS label, COUNT(*) AS n FROM patients GROUP BY gender ORDER BY n DESC")
    ages = dicts("""SELECT CASE WHEN age<=12 THEN '0-12' WHEN age<=19 THEN '13-19' WHEN age<=39 THEN '20-39'
                                 WHEN age<=59 THEN '40-59' ELSE '60+' END AS label, COUNT(*) AS n
                    FROM patients GROUP BY label""")
    order = ["0-12", "13-19", "20-39", "40-59", "60+"]
    ages.sort(key=lambda r: order.index(r["label"]))
    stock = dicts("""SELECT name, quantity, min_level, ROUND(100.0*quantity/NULLIF(min_level,0)) AS pct
                     FROM resources ORDER BY quantity*1.0/NULLIF(min_level,0) ASC LIMIT 8""")
    top_docs = dicts(f"""SELECT d.name AS doctor, d.specialization,
                         SUM(a.status='Completed') AS done, SUM(a.status='Scheduled') AS upcoming
                         FROM doctors d LEFT JOIN appointments a ON a.doctor_id=d.doctor_id
                         GROUP BY d.doctor_id ORDER BY done DESC LIMIT 6""")
    schedule = dicts(f"""SELECT a.appt_time AS time, p.name AS patient, d.name AS doctor, a.reason, a.status
                         FROM appointments a JOIN patients p ON p.patient_id=a.patient_id
                         JOIN doctors d ON d.doctor_id=a.doctor_id
                         WHERE a.appt_date={T} ORDER BY a.appt_time""")
    inpatients = dicts(f"""SELECT p.name AS patient, b.ward||'-'||b.bed_no AS bed, d.name AS doctor, ad.diagnosis,
                           CAST(julianday({T})-julianday(ad.admit_date) AS INTEGER)+1 AS days
                           FROM admissions ad JOIN patients p ON p.patient_id=ad.patient_id
                           JOIN beds b ON b.bed_id=ad.bed_id JOIN doctors d ON d.doctor_id=ad.doctor_id
                           WHERE ad.discharge_date IS NULL ORDER BY days DESC LIMIT 6""")
    return dict(kpi=k, days=days, occupancy=occ, revenue=rev, gender=gender, ages=ages, stock=stock,
                top_docs=top_docs, schedule=schedule, inpatients=inpatients)


@app.get("/api/dashboard")
def dashboard():
    with lock:
        return jsonify(dashboard_data())


@app.get("/api/bedmap")
def bedmap():
    with lock:
        beds = dicts(f"""SELECT b.bed_id, b.ward, b.bed_no, b.bed_type, b.status, b.daily_charge,
                  dep.name AS department,
                  p.name AS patient, ad.adm_id, ad.diagnosis, d.name AS doctor,
                  CAST(julianday(date('now','localtime')) - julianday(ad.admit_date) AS INTEGER) + 1 AS days
               FROM beds b
               LEFT JOIN departments dep ON dep.dept_id=b.dept_id
               LEFT JOIN admissions ad ON ad.bed_id=b.bed_id AND ad.discharge_date IS NULL
               LEFT JOIN patients p ON p.patient_id=ad.patient_id
               LEFT JOIN doctors d ON d.doctor_id=ad.doctor_id
               ORDER BY b.ward, b.bed_no""")
    return jsonify(beds)


# =====================================================================
#  Analytics (Excel pivot-table idea): choose rows, optional columns, measure, chart
#  Everything comes from white-lists, so no user text ever reaches the SQL.
# =====================================================================
AGE_GRP = ("CASE WHEN p.age<=12 THEN '0-12' WHEN p.age<=19 THEN '13-19' WHEN p.age<=39 THEN '20-39' "
           "WHEN p.age<=59 THEN '40-59' ELSE '60+' END")
WEEKDAY = ("CASE strftime('%w', {c}) WHEN '0' THEN 'Sun' WHEN '1' THEN 'Mon' WHEN '2' THEN 'Tue' "
           "WHEN '3' THEN 'Wed' WHEN '4' THEN 'Thu' WHEN '5' THEN 'Fri' ELSE 'Sat' END")
ORD_AGE = ["0-12", "13-19", "20-39", "40-59", "60+"]
ORD_DAY = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

DATASETS = {
    "appointments": dict(
        label="Appointments",
        base="""SELECT a.appt_date AS date, strftime('%Y-%m', a.appt_date) AS month, {wd} AS weekday,
                       a.status, d.name AS doctor, dep.name AS department, d.specialization,
                       p.gender, {age} AS age_group, d.fee AS fee
                FROM appointments a JOIN patients p ON p.patient_id=a.patient_id
                JOIN doctors d ON d.doctor_id=a.doctor_id JOIN departments dep ON dep.dept_id=d.dept_id""".format(
            wd=WEEKDAY.format(c="a.appt_date"), age=AGE_GRP),
        dims={"department": ("Department", None), "doctor": ("Doctor", None), "status": ("Status", None),
              "specialization": ("Specialization", None), "weekday": ("Weekday", ORD_DAY),
              "month": ("Month", "sort"), "date": ("Date", "sort"), "gender": ("Patient gender", None),
              "age_group": ("Patient age group", ORD_AGE)},
        measures={"count": ("Number of appointments", "COUNT(*)"),
                  "revenue": ("Consultation revenue (Rs)", "SUM(CASE WHEN status='Completed' THEN fee ELSE 0 END)"),
                  "avg_fee": ("Average fee (Rs)", "ROUND(AVG(fee),0)")}),
    "admissions": dict(
        label="Admissions",
        base="""SELECT dep.name AS department, b.ward, b.bed_type, ad.diagnosis, d.name AS doctor,
                       strftime('%Y-%m', ad.admit_date) AS month, p.gender, {age} AS age_group,
                       CASE WHEN ad.discharge_date IS NULL THEN 'In hospital' ELSE 'Discharged' END AS state,
                       CAST(julianday(COALESCE(ad.discharge_date, date('now','localtime'))) - julianday(ad.admit_date) AS INTEGER)+1 AS days,
                       (CAST(julianday(COALESCE(ad.discharge_date, date('now','localtime'))) - julianday(ad.admit_date) AS INTEGER)+1)*b.daily_charge AS bill
                FROM admissions ad JOIN patients p ON p.patient_id=ad.patient_id
                JOIN beds b ON b.bed_id=ad.bed_id JOIN doctors d ON d.doctor_id=ad.doctor_id
                JOIN departments dep ON dep.dept_id=d.dept_id""".format(age=AGE_GRP),
        dims={"department": ("Department", None), "ward": ("Ward", None), "bed_type": ("Bed type", None),
              "diagnosis": ("Diagnosis", None), "doctor": ("Doctor", None), "month": ("Admission month", "sort"),
              "state": ("Current state", None), "gender": ("Patient gender", None),
              "age_group": ("Patient age group", ORD_AGE)},
        measures={"count": ("Number of admissions", "COUNT(*)"),
                  "avg_days": ("Average stay (days)", "ROUND(AVG(days),1)"),
                  "bill": ("Bed charges (Rs)", "SUM(bill)")}),
    "usage": dict(
        label="Resource usage",
        base="""SELECT r.name AS resource, r.category, dep.name AS department,
                       strftime('%Y-%m', u.used_on) AS month, u.used_on AS date, p.gender,
                       u.qty, u.qty*r.unit_cost AS cost
                FROM resource_usage u JOIN resources r ON r.res_id=u.res_id
                JOIN departments dep ON dep.dept_id=r.dept_id JOIN patients p ON p.patient_id=u.patient_id""",
        dims={"resource": ("Resource", None), "category": ("Category", None), "department": ("Department", None),
              "month": ("Month", "sort"), "date": ("Date", "sort"), "gender": ("Patient gender", None)},
        measures={"issues": ("Number of issues", "COUNT(*)"), "units": ("Units used", "SUM(qty)"),
                  "cost": ("Cost (Rs)", "SUM(cost)")}),
    "patients": dict(
        label="Patients",
        base=f"""SELECT COALESCE(p.gender,'Unknown') AS gender, COALESCE(p.blood_group,'Unknown') AS blood_group,
                        {AGE_GRP} AS age_group, strftime('%Y-%m', p.registered_on) AS month, p.age
                 FROM patients p""",
        dims={"gender": ("Gender", None), "blood_group": ("Blood group", None),
              "age_group": ("Age group", ORD_AGE), "month": ("Registration month", "sort")},
        measures={"count": ("Number of patients", "COUNT(*)"), "avg_age": ("Average age", "ROUND(AVG(age),1)")}),
}


@app.get("/api/analytics/meta")
def analytics_meta():
    return jsonify({k: dict(label=v["label"],
                            dims=[dict(key=a, label=b[0]) for a, b in v["dims"].items()],
                            measures=[dict(key=a, label=b[0]) for a, b in v["measures"].items()])
                    for k, v in DATASETS.items()})


def _order(labels, rule, vals):
    if isinstance(rule, list):
        return sorted(labels, key=lambda l: rule.index(l) if l in rule else 99)
    if rule == "sort":
        return sorted(labels, key=lambda l: str(l))
    return sorted(labels, key=lambda l: -vals.get(l, 0))


@app.get("/api/analytics")
def analytics():
    ds = DATASETS.get(request.args.get("dataset", ""))
    if not ds:
        return err("unknown dataset")
    dim, dim2, mea = request.args.get("dim"), request.args.get("dim2") or None, request.args.get("measure")
    if dim not in ds["dims"] or mea not in ds["measures"] or (dim2 and dim2 not in ds["dims"]) or dim == dim2:
        return err("Pick a valid row field, measure and (optional) column field that differ from each other.")
    mexpr = ds["measures"][mea][1]
    with lock:
        if not dim2:
            r = conn.execute(f"SELECT COALESCE({dim},'-'), {mexpr} FROM ({ds['base']}) GROUP BY 1").fetchall()
            vals = {a: (b or 0) for a, b in r}
            labels = _order(list(vals), ds["dims"][dim][1], vals)
            if ds["dims"][dim][1] is None and len(labels) > 12 and ds["dims"][dim][1] != "sort":
                pass
            return jsonify(labels=labels, series=[dict(name=ds["measures"][mea][0], data=[vals[l] for l in labels])],
                           measure=ds["measures"][mea][0], dim=ds["dims"][dim][0], dim2=None)
        r = conn.execute(f"SELECT COALESCE({dim},'-'), COALESCE({dim2},'-'), {mexpr} "
                         f"FROM ({ds['base']}) GROUP BY 1,2").fetchall()
    cells, rtot, ctot = {}, {}, {}
    for a, b, v in r:
        cells[(a, b)] = v or 0
        rtot[a] = rtot.get(a, 0) + (v or 0)
        ctot[b] = ctot.get(b, 0) + (v or 0)
    cols = _order(list(ctot), ds["dims"][dim2][1], ctot)
    if len(cols) > 7 and ds["dims"][dim2][1] != "sort":      # fold the tail into "Other"
        keep = cols[:7]
        folded = {}
        for (a, b), v in cells.items():
            key = (a, b if b in keep else "Other")
            folded[key] = folded.get(key, 0) + v
        cells, cols = folded, keep + ["Other"]
    labels = _order(list(rtot), ds["dims"][dim][1], rtot)
    series = [dict(name=str(c), data=[cells.get((l, c), 0) for l in labels]) for c in cols]
    return jsonify(labels=labels, series=series, measure=ds["measures"][mea][0],
                   dim=ds["dims"][dim][0], dim2=ds["dims"][dim2][0])


# =====================================================================
#  SQL lab
# =====================================================================
@app.post("/api/query")
def run_query():
    sql = (request.get_json().get("sql") or "").strip().rstrip(";")
    if not sql:
        return err("Type a SQL statement first.")
    if ";" in sql:
        return err("Run one statement at a time.")
    with lock:
        try:
            cur = conn.execute(sql)
            if cur.description:
                cols = [d[0] for d in cur.description]
                data = [list(r) for r in cur.fetchall()]
                return jsonify(columns=cols, rows=data, message=f"{len(data)} row(s) returned")
            conn.commit()
            return jsonify(columns=[], rows=[], changed=True, message=f"OK - {cur.rowcount} row(s) affected")
        except sqlite3.Error as e:
            conn.rollback()
            return err(friendly(e))


@app.get("/api/schema")
def schema():
    out = []
    with lock:
        for (name,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
            cols = [dict(name=c[1], type=c[2], pk=bool(c[5]), notnull=bool(c[3]))
                    for c in conn.execute(f"PRAGMA table_info({name})")]
            fks = {f[3]: f"{f[2]}.{f[4]}" for f in conn.execute(f"PRAGMA foreign_key_list({name})")}
            for c in cols:
                c["fk"] = fks.get(c["name"])
            out.append(dict(name=name, columns=cols, rows=one(f"SELECT COUNT(*) FROM {name}")))
    return jsonify(out)


# =====================================================================
#  Excel export  (openpyxl, with formatting + native Excel charts)
# =====================================================================
from openpyxl import Workbook, load_workbook
from openpyxl.chart import BarChart, LineChart, PieChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.formatting.rule import DataBarRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

HEAD_FILL = PatternFill("solid", fgColor="0F3D3E")
STATUS_FILL = {"Completed": "D6F0E3", "Scheduled": "DCE8FA", "Cancelled": "E5E7EB", "Available": "D6F0E3",
               "Occupied": "FCE0D3", "Maintenance": "FBEBC5", "LOW": "F9D2D2", "OK": "D6F0E3",
               "IN HOSPITAL": "FCE0D3"}
BAR_COLS = {"Qty", "Charge", "Fee", "Cost", "BedBill", "UnitCost", "Days", "total_cost", "revenue", "bed_bill"}
thin = Side(style="thin", color="D9DEE2")


def write_sheet(ws, columns, data, title=None):
    headers = [c.replace("_", " ").title() if c.islower() else c for c in columns]
    ws.append(headers)
    for r in data:
        ws.append(["" if v is None else v for v in r])
    for c in ws[1]:
        c.fill, c.font = HEAD_FILL, Font(bold=True, color="FFFFFF")
        c.alignment = Alignment(vertical="center", horizontal="left")
    ws.row_dimensions[1].height = 22
    ws.freeze_panes = "A2"
    n = len(data) + 1
    if data:
        ws.auto_filter.ref = f"A1:{get_column_letter(len(columns))}{n}"
    for i, col in enumerate(columns, 1):
        width = max([len(str(headers[i - 1]))] + [len(str(r[i - 1])) for r in data[:300] if r[i - 1] is not None]) + 3
        ws.column_dimensions[get_column_letter(i)].width = min(max(width, 9), 46)
        letter = get_column_letter(i)
        for row in range(2, n + 1):
            cell = ws[f"{letter}{row}"]
            cell.border = Border(bottom=thin)
            if isinstance(cell.value, float) and col in BAR_COLS:
                cell.number_format = "#,##0"
            if isinstance(cell.value, str) and cell.value in STATUS_FILL:
                cell.fill = PatternFill("solid", fgColor=STATUS_FILL[cell.value])
                cell.font = Font(bold=True)
        if col in BAR_COLS and data and n > 2:
            ws.conditional_formatting.add(f"{letter}2:{letter}{n}",
                                          DataBarRule(start_type="num", start_value=0, end_type="max",
                                                      color="5B9BD5", showValue=True))


def send_wb(wb, name):
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=name,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.get("/api/export/<table>.xlsx")
def export_table(table):
    if table in TABLES:
        sql, title = TABLES[table]["sql"], TABLES[table]["title"]
    elif table in LISTS:
        title, sql = LISTS[table]
    else:
        return err("unknown table", 404)
    with lock:
        cols, data = rows(sql)
    wb = Workbook()
    ws = wb.active
    ws.title = title[:30]
    write_sheet(ws, cols, data)
    return send_wb(wb, f"{table}_{today()}.xlsx")


@app.post("/api/export/query.xlsx")
def export_query():
    d = request.get_json()
    with lock:
        try:
            cols, data = rows((d.get("sql") or "").strip().rstrip(";"))
        except sqlite3.Error as e:
            return err(friendly(e))
    wb = Workbook()
    ws = wb.active
    ws.title = "Query result"
    write_sheet(ws, cols, data)
    # a ready-made Excel chart when the result looks like  label | number...
    if data and len(data) <= 60 and len(cols) >= 2:
        num_cols = [i for i in range(1, len(cols)) if all(isinstance(r[i], (int, float)) or r[i] is None for r in data)]
        if num_cols and isinstance(data[0][0], str):
            ch = BarChart()
            ch.type, ch.title, ch.height, ch.width = "col", "Query result chart", 9, 18
            for i in num_cols[:3]:
                ch.add_data(Reference(ws, min_col=i + 1, min_row=1, max_row=len(data) + 1), titles_from_data=True)
            ch.set_categories(Reference(ws, min_col=1, min_row=2, max_row=len(data) + 1))
            ws.add_chart(ch, f"{get_column_letter(len(cols) + 2)}2")
    return send_wb(wb, f"query_result_{today()}.xlsx")


def put_block(ws, top, left, headers, data):
    """Write a small data table, return (first_data_row, last_data_row)."""
    for j, h in enumerate(headers):
        c = ws.cell(row=top, column=left + j, value=h)
        c.fill, c.font = HEAD_FILL, Font(bold=True, color="FFFFFF")
    for i, r in enumerate(data, 1):
        for j, v in enumerate(r):
            ws.cell(row=top + i, column=left + j, value=v)
    return top + 1, top + len(data)


@app.get("/api/export/workbook.xlsx")
def export_workbook():
    with lock:
        dd = dashboard_data()
        sheets = [(k, v["title"], v["sql"]) for k, v in TABLES.items()] + [(k, v[0], v[1]) for k, v in LISTS.items()]
        data_sheets = [(t, *rows(s)) for _, t, s in sheets]
    wb = Workbook()
    ws = wb.active
    ws.title = "Dashboard"
    ws.sheet_view.showGridLines = False
    ws["A1"] = "Healthcare Resource & Patient Management - Dashboard"
    ws["A1"].font = Font(size=18, bold=True, color="0F3D3E")
    ws["A2"] = f"Generated {datetime.now():%d %b %Y, %H:%M}"
    ws["A2"].font = Font(color="6B7280")
    k = dd["kpi"]
    cards = [("Patients", k["patients"]), ("Doctors", k["doctors"]), ("Appointments today", k["appt_today"]),
             ("Beds free", f"{k['beds_free']} / {k['beds_total']}"), ("Admitted now", k["admitted"]),
             ("Low-stock items", k["low_stock"]), ("Revenue, last 30 days (Rs)", k["revenue_30"])]
    for i, (t, v) in enumerate(cards):
        col = 1 + (i * 2)
        ws.merge_cells(start_row=4, start_column=col, end_row=4, end_column=col + 1)
        ws.merge_cells(start_row=5, start_column=col, end_row=5, end_column=col + 1)
        a, b = ws.cell(row=4, column=col, value=v), ws.cell(row=5, column=col, value=t)
        a.font, b.font = Font(size=20, bold=True, color="0F3D3E"), Font(size=9, color="6B7280")
        a.alignment = b.alignment = Alignment(horizontal="center")
        a.number_format = "#,##0"
        for r in (4, 5):
            for c in (col, col + 1):
                ws.cell(row=r, column=c).fill = PatternFill("solid", fgColor="EEF5F5")
    for c in range(1, 16):
        ws.column_dimensions[get_column_letter(c)].width = 14
    ws.column_dimensions['A'].width = 20

    top = 8
    # 1) appointments per day (line)  2) status split  3) occupancy  4) revenue
    r1, r2 = put_block(ws, top, 1, ["Day", "Completed", "Scheduled", "Cancelled"],
                       [[d["day"], d["Completed"], d["Scheduled"], d["Cancelled"]] for d in dd["days"]])
    ch = BarChart()
    ch.type, ch.grouping, ch.overlap = "col", "stacked", 100
    ch.title, ch.height, ch.width = "Appointments per day", 8.5, 17
    ch.add_data(Reference(ws, min_col=2, max_col=4, min_row=top, max_row=r2), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=r1, max_row=r2))
    ws.add_chart(ch, "F8")

    t2 = r2 + 3
    q1, q2 = put_block(ws, t2, 1, ["Department", "Occupied", "Available", "Maintenance"],
                       [[o["department"], o["occupied"], o["available"], o["maintenance"]] for o in dd["occupancy"]])
    ch = BarChart()
    ch.type, ch.grouping, ch.overlap = "bar", "stacked", 100
    ch.title, ch.height, ch.width = "Bed occupancy by department", 8.5, 17
    ch.add_data(Reference(ws, min_col=2, max_col=4, min_row=t2, max_row=q2), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=q1, max_row=q2))
    ws.add_chart(ch, "F26")

    t3 = q2 + 3
    s1, s2 = put_block(ws, t3, 1, ["Department", "Revenue (Rs)", "Visits"],
                       [[r["department"], r["revenue"], r["visits"]] for r in dd["revenue"]])
    ch = BarChart()
    ch.type, ch.title, ch.height, ch.width = "col", "Consultation revenue by department", 8.5, 17
    ch.add_data(Reference(ws, min_col=2, min_row=t3, max_row=s2), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=s1, max_row=s2))
    ch.legend = None
    ws.add_chart(ch, "F44")

    t4 = s2 + 3
    g1, g2 = put_block(ws, t4, 1, ["Gender", "Patients"], [[g["label"], g["n"]] for g in dd["gender"]])
    pie = PieChart()
    pie.title, pie.height, pie.width = "Patients by gender", 8.5, 12
    pie.add_data(Reference(ws, min_col=2, min_row=t4, max_row=g2), titles_from_data=True)
    pie.set_categories(Reference(ws, min_col=1, min_row=g1, max_row=g2))
    pie.dataLabels = DataLabelList()
    pie.dataLabels.showPercent = True
    ws.add_chart(pie, "F62")

    for title, cols, data in data_sheets:
        s = wb.create_sheet(title[:30])
        write_sheet(s, cols, data)
    return send_wb(wb, f"healthcare_workbook_{today()}.xlsx")


# =====================================================================
#  Import from Excel / CSV
# =====================================================================
@app.post("/api/import/<table>")
def import_table(table):
    cfg = TABLES.get(table)
    if not cfg or table not in ("patients", "resources", "doctors"):
        return err("Import is available for patients, doctors and resources.", 404)
    f = request.files.get("file")
    if not f:
        return err("Choose an .xlsx or .csv file.")
    name = f.filename.lower()
    try:
        if name.endswith(".csv"):
            text = f.read().decode("utf-8-sig")
            grid = list(csv.reader(io.StringIO(text)))
        elif name.endswith(".xlsx"):
            ws = load_workbook(f, read_only=True, data_only=True).active
            grid = [list(r) for r in ws.iter_rows(values_only=True)]
        else:
            return err("Only .xlsx and .csv files are supported.")
    except Exception as e:  # noqa
        return err(f"Could not read the file: {e}")
    if len(grid) < 2:
        return err("The file has no data rows.")
    norm = lambda s: re.sub(r"[^a-z0-9]", "", str(s or "").lower())
    head = [norm(h) for h in grid[0]]
    colmap = {}
    for fld in cfg["fields"]:
        for key in (norm(fld["col"]), norm(fld["label"])):
            if key in head:
                colmap[fld["col"]] = head.index(key)
                break
    missing = [f["label"] for f in cfg["fields"] if f.get("req") and f["col"] not in colmap]
    if missing:
        return err("Missing required column(s): " + ", ".join(missing) +
                   ". Tip: export the table first and use its headers.")
    ok, bad = 0, []
    with lock:
        for n, r in enumerate(grid[1:], 2):
            if not any(str(x).strip() for x in r if x is not None):
                continue
            rec = {c: (r[i] if i < len(r) else None) for c, i in colmap.items()}
            try:
                for fld in cfg["fields"]:               # resolve department names to ids
                    if fld["kind"] == "fk" and fld["col"] in rec and isinstance(rec[fld["col"]], str) \
                            and not rec[fld["col"]].strip().isdigit():
                        hit = one("SELECT dept_id FROM departments WHERE LOWER(name)=LOWER(?)", (rec[fld["col"]].strip(),))
                        if hit is None:
                            raise ValueError(f"unknown department '{rec[fld['col']]}'")
                        rec[fld["col"]] = hit
                vals = clean_values(cfg, rec)
                cols = [f["col"] for f in cfg["fields"]]
                conn.execute(f"INSERT INTO {table}({', '.join(cols)}) VALUES({', '.join('?' * len(cols))})", vals)
                ok += 1
            except (ValueError, sqlite3.Error) as e:
                bad.append(f"row {n}: {friendly(e) if isinstance(e, sqlite3.Error) else e}")
        conn.commit()
    return jsonify(ok=True, imported=ok, skipped=len(bad), problems=bad[:6])


@app.post("/api/reset")
def reset():
    """Delete hospital.db and rebuild with fresh sample data."""
    global conn
    with lock:
        conn.close()
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        conn = dbm.open_db(DB_PATH)
    return jsonify(ok=True)


def main():
    port = int(os.environ.get("PORT", 5000))
    url = f"http://127.0.0.1:{port}"
    if os.environ.get("NO_BROWSER") != "1":
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    print(f"\n  Healthcare system running at {url}   (Ctrl+C to stop)\n")
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
