-- Healthcare Resource & Patient Management System
-- DDL


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


-- DML (sample data; dates are relative to the day the DB is created)

INSERT INTO departments(name, floor) VALUES
 ('Cardiology',1),
 ('Orthopedics',2),
 ('Pediatrics',2),
 ('General Medicine',1),
 ('Emergency & ICU',0),
 ('Neurology',3),
 ('Gynecology',3);

INSERT INTO doctors(name, specialization, dept_id, phone, fee) VALUES
 ('Dr. Harpreet Singh','Cardiologist',1,'9810000001',800),
 ('Dr. Anjali Sharma','Orthopedic Surgeon',2,'9810000002',700),
 ('Dr. Ravi Verma','Pediatrician',3,'9810000003',500),
 ('Dr. Simran Kaur','General Physician',4,'9810000004',400),
 ('Dr. Mohit Gupta','Intensivist',5,'9810000005',900),
 ('Dr. Neha Bansal','Cardiologist',1,'9810000006',750),
 ('Dr. Arvind Khanna','Neurologist',6,'9810000007',850),
 ('Dr. Priya Malhotra','Gynecologist',7,'9810000008',650),
 ('Dr. Sandeep Bedi','Orthopedic Surgeon',2,'9810000009',600),
 ('Dr. Kavita Arora','Pediatrician',3,'9810000010',450),
 ('Dr. Rajesh Grover','General Physician',4,'9810000011',350);

INSERT INTO patients(name, age, gender, phone, blood_group, address, registered_on) VALUES
 ('Amandeep Singh',45,'Male','9876500001','A+','Civil Lines, Ludhiana',date('now','localtime','-59 day')),
 ('Gurpreet Kaur',32,'Female','9876500002','B+','Rajguru Nagar, Ludhiana',date('now','localtime','-15 day')),
 ('Rohan Mehta',8,'Male','9876500003','AB+','Pakhowal Road, Ludhiana',date('now','localtime','-64 day')),
 ('Sunita Devi',60,'Female','9876500004','AB+','Dugri, Ludhiana',date('now','localtime','-49 day')),
 ('Karan Malhotra',27,'Male','9876500005','B+','Focal Point, Ludhiana',date('now','localtime','-45 day')),
 ('Pooja Arora',38,'Female','9876500006','O+','Chandigarh Road, Ludhiana',date('now','localtime','-55 day')),
 ('Baljit Singh',71,'Male','9876500007','O+','Dugri, Ludhiana',date('now','localtime','-42 day')),
 ('Meera Joshi',5,'Female','9876500008','B+','Chandigarh Road, Ludhiana',date('now','localtime','-15 day')),
 ('Vikram Chauhan',52,'Male','9876500009','B+','Sherpur, Ludhiana',date('now','localtime','-53 day')),
 ('Tanya Bedi',29,'Female','9876500010','B+','Ghumar Mandi, Ludhiana',date('now','localtime','-2 day')),
 ('Arjun Sethi',32,'Male','9876500011','A+','Pakhowal Road, Ludhiana',date('now','localtime','-25 day')),
 ('Riya Walia',49,'Female','9876500012','A+','Model Town, Ludhiana',date('now','localtime','-14 day')),
 ('Ritu Singh',64,'Female','9876500013','O+','Ghumar Mandi, Ludhiana',date('now','localtime','-15 day')),
 ('Rahul Kapoor',43,'Male','9876500014','O+','Model Town, Ludhiana',date('now','localtime','-16 day')),
 ('Aanya Sethi',42,'Female','9876500015','A+','Pakhowal Road, Ludhiana',date('now','localtime','-38 day')),
 ('Komal Grewal',49,'Female','9876500016','O+','Samrala Chowk, Ludhiana',date('now','localtime','-74 day')),
 ('Mehak Sandhu',70,'Female','9876500017','O+','Pakhowal Road, Ludhiana',date('now','localtime','-53 day')),
 ('Ishita Kapoor',34,'Female','9876500018','B+','Samrala Chowk, Ludhiana',date('now','localtime','-30 day')),
 ('Ishaan Devi',70,'Male','9876500019','B-','Samrala Chowk, Ludhiana',date('now','localtime','-28 day')),
 ('Baljit Grewal',63,'Male','9876500020','B-','BRS Nagar, Ludhiana',date('now','localtime','-23 day')),
 ('Sneha Sethi',55,'Female','9876500021','A+','Model Town, Ludhiana',date('now','localtime','-69 day')),
 ('Dev Grewal',61,'Male','9876500022','AB+','Ferozepur Road, Ludhiana',date('now','localtime','-50 day')),
 ('Mehak Sethi',38,'Female','9876500023','B+','Sherpur, Ludhiana',date('now','localtime','-18 day')),
 ('Sahil Verma',47,'Male','9876500024','O+','Model Town, Ludhiana',date('now','localtime','-2 day')),
 ('Mehak Arora',60,'Female','9876500025','B+','Ferozepur Road, Ludhiana',date('now','localtime','-61 day')),
 ('Kiran Devi',4,'Female','9876500026','B+','Dugri, Ludhiana',date('now','localtime','-40 day')),
 ('Amandeep Grewal',35,'Male','9876500027','O+','Rajguru Nagar, Ludhiana',date('now','localtime','-75 day')),
 ('Baljit Kaur',47,'Male','9876500028','O+','Focal Point, Ludhiana',date('now','localtime','-22 day')),
 ('Amandeep Verma',36,'Male','9876500029','A+','Model Town, Ludhiana',date('now','localtime','-65 day')),
 ('Yash Malhotra',64,'Male','9876500030','AB-','Dugri, Ludhiana',date('now','localtime','-43 day')),
 ('Vikram Sharma',29,'Male','9876500031','A+','Ferozepur Road, Ludhiana',date('now','localtime','-40 day')),
 ('Deepak Singh',34,'Male','9876500032','O+','Rajguru Nagar, Ludhiana',date('now','localtime','-1 day')),
 ('Amandeep Sethi',8,'Male','9876500033','A+','Civil Lines, Ludhiana',date('now','localtime','-60 day')),
 ('Vivaan Sethi',31,'Male','9876500034','O+','Civil Lines, Ludhiana',date('now','localtime','-65 day')),
 ('Aarav Bansal',45,'Male','9876500035','O+','Chandigarh Road, Ludhiana',date('now','localtime','-51 day')),
 ('Tarun Joshi',45,'Male','9876500036','AB+','Pakhowal Road, Ludhiana',date('now','localtime','-29 day')),
 ('Ishaan Malhotra',67,'Male','9876500037','A+','Focal Point, Ludhiana',date('now','localtime','-35 day')),
 ('Pooja Bansal',60,'Female','9876500038','B+','Focal Point, Ludhiana',date('now','localtime','-25 day')),
 ('Ishita Sharma',71,'Female','9876500039','B+','Pakhowal Road, Ludhiana',date('now','localtime','-58 day')),
 ('Ishaan Sethi',26,'Male','9876500040','A+','Haibowal, Ludhiana',date('now','localtime','-70 day')),
 ('Karan Grewal',28,'Male','9876500041','A-','Haibowal, Ludhiana',date('now','localtime','-74 day')),
 ('Jaspreet Arora',28,'Male','9876500042','B+','Civil Lines, Ludhiana',date('now','localtime','-20 day')),
 ('Sneha Joshi',27,'Female','9876500043','A+','Samrala Chowk, Ludhiana',date('now','localtime','-19 day')),
 ('Nitin Devi',36,'Male','9876500044','A+','Model Town, Ludhiana',date('now','localtime','-45 day')),
 ('Dev Devi',47,'Male','9876500045','AB-','Focal Point, Ludhiana',date('now','localtime','-66 day')),
 ('Simran Bedi',30,'Female','9876500046','AB+','Samrala Chowk, Ludhiana',date('now','localtime','-4 day')),
 ('Gaurav Singh',42,'Male','9876500047','A+','BRS Nagar, Ludhiana',date('now','localtime','-10 day')),
 ('Shruti Grewal',32,'Female','9876500048','B+','Pakhowal Road, Ludhiana',date('now','localtime','-69 day'));

