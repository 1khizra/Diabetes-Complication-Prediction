import sqlite3
import hashlib
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")


# ================= HASH =================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# ================= CONNECTION =================
def conn():
    return sqlite3.connect(DB_PATH)


# ================= CREATE TABLE =================
def create_user_table():
    c = conn().cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    conn().commit()
    conn().close()


# ================= DEFAULT USERS =================
def create_default_users():
    db = conn()
    c = db.cursor()

    users = [
        ("admin", "admin123", "admin"),
        ("patient", "patient123", "patient")
    ]

    for username, password, role in users:
        c.execute("SELECT username FROM users WHERE username=?", (username,))
        if not c.fetchone():
            c.execute("""
                INSERT INTO users (username, password, role)
                VALUES (?, ?, ?)
            """, (username, hash_password(password), role))

    db.commit()
    db.close()

# ================= ADD NEW USER =================
def create_user(username, password, role):
    db = conn()
    c = db.cursor()

    try:
        c.execute("""
        INSERT INTO users (username, password, role)
        VALUES (?, ?, ?)
        """, (username, hash_password(password), role))

        db.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        db.close()

# ================= CHANGE PASSWORD =================
def change_password(username, new_password):

    db = conn()
    c = db.cursor()

    c.execute("""
        UPDATE users
        SET password=?
        WHERE username=?
    """, (hash_password(new_password), username))

    db.commit()
    db.close()

# ================= LOGIN =================
def login_user(username, password):
    db = conn()
    c = db.cursor()

    c.execute("""
    SELECT role FROM users
    WHERE username=? AND password=?
    """, (username, hash_password(password)))

    result = c.fetchone()
    db.close()

    if result:
        return result[0]
    return None