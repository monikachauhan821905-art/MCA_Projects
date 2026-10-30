# CareDesk - Healthcare Resource & Patient Management System

A modern dashboard for the same SQLite project: patients, doctors, appointments, beds,
admissions and medical resources. The UI runs in your browser (served locally by Flask),
so there is no Tkinter. Everything works offline - Chart.js and the font are bundled.

## Run it

    pip install -r requirements.txt
    python app.py

It opens http://127.0.0.1:5000 by itself. `hospital.db` is created on the first run with
sample data (48 patients, 160 appointments, 22 beds ...). Use **Reset sample data**
(bottom of the sidebar) or delete `hospital.db` to start again.

## What is new

| Area | What you get |
|---|---|
| Dashboard | KPI strip, live **ward map** (click a bed to admit / discharge / send for maintenance), occupancy, appointment, revenue, stock, age and doctor-workload charts |
| Excel-style grids | sort, search, filter chips, data bars, a **totals row** (Σ), pagination |
| Chart this view | one click turns any grid or SQL result into a bar / line / pie / donut chart |
| Analytics | build a **pivot table** (rows x columns x values) with a chart and colour-scale shading; CSV download |
| Excel export | any table, any SQL result, or the **whole workbook** with native Excel charts and formatting |
| Excel import | patients, doctors and resources from .xlsx / .csv |
| SQL lab | all 14 report queries plus a free SQL editor (Ctrl+Enter) |
| Tables & triggers | schema view with PK / FK tags and what each trigger does |
| Dark mode | toggle in the top bar (remembered) |

## Files

- `app.py` - Flask server: API, analytics, Excel export / import
- `database.py` - DDL, triggers, view, sample data (DML) and the report queries
- `healthcare.sql` - the complete DDL + DML + report queries as plain SQL, for your report / viva
  (regenerate with `python database.py`)
- `static/` - the interface (`index.html`, `style.css`, `core.js`, `pages.js`) and bundled libraries

## SQL concepts covered (for viva)

DDL with PRIMARY KEY / FOREIGN KEY / UNIQUE / CHECK / DEFAULT, indexes, DML, 4-table JOINs,
LEFT JOIN, GROUP BY / HAVING, aggregate functions, subqueries (IN, NOT IN, NOT EXISTS, scalar,
in HAVING), UNION ALL, date functions (julianday, strftime), a recursive CTE, a VIEW and
three TRIGGERS (admit -> bed Occupied, discharge -> bed Available, issue -> stock reduces).