INSERT INTO beds(ward, bed_no, bed_type, dept_id, status, daily_charge) VALUES
 ('Ward A','A1','General',4,'Available',800),
 ('Ward A','A2','General',4,'Available',800),
 ('Ward A','A3','General',4,'Available',800),
 ('Ward A','A4','General',4,'Available',800),
 ('Ward B','B1','General',2,'Available',900),
 ('Ward B','B2','General',2,'Available',900),
 ('Ward B','B3','General',2,'Available',900),
 ('Peds','P1','General',3,'Available',850),
 ('Peds','P2','General',3,'Available',850),
 ('Peds','P3','General',3,'Available',850),
 ('ICU','I1','ICU',5,'Available',5000),
 ('ICU','I2','ICU',5,'Available',5000),
 ('ICU','I3','ICU',5,'Available',5000),
 ('ICU','I4','ICU',5,'Maintenance',5000),
 ('Private','R1','Private',1,'Available',3500),
 ('Private','R2','Private',1,'Available',3500),
 ('Private','R3','Private',6,'Available',3500),
 ('Private','R4','Private',6,'Available',3500),
 ('Neuro','N1','General',6,'Available',1100),
 ('Neuro','N2','General',6,'Available',1100),
 ('Maternity','M1','Private',7,'Available',3000),
 ('Maternity','M2','Private',7,'Available',3000);

