"""
database.py - schema (DDL), sample data (DML) and report queries.

Same relational design as the original project:
  8 tables, 3 triggers, 1 view, indexes, CHECK / UNIQUE / FOREIGN KEY constraints.
Sample data is generated with a fixed random seed so every run is identical,
and all dates are relative to "today" so the dashboard always looks alive.
"""
import random
import sqlite3

DB_FILE = "hospital.db"

# =====================================================================
#  DDL
# =====================================================================
SCHEMA = """
CREATE TABLE departments (
    dept_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT NOT NULL UNIQUE,
    floor    INTEGER
);

CREATE TABLE doctors (
    doctor_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL,
    specialization TEXT NOT NULL,
    dept_id        INTEGER NOT NULL REFERENCES departments(dept_id),
    phone          TEXT,
    fee            REAL NOT NULL DEFAULT 500 CHECK (fee >= 0)
);

CREATE TABLE patients (
    patient_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    age           INTEGER CHECK (age BETWEEN 0 AND 120),
    gender        TEXT CHECK (gender IN ('Male','Female','Other')),
    phone         TEXT,
    blood_group   TEXT,
    address       TEXT,
    registered_on TEXT DEFAULT CURRENT_DATE
);

CREATE TABLE beds (
    bed_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ward          TEXT NOT NULL,
    bed_no        TEXT NOT NULL,
    bed_type      TEXT NOT NULL CHECK (bed_type IN ('General','Private','ICU')),
    dept_id       INTEGER REFERENCES departments(dept_id),
    status        TEXT NOT NULL DEFAULT 'Available'
                  CHECK (status IN ('Available','Occupied','Maintenance')),
    daily_charge  REAL NOT NULL CHECK (daily_charge >= 0),
    UNIQUE (ward, bed_no)
);

CREATE TABLE appointments (
    appt_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL REFERENCES patients(patient_id),
    doctor_id  INTEGER NOT NULL REFERENCES doctors(doctor_id),
    appt_date  TEXT NOT NULL,
    appt_time  TEXT NOT NULL,
    reason     TEXT,
    status     TEXT NOT NULL DEFAULT 'Scheduled'
               CHECK (status IN ('Scheduled','Completed','Cancelled')),
    UNIQUE (doctor_id, appt_date, appt_time)      -- no double booking
);

CREATE TABLE admissions (
    adm_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id     INTEGER NOT NULL REFERENCES patients(patient_id),
    bed_id         INTEGER NOT NULL REFERENCES beds(bed_id),
    doctor_id      INTEGER NOT NULL REFERENCES doctors(doctor_id),
    admit_date     TEXT NOT NULL,
    discharge_date TEXT,
    diagnosis      TEXT
);

CREATE TABLE resources (
    res_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL UNIQUE,
    category   TEXT NOT NULL CHECK (category IN ('Equipment','Medicine','Consumable')),
    quantity   INTEGER NOT NULL CHECK (quantity >= 0),
    min_level  INTEGER NOT NULL DEFAULT 10,
    unit_cost  REAL NOT NULL DEFAULT 0,
    dept_id    INTEGER REFERENCES departments(dept_id)
);

CREATE TABLE resource_usage (
    usage_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    res_id     INTEGER NOT NULL REFERENCES resources(res_id),
    patient_id INTEGER NOT NULL REFERENCES patients(patient_id),
    qty        INTEGER NOT NULL CHECK (qty > 0),
    used_on    TEXT DEFAULT CURRENT_DATE
);

CREATE INDEX idx_appt_date     ON appointments(appt_date);
CREATE INDEX idx_adm_patient   ON admissions(patient_id);
CREATE INDEX idx_usage_res     ON resource_usage(res_id);

-- Triggers keep bed status and stock levels consistent automatically
CREATE TRIGGER trg_admit AFTER INSERT ON admissions
WHEN NEW.discharge_date IS NULL
BEGIN
    UPDATE beds SET status = 'Occupied' WHERE bed_id = NEW.bed_id;
END;

CREATE TRIGGER trg_discharge AFTER UPDATE OF discharge_date ON admissions
WHEN NEW.discharge_date IS NOT NULL
BEGIN
    UPDATE beds SET status = 'Available' WHERE bed_id = NEW.bed_id;
END;

CREATE TRIGGER trg_usage AFTER INSERT ON resource_usage
BEGIN
    UPDATE resources SET quantity = quantity - NEW.qty WHERE res_id = NEW.res_id;
END;

CREATE VIEW v_current_inpatients AS
SELECT ad.adm_id, p.name AS patient, b.ward || '-' || b.bed_no AS bed,
       d.name AS doctor, ad.admit_date
FROM admissions ad
JOIN patients p ON p.patient_id = ad.patient_id
JOIN beds b     ON b.bed_id     = ad.bed_id
JOIN doctors d  ON d.doctor_id  = ad.doctor_id
WHERE ad.discharge_date IS NULL;
"""


