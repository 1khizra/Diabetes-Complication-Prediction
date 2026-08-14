import sqlite3
from datetime import datetime

DB_NAME = "patients.db"

def connect():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


# ================= SAFE COLUMN ADD =================
def safe_add_column(cur, table, column, col_type):
    try:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
    except:
        pass


# ================= CREATE TABLE =================
def create_table():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT,
        age INTEGER,
        gender TEXT,
        contact TEXT,

        stage TEXT,
        type TEXT,

        bmi REAL,
        fbs REAL,
        hba1c REAL,
        ldl REAL,
        hdl REAL,

        pregnant REAL,
        history_gdm REAL,
        insulin REAL,
        triglycerides REAL,
        dm_duration REAL,
        onset_age REAL,
        antigad REAL,
        ia2a REAL,
        ica REAL,
        smoker REAL,
        urea REAL,
        creatinine REAL,

        egfr REAL,
        systolic_bp REAL,
        diastolic_bp REAL,

        complications TEXT,
        recommendations TEXT,

        date TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient TEXT,
        doctor TEXT,
        type TEXT,
        date TEXT,
        time TEXT,
        status TEXT,
        phone TEXT,
        room TEXT
    )
    """)

    # ================= SAFE UPGRADES =================
    safe_add_column(cur, "patients", "complications", "TEXT")
    safe_add_column(cur, "patients", "recommendations", "TEXT")

    conn.commit()
    conn.close()


# ================= INSERT / UPDATE =================
def add_patient(patient):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT id FROM patients
        WHERE name=? AND contact=?
        ORDER BY id DESC LIMIT 1
    """, (
        patient.get("Name"),
        patient.get("Contact")
    ))

    existing = cur.fetchone()

    recommendations = patient.get("Recommendations", "")
    if isinstance(recommendations, list):
        recommendations = ", ".join(recommendations)

    if existing:

        patient_id = existing[0]

        cur.execute("""
            UPDATE patients SET
                age=?,
                gender=?,
                stage=?,
                type=?,

                bmi=?,
                fbs=?,
                hba1c=?,
                ldl=?,
                hdl=?,

                pregnant=?,
                history_gdm=?,
                insulin=?,
                triglycerides=?,
                dm_duration=?,
                onset_age=?,
                antigad=?,
                ia2a=?,
                ica=?,
                smoker=?,
                urea=?,
                creatinine=?,

                egfr=?,
                systolic_bp=?,
                diastolic_bp=?,

                complications=?,
                recommendations=?,

                date=?

            WHERE id=?
        """, (
            patient.get("Age"),
            patient.get("Gender"),
            patient.get("Stage"),
            patient.get("Type"),

            patient.get("BMI"),
            patient.get("FBS"),
            patient.get("HbA1c"),
            patient.get("LDL"),
            patient.get("HDL"),

            patient.get("Pregnant"),
            patient.get("HistoryOfGDM"),
            patient.get("InsulinTotalUnits"),
            patient.get("Triglycerides"),
            patient.get("DMDuration"),
            patient.get("DMonSetAge"),
            patient.get("AntiGad"),
            patient.get("IA2A"),
            patient.get("ICA"),
            patient.get("Smoker"),
            patient.get("Urea"),
            patient.get("Creatinine"),

            patient.get("EGFR"),
            patient.get("SystolicBP"),
            patient.get("DiastolicBP"),

            patient.get("Complications"),
            recommendations,

            datetime.now().strftime("%Y-%m-%d"),
            patient_id
        ))

    else:

        cur.execute("""
            INSERT INTO patients (
                name, age, gender, contact,
                stage, type,
                bmi, fbs, hba1c, ldl, hdl,

                pregnant, history_gdm, insulin,
                triglycerides, dm_duration, onset_age,
                antigad, ia2a, ica, smoker,
                urea, creatinine,

                egfr, systolic_bp, diastolic_bp,

                complications, recommendations, date
            )
            VALUES (
                ?, ?, ?, ?,
                ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?,
                ?, ?, ?,
                ?, ?, ?
            )
        """, (
            patient.get("Name"),
            patient.get("Age"),
            patient.get("Gender"),
            patient.get("Contact"),

            patient.get("Stage"),
            patient.get("Type"),

            patient.get("BMI"),
            patient.get("FBS"),
            patient.get("HbA1c"),
            patient.get("LDL"),
            patient.get("HDL"),

            patient.get("Pregnant"),
            patient.get("HistoryOfGDM"),
            patient.get("InsulinTotalUnits"),
            patient.get("Triglycerides"),
            patient.get("DMDuration"),
            patient.get("DMonSetAge"),
            patient.get("AntiGad"),
            patient.get("IA2A"),
            patient.get("ICA"),
            patient.get("Smoker"),
            patient.get("Urea"),
            patient.get("Creatinine"),

            patient.get("EGFR"),
            patient.get("SystolicBP"),
            patient.get("DiastolicBP"),

            patient.get("Complications"),
            recommendations,
            datetime.now().strftime("%Y-%m-%d")
        ))

    conn.commit()
    conn.close()