INSERT INTO appointments(patient_id, doctor_id, appt_date, appt_time, reason, status) VALUES
 (2,2,date('now','localtime','-30 day'),'10:30','Cast removal','Completed'),
 (26,4,date('now','localtime','-30 day'),'09:30','Headache','Completed'),
 (33,9,date('now','localtime','-30 day'),'11:30','Back pain','Completed'),
 (36,8,date('now','localtime','-30 day'),'14:00','Antenatal checkup','Completed'),
 (11,8,date('now','localtime','-30 day'),'12:00','Ultrasound review','Cancelled'),
 (9,6,date('now','localtime','-30 day'),'14:30','Follow-up ECG','Cancelled'),
 (28,10,date('now','localtime','-29 day'),'16:30','Rash','Completed'),
 (12,2,date('now','localtime','-29 day'),'09:00','Back pain','Completed'),
 (33,2,date('now','localtime','-29 day'),'10:30','Knee injury','Completed'),
 (24,10,date('now','localtime','-29 day'),'10:00','Rash','Completed'),
 (9,7,date('now','localtime','-28 day'),'12:30','Seizure follow-up','Completed'),
 (25,5,date('now','localtime','-28 day'),'10:00','Emergency follow-up','Completed'),
 (31,7,date('now','localtime','-28 day'),'14:30','Migraine','Cancelled'),
 (23,6,date('now','localtime','-28 day'),'12:30','Palpitations','Completed'),
 (6,11,date('now','localtime','-28 day'),'14:30','Fever','Completed'),
 (17,9,date('now','localtime','-28 day'),'13:30','Back pain','Completed'),
 (21,4,date('now','localtime','-27 day'),'14:00','Diabetes review','Cancelled'),
 (13,4,date('now','localtime','-27 day'),'11:30','Routine checkup','Completed'),
 (23,10,date('now','localtime','-27 day'),'14:30','Rash','Completed'),
 (29,4,date('now','localtime','-27 day'),'11:00','Routine checkup','Completed'),
 (18,10,date('now','localtime','-27 day'),'14:00','Growth check','Completed'),
 (15,2,date('now','localtime','-26 day'),'13:00','Back pain','Completed'),
 (18,6,date('now','localtime','-26 day'),'10:30','Palpitations','Completed'),
 (2,7,date('now','localtime','-26 day'),'15:00','Seizure follow-up','Completed'),
 (7,8,date('now','localtime','-26 day'),'14:00','Ultrasound review','Completed'),
 (28,11,date('now','localtime','-26 day'),'12:00','Report review','Completed'),
 (47,1,date('now','localtime','-26 day'),'15:00','BP check','Completed'),
 (31,2,date('now','localtime','-25 day'),'15:30','Shoulder pain','Completed'),
 (15,4,date('now','localtime','-25 day'),'09:30','Report review','Completed'),
 (30,4,date('now','localtime','-25 day'),'12:00','Headache','Completed'),
 (36,7,date('now','localtime','-25 day'),'10:00','Migraine','Completed'),
 (22,11,date('now','localtime','-25 day'),'11:00','Diabetes review','Cancelled'),
 (46,2,date('now','localtime','-25 day'),'11:30','Cast removal','Completed'),
 (7,8,date('now','localtime','-24 day'),'11:00','Ultrasound review','Completed'),
 (31,1,date('now','localtime','-24 day'),'12:30','BP check','Completed'),
 (39,4,date('now','localtime','-24 day'),'14:00','Diabetes review','Completed'),
 (3,11,date('now','localtime','-24 day'),'13:00','Routine checkup','Completed'),
 (17,1,date('now','localtime','-24 day'),'14:30','Palpitations','Completed'),
 (33,2,date('now','localtime','-24 day'),'13:00','Shoulder pain','Completed'),
 (27,4,date('now','localtime','-24 day'),'09:30','Headache','Cancelled'),
 (33,11,date('now','localtime','-23 day'),'10:00','Headache','Cancelled'),
 (43,4,date('now','localtime','-23 day'),'14:00','Routine checkup','Completed'),
 (17,1,date('now','localtime','-23 day'),'11:30','Second opinion','Cancelled'),
 (41,6,date('now','localtime','-23 day'),'15:00','Second opinion','Completed'),
 (30,11,date('now','localtime','-23 day'),'09:00','Diabetes review','Completed'),
 (33,6,date('now','localtime','-23 day'),'11:00','BP check','Completed'),
 (24,2,date('now','localtime','-22 day'),'14:00','Shoulder pain','Cancelled'),
 (10,6,date('now','localtime','-22 day'),'12:00','Follow-up ECG','Completed'),
 (43,8,date('now','localtime','-22 day'),'11:00','Routine checkup','Completed'),
 (20,10,date('now','localtime','-22 day'),'13:00','Cough & cold','Cancelled'),
 (9,2,date('now','localtime','-22 day'),'14:30','Back pain','Completed'),
 (44,8,date('now','localtime','-22 day'),'11:30','Routine checkup','Completed'),
 (20,7,date('now','localtime','-22 day'),'09:00','Seizure follow-up','Completed'),
 (10,5,date('now','localtime','-21 day'),'15:30','ICU review','Cancelled'),
 (31,8,date('now','localtime','-21 day'),'09:30','Antenatal checkup','Completed'),
 (22,4,date('now','localtime','-21 day'),'13:00','Routine checkup','Completed'),
 (28,6,date('now','localtime','-21 day'),'10:00','Follow-up ECG','Completed'),
 (16,10,date('now','localtime','-21 day'),'11:30','Growth check','Completed'),
 (47,4,date('now','localtime','-20 day'),'15:30','Report review','Completed'),
 (41,8,date('now','localtime','-20 day'),'13:30','Routine checkup','Completed'),
 (14,7,date('now','localtime','-20 day'),'10:00','Migraine','Completed'),
 (46,8,date('now','localtime','-20 day'),'14:30','Routine checkup','Completed'),
 (14,2,date('now','localtime','-20 day'),'11:30','Back pain','Completed'),
 (2,11,date('now','localtime','-20 day'),'15:30','Routine checkup','Completed'),
 (26,3,date('now','localtime','-19 day'),'14:30','Rash','Completed'),
 (23,5,date('now','localtime','-19 day'),'13:00','ICU review','Completed'),
 (36,1,date('now','localtime','-19 day'),'11:00','BP check','Completed'),
 (45,5,date('now','localtime','-19 day'),'09:30','Emergency follow-up','Completed'),
 (30,11,date('now','localtime','-18 day'),'10:00','Headache','Completed'),
 (18,10,date('now','localtime','-18 day'),'10:30','Vaccination','Completed'),
 (34,7,date('now','localtime','-18 day'),'10:00','Migraine','Cancelled'),
 (40,4,date('now','localtime','-18 day'),'16:00','Fever','Completed'),
 (2,11,date('now','localtime','-17 day'),'11:00','Fever','Completed'),
 (2,2,date('now','localtime','-17 day'),'13:00','Knee injury','Cancelled'),
 (47,8,date('now','localtime','-17 day'),'10:30','Ultrasound review','Cancelled'),
 (16,4,date('now','localtime','-16 day'),'16:30','Diabetes review','Completed'),
 (16,8,date('now','localtime','-16 day'),'15:00','Ultrasound review','Completed'),
 (13,7,date('now','localtime','-15 day'),'16:00','Numbness','Completed'),
 (34,7,date('now','localtime','-15 day'),'16:30','Dizziness','Completed'),
 (34,4,date('now','localtime','-15 day'),'09:30','Routine checkup','Completed'),
 (18,3,date('now','localtime','-14 day'),'14:00','Rash','Completed'),
 (34,1,date('now','localtime','-14 day'),'11:30','BP check','Completed'),
 (36,9,date('now','localtime','-14 day'),'10:00','Shoulder pain','Completed'),
 (27,9,date('now','localtime','-14 day'),'10:30','Knee injury','Completed'),
 (17,3,date('now','localtime','-14 day'),'09:30','Cough & cold','Completed'),
 (17,11,date('now','localtime','-13 day'),'10:00','Fever','Completed'),
 (29,3,date('now','localtime','-13 day'),'10:30','Vaccination','Completed'),
 (33,4,date('now','localtime','-13 day'),'16:00','Fever','Completed'),
 (42,11,date('now','localtime','-13 day'),'12:00','Diabetes review','Completed'),
 (11,1,date('now','localtime','-13 day'),'10:00','BP check','Completed'),
 (31,1,date('now','localtime','-12 day'),'09:30','Chest pain','Cancelled'),
 (36,11,date('now','localtime','-12 day'),'11:30','Headache','Completed'),
 (4,6,date('now','localtime','-12 day'),'16:30','Follow-up ECG','Completed'),
 (3,5,date('now','localtime','-11 day'),'12:30','Emergency follow-up','Completed'),
 (44,6,date('now','localtime','-11 day'),'16:00','Follow-up ECG','Completed'),
 (33,3,date('now','localtime','-11 day'),'12:00','Growth check','Completed'),
 (30,3,date('now','localtime','-11 day'),'11:30','Fever','Completed'),
 (37,1,date('now','localtime','-11 day'),'11:00','Follow-up ECG','Cancelled'),
 (44,10,date('now','localtime','-10 day'),'11:00','Cough & cold','Completed'),
 (9,6,date('now','localtime','-10 day'),'10:30','Palpitations','Completed'),
 (41,1,date('now','localtime','-10 day'),'16:30','Second opinion','Completed'),
 (6,4,date('now','localtime','-10 day'),'14:30','Headache','Completed'),
 (16,1,date('now','localtime','-10 day'),'13:00','Follow-up ECG','Completed'),
 (20,7,date('now','localtime','-9 day'),'11:30','Migraine','Completed'),
 (48,11,date('now','localtime','-9 day'),'14:00','Diabetes review','Completed'),
 (43,7,date('now','localtime','-9 day'),'12:30','Dizziness','Completed'),
 (8,7,date('now','localtime','-9 day'),'16:30','Migraine','Completed'),
 (2,2,date('now','localtime','-8 day'),'13:00','Fracture review','Completed'),
 (41,11,date('now','localtime','-8 day'),'15:00','Diabetes review','Completed'),
 (15,7,date('now','localtime','-8 day'),'10:30','Numbness','Completed'),
 (18,9,date('now','localtime','-8 day'),'15:00','Shoulder pain','Completed'),
 (31,3,date('now','localtime','-7 day'),'15:30','Fever','Completed'),
 (40,9,date('now','localtime','-7 day'),'10:30','Back pain','Completed'),
 (46,3,date('now','localtime','-7 day'),'13:30','Growth check','Cancelled'),
 (11,3,date('now','localtime','-7 day'),'14:00','Cough & cold','Completed'),
 (42,4,date('now','localtime','-7 day'),'14:00','Routine checkup','Completed'),
 (45,11,date('now','localtime','-6 day'),'15:00','Diabetes review','Completed'),
 (3,3,date('now','localtime','-6 day'),'13:30','Cough & cold','Completed'),
 (43,3,date('now','localtime','-6 day'),'15:30','Growth check','Completed'),
 (44,11,date('now','localtime','-6 day'),'16:30','Report review','Completed'),
 (36,8,date('now','localtime','-6 day'),'14:00','Ultrasound review','Completed'),
 (43,11,date('now','localtime','-5 day'),'13:30','Headache','Completed'),
 (25,6,date('now','localtime','-5 day'),'14:30','Chest pain','Completed'),
 (25,4,date('now','localtime','-5 day'),'15:30','Report review','Completed'),
 (23,6,date('now','localtime','-4 day'),'15:00','Chest pain','Cancelled'),
 (12,1,date('now','localtime','-4 day'),'12:00','Palpitations','Completed'),
 (28,5,date('now','localtime','-4 day'),'11:30','Emergency follow-up','Completed'),
 (8,6,date('now','localtime','-3 day'),'10:30','Chest pain','Completed'),
 (41,5,date('now','localtime','-3 day'),'14:30','ICU review','Completed'),
 (1,3,date('now','localtime','-2 day'),'13:30','Vaccination','Completed'),
 (30,9,date('now','localtime','-2 day'),'11:00','Knee injury','Completed'),
 (36,7,date('now','localtime','-2 day'),'12:00','Seizure follow-up','Completed'),
 (6,7,date('now','localtime','-2 day'),'10:30','Dizziness','Completed'),
 (36,4,date('now','localtime','-2 day'),'10:30','Diabetes review','Completed'),
 (28,1,date('now','localtime','-1 day'),'16:00','Chest pain','Cancelled'),
 (29,4,date('now','localtime','-1 day'),'09:30','Fever','Completed'),
 (12,11,date('now','localtime','-1 day'),'15:30','Fever','Completed'),
 (28,8,date('now','localtime','+0 day'),'12:30','Antenatal checkup','Scheduled'),
 (1,4,date('now','localtime','+0 day'),'11:30','Routine checkup','Completed'),
 (17,7,date('now','localtime','+0 day'),'13:30','Numbness','Scheduled'),
 (24,9,date('now','localtime','+0 day'),'12:30','Knee injury','Scheduled'),
 (37,4,date('now','localtime','+0 day'),'10:00','Headache','Completed'),
 (15,4,date('now','localtime','+1 day'),'13:30','Headache','Scheduled'),
 (17,6,date('now','localtime','+1 day'),'15:30','Chest pain','Scheduled'),
 (34,6,date('now','localtime','+1 day'),'13:00','Palpitations','Scheduled'),
 (14,3,date('now','localtime','+1 day'),'13:00','Rash','Scheduled'),
 (34,4,date('now','localtime','+1 day'),'14:30','Report review','Scheduled'),
 (1,4,date('now','localtime','+2 day'),'12:30','Routine checkup','Scheduled'),
 (45,7,date('now','localtime','+2 day'),'14:00','Seizure follow-up','Scheduled'),
 (43,8,date('now','localtime','+2 day'),'10:30','Ultrasound review','Scheduled'),
 (40,4,date('now','localtime','+2 day'),'15:30','Diabetes review','Scheduled'),
 (28,8,date('now','localtime','+3 day'),'14:30','Routine checkup','Scheduled'),
 (37,4,date('now','localtime','+3 day'),'14:00','Diabetes review','Scheduled'),
 (25,4,date('now','localtime','+3 day'),'14:30','Report review','Scheduled'),
 (1,9,date('now','localtime','+3 day'),'16:30','Fracture review','Scheduled'),
 (39,4,date('now','localtime','+3 day'),'09:30','Fever','Scheduled'),
 (8,6,date('now','localtime','+4 day'),'09:30','BP check','Scheduled'),
 (20,4,date('now','localtime','+4 day'),'15:00','Report review','Scheduled'),
 (4,1,date('now','localtime','+4 day'),'12:00','Chest pain','Scheduled'),
 (46,3,date('now','localtime','+4 day'),'09:30','Fever','Scheduled');