# =====================================================================
#  DML - sample data (generated, deterministic)
# =====================================================================
def _q(v):
    """SQL literal."""
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, tuple):          # ('raw', 'sql expression')
        return v[1]
    return "'" + str(v).replace("'", "''") + "'"


def _d(days):
    """Date expression relative to today (local time)."""
    return ("raw", f"date('now','localtime','{days:+d} day')")


def _insert(table, cols, rows):
    vals = ",\n ".join("(" + ",".join(_q(v) for v in r) + ")" for r in rows)
    return f"INSERT INTO {table}({', '.join(cols)}) VALUES\n {vals};\n"


def build_sample():
    rnd = random.Random(2026)
    out = []

    depts = [("Cardiology", 1), ("Orthopedics", 2), ("Pediatrics", 2),
             ("General Medicine", 1), ("Emergency & ICU", 0),
             ("Neurology", 3), ("Gynecology", 3)]
    out.append(_insert("departments", ["name", "floor"], depts))

    doctors = [
        ("Dr. Harpreet Singh", "Cardiologist", 1, 800),
        ("Dr. Anjali Sharma", "Orthopedic Surgeon", 2, 700),
        ("Dr. Ravi Verma", "Pediatrician", 3, 500),
        ("Dr. Simran Kaur", "General Physician", 4, 400),
        ("Dr. Mohit Gupta", "Intensivist", 5, 900),
        ("Dr. Neha Bansal", "Cardiologist", 1, 750),
        ("Dr. Arvind Khanna", "Neurologist", 6, 850),
        ("Dr. Priya Malhotra", "Gynecologist", 7, 650),
        ("Dr. Sandeep Bedi", "Orthopedic Surgeon", 2, 600),
        ("Dr. Kavita Arora", "Pediatrician", 3, 450),
        ("Dr. Rajesh Grover", "General Physician", 4, 350),
    ]
    out.append(_insert("doctors", ["name", "specialization", "dept_id", "phone", "fee"],
                       [(n, s, d, f"98100000{i + 1:02d}", f) for i, (n, s, d, f) in enumerate(doctors)]))

    male = ["Amandeep", "Rohan", "Karan", "Baljit", "Vikram", "Harjot", "Manpreet", "Gaurav",
            "Nitin", "Sahil", "Arjun", "Jaspreet", "Deepak", "Lakhwinder", "Tarun", "Yash",
            "Ishaan", "Aarav", "Vivaan", "Kabir", "Dev", "Rahul"]
    female = ["Gurpreet", "Sunita", "Pooja", "Meera", "Tanya", "Simran", "Navneet", "Ritu",
              "Anita", "Komal", "Shruti", "Kiran", "Aanya", "Ishita", "Mehak", "Jyoti",
              "Palak", "Sneha", "Riya", "Neelam", "Harleen", "Diya"]
    last = ["Singh", "Kaur", "Mehta", "Devi", "Malhotra", "Arora", "Joshi", "Chauhan", "Bedi",
            "Sharma", "Verma", "Gill", "Bansal", "Sandhu", "Grewal", "Kapoor", "Sethi", "Walia"]
    areas = ["Model Town", "Sarabha Nagar", "BRS Nagar", "Civil Lines", "Dugri", "Pakhowal Road",
             "Samrala Chowk", "Haibowal", "Ferozepur Road", "Ghumar Mandi", "Rajguru Nagar",
             "Chandigarh Road", "Sherpur", "Focal Point"]
    blood = ["O+"] * 8 + ["B+"] * 7 + ["A+"] * 6 + ["AB+"] * 2 + ["O-", "B-", "A-", "AB-"]

    patients, used = [], set()
    ages = [45, 32, 8, 60, 27, 38, 71, 5, 52, 29]          # first ten kept from the original data
    first10 = [("Amandeep Singh", "Male"), ("Gurpreet Kaur", "Female"), ("Rohan Mehta", "Male"),
               ("Sunita Devi", "Female"), ("Karan Malhotra", "Male"), ("Pooja Arora", "Female"),
               ("Baljit Singh", "Male"), ("Meera Joshi", "Female"), ("Vikram Chauhan", "Male"),
               ("Tanya Bedi", "Female")]
    for (nm, g), a in zip(first10, ages):
        used.add(nm)
        patients.append((nm, a, g))
    while len(patients) < 48:
        g = rnd.choice(["Male", "Female"])
        nm = f"{rnd.choice(male if g == 'Male' else female)} {rnd.choice(last)}"
        if nm in used:
            continue
        used.add(nm)
        age = rnd.choice([rnd.randint(1, 14), rnd.randint(18, 45), rnd.randint(30, 65),
                          rnd.randint(55, 85), rnd.randint(25, 50)])
        patients.append((nm, age, g))
    prow = []
    for i, (nm, a, g) in enumerate(patients):
        prow.append((nm, a, g, f"98765{i + 1:05d}", rnd.choice(blood),
                     f"{rnd.choice(areas)}, Ludhiana", _d(-rnd.randint(0, 75))))
    out.append(_insert("patients", ["name", "age", "gender", "phone", "blood_group", "address",
                                    "registered_on"], prow))

    # (ward, bed_no, type, dept, status, charge)
    beds = []
    for n in range(1, 5):
        beds.append(("Ward A", f"A{n}", "General", 4, "Available", 800))
    for n in range(1, 4):
        beds.append(("Ward B", f"B{n}", "General", 2, "Available", 900))
    for n in range(1, 4):
        beds.append(("Peds", f"P{n}", "General", 3, "Available", 850))
    for n in range(1, 5):
        beds.append(("ICU", f"I{n}", "ICU", 5, "Maintenance" if n == 4 else "Available", 5000))
    for n in range(1, 5):
        beds.append(("Private", f"R{n}", "Private", 1 if n < 3 else 6, "Available", 3500))
    for n in range(1, 3):
        beds.append(("Neuro", f"N{n}", "General", 6, "Available", 1100))
    for n in range(1, 3):
        beds.append(("Maternity", f"M{n}", "Private", 7, "Available", 3000))
    out.append(_insert("beds", ["ward", "bed_no", "bed_type", "dept_id", "status", "daily_charge"], beds))

    # ---------------- appointments (past 30 days -> next 4 days)
    reasons = {
        1: ["Chest pain", "Follow-up ECG", "BP check", "Palpitations", "Second opinion"],
        2: ["Knee injury", "Back pain", "Fracture review", "Shoulder pain", "Cast removal"],
        3: ["Vaccination", "Cough & cold", "Fever", "Growth check", "Rash"],
        4: ["Fever", "Routine checkup", "Report review", "Diabetes review", "Headache"],
        5: ["ICU review", "Emergency follow-up"],
        6: ["Migraine", "Dizziness", "Seizure follow-up", "Numbness"],
        7: ["Antenatal checkup", "Ultrasound review", "Routine checkup"],
    }
    slots = [f"{h:02d}:{m}" for h in range(9, 17) for m in ("00", "30")]
    taken, appts = set(), []
    weights = [3, 2, 3, 4, 1, 2, 2]                      # busy doctors vs quiet ones
    doc_ids = list(range(1, len(doctors) + 1))
    dweights = [4, 3, 3, 5, 1, 3, 3, 3, 2, 2, 4]
    for day in range(-30, 5):
        n = rnd.randint(2, 5) + (2 if -30 <= day <= -20 else 0) + (1 if day % 7 in (0, 1) else 0)
        for _ in range(n):
            did = rnd.choices(doc_ids, dweights)[0]
            t = rnd.choice(slots)
            if (did, day, t) in taken:
                continue
            taken.add((did, day, t))
            pid = rnd.randint(1, len(patients))
            dep = doctors[did - 1][2]
            if day < 0:
                st = rnd.choices(["Completed", "Cancelled"], [86, 14])[0]
            elif day == 0:
                st = "Completed" if t < "12:00" else "Scheduled"
            else:
                st = "Scheduled"
            appts.append((pid, did, _d(day), t, rnd.choice(reasons[dep]), st))
    out.append(_insert("appointments",
                       ["patient_id", "doctor_id", "appt_date", "appt_time", "reason", "status"], appts))

    # ---------------- admissions
    def doctor_for(bed):
        dep = beds[bed - 1][3]
        cands = [i + 1 for i, d in enumerate(doctors) if d[2] == dep]
        return rnd.choice(cands)

    diag = {
        1: ["Acute MI - monitoring", "Hypertensive crisis", "Unstable angina", "Heart failure"],
        2: ["Femur fracture", "Tibia fracture", "Hip replacement", "Spinal injury"],
        3: ["Pneumonia", "Bronchiolitis", "Gastroenteritis", "Dengue fever"],
        4: ["Dengue fever", "Typhoid", "Diabetic ketoacidosis", "Viral fever"],
        5: ["Respiratory failure", "Sepsis", "Post-op ICU care", "Head trauma"],
        6: ["Stroke", "Status epilepticus", "Meningitis"],
        7: ["Normal delivery", "C-section recovery", "Preeclampsia"],
    }
    adms = []
    free = [i for i, b in enumerate(beds, 1) if b[4] != "Maintenance"]
    pats = list(range(1, len(patients) + 1))
    rnd.shuffle(pats)
    # historical (already discharged) stays
    for _ in range(26):
        b = rnd.choice(free)
        start = -rnd.randint(9, 55)
        stay = rnd.randint(2, 8)
        dep = beds[b - 1][3]
        adms.append((rnd.choice(pats), b, doctor_for(b), _d(start), _d(start + stay), rnd.choice(diag[dep])))
    # currently admitted - distinct beds, distinct patients
    cur_beds = rnd.sample(free, 11)
    cur_pats = pats[:11]
    for b, p in zip(cur_beds, cur_pats):
        dep = beds[b - 1][3]
        adms.append((p, b, doctor_for(b), _d(-rnd.randint(0, 8)), None, rnd.choice(diag[dep])))
    out.append(_insert("admissions",
                       ["patient_id", "bed_id", "doctor_id", "admit_date", "discharge_date", "diagnosis"],
                       adms))

    # ---------------- resources: (name, category, final_qty, min, unit_cost, dept)
    res = [
        ("Ventilator", "Equipment", 6, 3, 450000, 5),
        ("ECG Machine", "Equipment", 4, 2, 120000, 1),
        ("Wheelchair", "Equipment", 15, 5, 6500, 4),
        ("Defibrillator", "Equipment", 3, 2, 180000, 1),
        ("Paracetamol 500mg", "Medicine", 400, 100, 2, 4),
        ("Insulin Vial", "Medicine", 14, 20, 350, 4),
        ("Amoxicillin 250mg", "Medicine", 160, 80, 6, 3),
        ("Pediatric Syrup", "Medicine", 70, 30, 95, 3),
        ("Aspirin 75mg", "Medicine", 55, 60, 3, 1),
        ("Surgical Gloves (box)", "Consumable", 38, 40, 250, 2),
        ("IV Fluid Bag", "Consumable", 41, 50, 80, 5),
        ("Syringe 5ml (pack)", "Consumable", 120, 50, 120, 4),
        ("Cotton Roll", "Consumable", 90, 40, 45, 2),
        ("Plaster Bandage", "Consumable", 22, 25, 160, 2),
        ("Oxygen Cylinder", "Equipment", 9, 8, 4500, 5),
    ]
    usage = []
    for _ in range(46):
        r = rnd.randint(1, len(res))
        cat = res[r - 1][1]
        q = rnd.randint(1, 3) if cat == "Equipment" else rnd.randint(1, 12)
        if cat == "Equipment":
            q = 1
        usage.append((r, rnd.randint(1, len(patients)), q, _d(-rnd.randint(0, 40))))
    total = {}
    for r, _, q, _ in usage:
        total[r] = total.get(r, 0) + q
    res_rows = [(n, c, fq + total.get(i, 0), m, u, d) for i, (n, c, fq, m, u, d) in enumerate(res, 1)]
    out.append(_insert("resources", ["name", "category", "quantity", "min_level", "unit_cost", "dept_id"],
                       res_rows))
    out.append(_insert("resource_usage", ["res_id", "patient_id", "qty", "used_on"], usage))
    return "\n".join(out)