# ================= GET PATIENTS =================
def get_patients():
    conn = connect()
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(patients)")
    columns = [col[1] for col in cur.fetchall()]

    cur.execute("SELECT * FROM patients ORDER BY id DESC")
    rows = cur.fetchall()

    conn.close()

    result = []

    for r in rows:

        row_dict = dict(zip(columns, r))

        result.append({
            "ID": row_dict.get("id"),
            "Name": row_dict.get("name"),
            "Age": row_dict.get("age"),
            "Gender": row_dict.get("gender"),
            "Contact": row_dict.get("contact"),

            "Stage": row_dict.get("stage"),
            "Type": row_dict.get("type"),

            "BMI": row_dict.get("bmi"),
            "FBS": row_dict.get("fbs"),
            "HbA1c": row_dict.get("hba1c"),
            "LDL": row_dict.get("ldl"),
            "HDL": row_dict.get("hdl"),

            "Complications": row_dict.get("complications"),
            "Recommendations": row_dict.get("recommendations"),
            "Date": row_dict.get("date")
        })

    return result


# ================= GET SINGLE =================
def get_patient(pid):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM patients WHERE id=?", (pid,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "ID": row[0],
        "Name": row[1],
        "Age": row[2],
        "Gender": row[3],
        "Contact": row[4],
        "Stage": row[5],
        "Type": row[6],
        "BMI": row[7],
        "FBS": row[8],
        "HbA1c": row[9],
        "LDL": row[10],
        "HDL": row[11],
        "Pregnant": row[12],
        "HistoryOfGDM": row[13],
        "Insulin": row[14],
        "Triglycerides": row[15],
        "DMDuration": row[16],
        "OnsetAge": row[17],
        "AntiGad": row[18],
        "IA2A": row[19],
        "ICA": row[20],
        "Smoker": row[21],
        "Urea": row[22],
        "Creatinine": row[23],
        "EGFR": row[24],
        "SystolicBP": row[25],
        "DiastolicBP": row[26],
        "Complications": row[27],
        "Recommendations": row[28],
        "Date": row[29]
    }


# ================= DELETE =================
def delete_patient(pid):
    conn = connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM patients WHERE id=?", (pid,))
    conn.commit()
    conn.close()


def delete_multiple(ids):
    conn = connect()
    cur = conn.cursor()
    cur.executemany("DELETE FROM patients WHERE id=?", [(i,) for i in ids])
    conn.commit()
    conn.close()


# ================= APPOINTMENTS =================
def add_appointment(patient, doctor, type_, date, time, status, phone, room):
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO appointments (
            patient, doctor, type, date, time, status, phone, room
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (patient, doctor, type_, date, time, status, phone, room))
    conn.commit()
    conn.close()


def get_appointments():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM appointments ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


def update_appointment_status(app_id, status):
    conn = connect()
    cur = conn.cursor()
    cur.execute("UPDATE appointments SET status=? WHERE id=?", (status, app_id))
    conn.commit()
    conn.close()


def delete_appointment(app_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM appointments WHERE id=?", (app_id,))
    conn.commit()
    conn.close()


# ================= INIT =================
create_table()