INSERT INTO admissions(patient_id, bed_id, doctor_id, admit_date, discharge_date, diagnosis) VALUES
 (9,2,11,date('now','localtime','-13 day'),date('now','localtime','-8 day'),'Viral fever'),
 (31,16,1,date('now','localtime','-49 day'),date('now','localtime','-42 day'),'Unstable angina'),
 (37,4,11,date('now','localtime','-17 day'),date('now','localtime','-12 day'),'Viral fever'),
 (6,18,7,date('now','localtime','-48 day'),date('now','localtime','-45 day'),'Stroke'),
 (37,10,10,date('now','localtime','-10 day'),date('now','localtime','-8 day'),'Dengue fever'),
 (12,3,4,date('now','localtime','-32 day'),date('now','localtime','-27 day'),'Diabetic ketoacidosis'),
 (1,20,7,date('now','localtime','-51 day'),date('now','localtime','-49 day'),'Stroke'),
 (41,11,5,date('now','localtime','-25 day'),date('now','localtime','-23 day'),'Respiratory failure'),
 (13,8,3,date('now','localtime','-38 day'),date('now','localtime','-32 day'),'Bronchiolitis'),
 (10,5,2,date('now','localtime','-21 day'),date('now','localtime','-15 day'),'Spinal injury'),
 (46,9,10,date('now','localtime','-46 day'),date('now','localtime','-39 day'),'Bronchiolitis'),
 (46,7,2,date('now','localtime','-20 day'),date('now','localtime','-16 day'),'Tibia fracture'),
 (27,21,8,date('now','localtime','-27 day'),date('now','localtime','-19 day'),'Preeclampsia'),
 (1,12,5,date('now','localtime','-23 day'),date('now','localtime','-16 day'),'Respiratory failure'),
 (39,10,10,date('now','localtime','-18 day'),date('now','localtime','-14 day'),'Pneumonia'),
 (10,7,9,date('now','localtime','-28 day'),date('now','localtime','-26 day'),'Femur fracture'),
 (41,17,7,date('now','localtime','-29 day'),date('now','localtime','-25 day'),'Meningitis'),
 (29,2,4,date('now','localtime','-13 day'),date('now','localtime','-9 day'),'Typhoid'),
 (23,22,8,date('now','localtime','-21 day'),date('now','localtime','-15 day'),'C-section recovery'),
 (32,7,2,date('now','localtime','-10 day'),date('now','localtime','-3 day'),'Hip replacement'),
 (3,17,7,date('now','localtime','-42 day'),date('now','localtime','-34 day'),'Meningitis'),
 (13,21,8,date('now','localtime','-23 day'),date('now','localtime','-21 day'),'Preeclampsia'),
 (16,17,7,date('now','localtime','-53 day'),date('now','localtime','-48 day'),'Status epilepticus'),
 (45,7,9,date('now','localtime','-43 day'),date('now','localtime','-39 day'),'Spinal injury'),
 (47,19,7,date('now','localtime','-14 day'),date('now','localtime','-7 day'),'Status epilepticus'),
 (47,16,1,date('now','localtime','-52 day'),date('now','localtime','-50 day'),'Heart failure'),
 (23,5,2,date('now','localtime','-4 day'),NULL,'Tibia fracture'),
 (17,17,7,date('now','localtime','+0 day'),NULL,'Stroke'),
 (21,13,5,date('now','localtime','-8 day'),NULL,'Head trauma'),
 (16,4,11,date('now','localtime','-2 day'),NULL,'Viral fever'),
 (12,12,5,date('now','localtime','-3 day'),NULL,'Post-op ICU care'),
 (22,19,7,date('now','localtime','-4 day'),NULL,'Status epilepticus'),
 (42,22,8,date('now','localtime','-6 day'),NULL,'C-section recovery'),
 (36,2,11,date('now','localtime','-3 day'),NULL,'Dengue fever'),
 (28,21,8,date('now','localtime','-6 day'),NULL,'C-section recovery'),
 (31,7,2,date('now','localtime','-8 day'),NULL,'Spinal injury'),
 (33,20,7,date('now','localtime','-5 day'),NULL,'Meningitis');