SAMPLE = build_sample()


# =====================================================================
#  Report queries (title, concept, SQL) - used by the SQL Lab page
# =====================================================================
REPORTS = [
    ("Appointment schedule", "JOIN (4 tables)",
     """SELECT a.appt_id, a.appt_date, a.appt_time, p.name AS patient,
       d.name AS doctor, dep.name AS department, a.status
FROM appointments a
JOIN patients p     ON p.patient_id = a.patient_id
JOIN doctors d      ON d.doctor_id  = a.doctor_id
JOIN departments dep ON dep.dept_id = d.dept_id
ORDER BY a.appt_date, a.appt_time"""),

    ("Doctor workload", "LEFT JOIN + COUNT + GROUP BY",
     """SELECT d.name AS doctor, d.specialization,
       COUNT(a.appt_id) AS total_appointments,
       COALESCE(SUM(a.status = 'Completed'), 0) AS completed,
       COALESCE(SUM(a.status = 'Scheduled'), 0) AS upcoming
FROM doctors d
LEFT JOIN appointments a ON a.doctor_id = d.doctor_id
GROUP BY d.doctor_id
ORDER BY total_appointments DESC"""),

    ("Bed occupancy by department", "Aggregates + HAVING",
     """SELECT dep.name AS department,
       COUNT(b.bed_id) AS total_beds,
       SUM(b.status = 'Occupied')    AS occupied,
       SUM(b.status = 'Available')   AS available,
       SUM(b.status = 'Maintenance') AS maintenance,
       ROUND(100.0 * SUM(b.status = 'Occupied') / COUNT(b.bed_id), 1) AS occupancy_pct
FROM departments dep
JOIN beds b ON b.dept_id = dep.dept_id
GROUP BY dep.dept_id
HAVING COUNT(b.bed_id) > 0
ORDER BY occupancy_pct DESC"""),

    ("Current inpatients with running bill", "JOIN + date arithmetic",
     """SELECT p.name AS patient, b.ward || '-' || b.bed_no AS bed, b.bed_type,
       d.name AS doctor, ad.admit_date,
       CAST(julianday('now','localtime') - julianday(ad.admit_date) AS INTEGER) + 1 AS days_stayed,
       (CAST(julianday('now','localtime') - julianday(ad.admit_date) AS INTEGER) + 1)
         * b.daily_charge AS bed_bill
FROM admissions ad
JOIN patients p ON p.patient_id = ad.patient_id
JOIN beds b     ON b.bed_id     = ad.bed_id
JOIN doctors d  ON d.doctor_id  = ad.doctor_id
WHERE ad.discharge_date IS NULL
ORDER BY bed_bill DESC"""),

    ("Patients with above-average visits", "Subquery in HAVING",
     """SELECT p.name AS patient, COUNT(*) AS appointments
FROM patients p
JOIN appointments a ON a.patient_id = p.patient_id
GROUP BY p.patient_id
HAVING COUNT(*) > (SELECT AVG(c) FROM
                    (SELECT COUNT(*) AS c FROM appointments GROUP BY patient_id))
ORDER BY appointments DESC"""),

    ("Doctors with no appointments", "Subquery (NOT IN)",
     """SELECT name, specialization, phone
FROM doctors
WHERE doctor_id NOT IN (SELECT doctor_id FROM appointments)"""),

    ("Patients never admitted", "Correlated subquery (NOT EXISTS)",
     """SELECT p.patient_id, p.name, p.age, p.phone
FROM patients p
WHERE NOT EXISTS (SELECT 1 FROM admissions ad
                  WHERE ad.patient_id = p.patient_id)"""),

    ("Costliest available bed", "Subquery with MAX",
     """SELECT bed_id, ward, bed_no, bed_type, daily_charge
FROM beds
WHERE status = 'Available'
  AND daily_charge = (SELECT MAX(daily_charge) FROM beds
                      WHERE status = 'Available')"""),

    ("Low-stock resources", "WHERE + LEFT JOIN",
     """SELECT r.name, r.category, r.quantity, r.min_level,
       r.min_level - r.quantity AS shortfall, dep.name AS department
FROM resources r
LEFT JOIN departments dep ON dep.dept_id = r.dept_id
WHERE r.quantity <= r.min_level
ORDER BY shortfall DESC"""),

    ("Resource cost by department", "JOIN + SUM",
     """SELECT dep.name AS department, COUNT(u.usage_id) AS issues,
       SUM(u.qty) AS units_used, SUM(u.qty * r.unit_cost) AS total_cost
FROM resource_usage u
JOIN resources r     ON r.res_id  = u.res_id
JOIN departments dep ON dep.dept_id = r.dept_id
GROUP BY dep.dept_id
ORDER BY total_cost DESC"""),

    ("Consultation revenue by department", "JOIN + SUM + HAVING",
     """SELECT dep.name AS department, COUNT(*) AS completed_visits,
       SUM(d.fee) AS revenue, ROUND(AVG(d.fee), 2) AS avg_fee
FROM appointments a
JOIN doctors d       ON d.doctor_id = a.doctor_id
JOIN departments dep ON dep.dept_id = d.dept_id
WHERE a.status = 'Completed'
GROUP BY dep.dept_id
HAVING SUM(d.fee) > 0
ORDER BY revenue DESC"""),

    ("Average length of stay (discharged)", "AVG + date functions",
     """SELECT dep.name AS department, COUNT(*) AS discharges,
       ROUND(AVG(julianday(ad.discharge_date) - julianday(ad.admit_date)), 1)
         AS avg_days_stay
FROM admissions ad
JOIN doctors d       ON d.doctor_id = ad.doctor_id
JOIN departments dep ON dep.dept_id = d.dept_id
WHERE ad.discharge_date IS NOT NULL
GROUP BY dep.dept_id
ORDER BY avg_days_stay DESC"""),

    ("Complete patient history", "UNION ALL",
     """SELECT p.name AS patient, 'Appointment' AS event, a.appt_date AS event_date,
       a.reason AS detail
FROM appointments a JOIN patients p ON p.patient_id = a.patient_id
UNION ALL
SELECT p.name, 'Admission', ad.admit_date, ad.diagnosis
FROM admissions ad JOIN patients p ON p.patient_id = ad.patient_id
ORDER BY patient, event_date"""),

    ("View: v_current_inpatients", "VIEW",
     "SELECT * FROM v_current_inpatients"),
]


def open_db(path=DB_FILE):
    """Open the database; create schema + sample data on first run."""
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    exists = conn.execute("SELECT 1 FROM sqlite_master WHERE name='patients'").fetchone()
    if not exists:
        conn.executescript(SCHEMA)
        conn.executescript(SAMPLE)
        conn.commit()
    return conn


def export_sql_file(path="healthcare.sql"):
    """Write DDL + DML + report queries into one .sql file (for the project report / viva)."""
    parts = ["-- Healthcare Resource & Patient Management System\n"
             "-- DDL\n", SCHEMA, "\n-- DML (sample data; dates are relative to the day the DB is created)\n", SAMPLE,
             "\n-- Report queries\n"]
    for t, c, sql in REPORTS:
        parts.append(f"\n-- {t}   [{c}]\n{sql};\n")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


if __name__ == "__main__":
    export_sql_file()
    print("healthcare.sql written")