INSERT INTO resources(name, category, quantity, min_level, unit_cost, dept_id) VALUES
 ('Ventilator','Equipment',12,3,450000,5),
 ('ECG Machine','Equipment',8,2,120000,1),
 ('Wheelchair','Equipment',19,5,6500,4),
 ('Defibrillator','Equipment',9,2,180000,1),
 ('Paracetamol 500mg','Medicine',418,100,2,4),
 ('Insulin Vial','Medicine',27,20,350,4),
 ('Amoxicillin 250mg','Medicine',184,80,6,3),
 ('Pediatric Syrup','Medicine',80,30,95,3),
 ('Aspirin 75mg','Medicine',65,60,3,1),
 ('Surgical Gloves (box)','Consumable',50,40,250,2),
 ('IV Fluid Bag','Consumable',47,50,80,5),
 ('Syringe 5ml (pack)','Consumable',135,50,120,4),
 ('Cotton Roll','Consumable',122,40,45,2),
 ('Plaster Bandage','Consumable',35,25,160,2),
 ('Oxygen Cylinder','Equipment',9,8,4500,5);

INSERT INTO resource_usage(res_id, patient_id, qty, used_on) VALUES
 (4,48,1,date('now','localtime','-21 day')),
 (9,13,2,date('now','localtime','-17 day')),
 (3,30,1,date('now','localtime','-11 day')),
 (4,15,1,date('now','localtime','-19 day')),
 (10,30,7,date('now','localtime','-29 day')),
 (1,47,1,date('now','localtime','-18 day')),
 (12,41,2,date('now','localtime','-2 day')),
 (5,22,8,date('now','localtime','-4 day')),
 (13,34,7,date('now','localtime','-32 day')),
 (7,21,12,date('now','localtime','-26 day')),
 (2,45,1,date('now','localtime','-17 day')),
 (2,4,1,date('now','localtime','-33 day')),
 (14,16,3,date('now','localtime','-20 day')),
 (13,21,10,date('now','localtime','-14 day')),
 (5,44,10,date('now','localtime','-17 day')),
 (1,19,1,date('now','localtime','-10 day')),
 (10,31,5,date('now','localtime','-17 day')),
 (8,46,9,date('now','localtime','-4 day')),
 (13,9,9,date('now','localtime','-17 day')),
 (13,26,5,date('now','localtime','+0 day')),
 (3,6,1,date('now','localtime','-39 day')),
 (6,36,7,date('now','localtime','+0 day')),
 (12,1,9,date('now','localtime','-4 day')),
 (1,46,1,date('now','localtime','-2 day')),
 (11,41,6,date('now','localtime','-8 day')),
 (1,32,1,date('now','localtime','-3 day')),
 (13,38,1,date('now','localtime','-6 day')),
 (8,13,1,date('now','localtime','-38 day')),
 (3,13,1,date('now','localtime','-14 day')),
 (1,29,1,date('now','localtime','-2 day')),
 (4,20,1,date('now','localtime','-33 day')),
 (9,29,8,date('now','localtime','-33 day')),
 (12,27,2,date('now','localtime','-25 day')),
 (14,7,2,date('now','localtime','-19 day')),
 (7,23,4,date('now','localtime','-5 day')),
 (2,12,1,date('now','localtime','-1 day')),
 (4,16,1,date('now','localtime','-2 day')),
 (1,1,1,date('now','localtime','-40 day')),
 (4,1,1,date('now','localtime','-19 day')),
 (3,13,1,date('now','localtime','-28 day')),
 (2,32,1,date('now','localtime','-6 day')),
 (6,12,6,date('now','localtime','-37 day')),
 (4,6,1,date('now','localtime','-8 day')),
 (7,3,8,date('now','localtime','-32 day')),
 (12,10,2,date('now','localtime','-38 day')),
 (14,31,8,date('now','localtime','-1 day'));


-- Report queries


-- Appointment schedule   [JOIN (4 tables)]
SELECT a.appt_id, a.appt_date, a.appt_time, p.name AS patient,
       d.name AS doctor, dep.name AS department, a.status
FROM appointments a
JOIN patients p     ON p.patient_id = a.patient_id
JOIN doctors d      ON d.doctor_id  = a.doctor_id
JOIN departments dep ON dep.dept_id = d.dept_id
ORDER BY a.appt_date, a.appt_time;


-- Doctor workload   [LEFT JOIN + COUNT + GROUP BY]
SELECT d.name AS doctor, d.specialization,
       COUNT(a.appt_id) AS total_appointments,
       COALESCE(SUM(a.status = 'Completed'), 0) AS completed,
       COALESCE(SUM(a.status = 'Scheduled'), 0) AS upcoming
FROM doctors d
LEFT JOIN appointments a ON a.doctor_id = d.doctor_id
GROUP BY d.doctor_id
ORDER BY total_appointments DESC;


-- Bed occupancy by department   [Aggregates + HAVING]
SELECT dep.name AS department,
       COUNT(b.bed_id) AS total_beds,
       SUM(b.status = 'Occupied')    AS occupied,
       SUM(b.status = 'Available')   AS available,
       SUM(b.status = 'Maintenance') AS maintenance,
       ROUND(100.0 * SUM(b.status = 'Occupied') / COUNT(b.bed_id), 1) AS occupancy_pct
FROM departments dep
JOIN beds b ON b.dept_id = dep.dept_id
GROUP BY dep.dept_id
HAVING COUNT(b.bed_id) > 0
ORDER BY occupancy_pct DESC;


-- Current inpatients with running bill   [JOIN + date arithmetic]
SELECT p.name AS patient, b.ward || '-' || b.bed_no AS bed, b.bed_type,
       d.name AS doctor, ad.admit_date,
       CAST(julianday('now','localtime') - julianday(ad.admit_date) AS INTEGER) + 1 AS days_stayed,
       (CAST(julianday('now','localtime') - julianday(ad.admit_date) AS INTEGER) + 1)
         * b.daily_charge AS bed_bill
FROM admissions ad
JOIN patients p ON p.patient_id = ad.patient_id
JOIN beds b     ON b.bed_id     = ad.bed_id
JOIN doctors d  ON d.doctor_id  = ad.doctor_id
WHERE ad.discharge_date IS NULL
ORDER BY bed_bill DESC;


-- Patients with above-average visits   [Subquery in HAVING]
SELECT p.name AS patient, COUNT(*) AS appointments
FROM patients p
JOIN appointments a ON a.patient_id = p.patient_id
GROUP BY p.patient_id
HAVING COUNT(*) > (SELECT AVG(c) FROM
                    (SELECT COUNT(*) AS c FROM appointments GROUP BY patient_id))
ORDER BY appointments DESC;


-- Doctors with no appointments   [Subquery (NOT IN)]
SELECT name, specialization, phone
FROM doctors
WHERE doctor_id NOT IN (SELECT doctor_id FROM appointments);


-- Patients never admitted   [Correlated subquery (NOT EXISTS)]
SELECT p.patient_id, p.name, p.age, p.phone
FROM patients p
WHERE NOT EXISTS (SELECT 1 FROM admissions ad
                  WHERE ad.patient_id = p.patient_id);


-- Costliest available bed   [Subquery with MAX]
SELECT bed_id, ward, bed_no, bed_type, daily_charge
FROM beds
WHERE status = 'Available'
  AND daily_charge = (SELECT MAX(daily_charge) FROM beds
                      WHERE status = 'Available');


-- Low-stock resources   [WHERE + LEFT JOIN]
SELECT r.name, r.category, r.quantity, r.min_level,
       r.min_level - r.quantity AS shortfall, dep.name AS department
FROM resources r
LEFT JOIN departments dep ON dep.dept_id = r.dept_id
WHERE r.quantity <= r.min_level
ORDER BY shortfall DESC;


-- Resource cost by department   [JOIN + SUM]
SELECT dep.name AS department, COUNT(u.usage_id) AS issues,
       SUM(u.qty) AS units_used, SUM(u.qty * r.unit_cost) AS total_cost
FROM resource_usage u
JOIN resources r     ON r.res_id  = u.res_id
JOIN departments dep ON dep.dept_id = r.dept_id
GROUP BY dep.dept_id
ORDER BY total_cost DESC;


-- Consultation revenue by department   [JOIN + SUM + HAVING]
SELECT dep.name AS department, COUNT(*) AS completed_visits,
       SUM(d.fee) AS revenue, ROUND(AVG(d.fee), 2) AS avg_fee
FROM appointments a
JOIN doctors d       ON d.doctor_id = a.doctor_id
JOIN departments dep ON dep.dept_id = d.dept_id
WHERE a.status = 'Completed'
GROUP BY dep.dept_id
HAVING SUM(d.fee) > 0
ORDER BY revenue DESC;


-- Average length of stay (discharged)   [AVG + date functions]
SELECT dep.name AS department, COUNT(*) AS discharges,
       ROUND(AVG(julianday(ad.discharge_date) - julianday(ad.admit_date)), 1)
         AS avg_days_stay
FROM admissions ad
JOIN doctors d       ON d.doctor_id = ad.doctor_id
JOIN departments dep ON dep.dept_id = d.dept_id
WHERE ad.discharge_date IS NOT NULL
GROUP BY dep.dept_id
ORDER BY avg_days_stay DESC;


-- Complete patient history   [UNION ALL]
SELECT p.name AS patient, 'Appointment' AS event, a.appt_date AS event_date,
       a.reason AS detail
FROM appointments a JOIN patients p ON p.patient_id = a.patient_id
UNION ALL
SELECT p.name, 'Admission', ad.admit_date, ad.diagnosis
FROM admissions ad JOIN patients p ON p.patient_id = ad.patient_id
ORDER BY patient, event_date;


-- View: v_current_inpatients   [VIEW]
SELECT * FROM v_current_inpatients;
