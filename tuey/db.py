import sqlite3
import json
import os

# We'll store the cache and history in this DB.
DB_FILE = os.path.join(os.path.dirname(__file__), "cache.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            func_name TEXT,
            args TEXT,
            start_time TEXT,
            end_time TEXT,
            duration REAL,
            status TEXT,
            error_message TEXT,
            result BLOB,
            progress INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def get_cached_result(func_name, args):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    args_str = json.dumps(args)
    cursor.execute("SELECT result FROM history WHERE func_name = ? AND args = ? AND status = 'SUCCESS'", (func_name, args_str))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def cache_result(func_name, args, result):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    args_str = json.dumps(args)
    cursor.execute("REPLACE INTO history (func_name, args, result, status) VALUES (?, ?, ?, 'SUCCESS')",
                   (func_name, args_str, result))
    conn.commit()
    conn.close()

def log_task(func_name, args, start_time, status="PENDING", error_message=None):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    args_str = json.dumps(args)
    cursor.execute("""
        INSERT INTO history (func_name, args, start_time, status, error_message)
        VALUES (?, ?, ?, ?, ?)
    """, (func_name, args_str, start_time, status, error_message))
    conn.commit()
    conn.close()

def update_task(func_name, args, status, end_time=None, duration=None, error_message=None):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    args_str = json.dumps(args)
    query = """
        UPDATE history SET status = ?, end_time = ?, duration = ?, error_message = ?
        WHERE func_name = ? AND args = ? AND status = 'PENDING'
    """
    cursor.execute(query, (status, end_time, duration, error_message, func_name, args_str))
    conn.commit()
    conn.close()

def update_progress(func_name, args, progress):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    args_str = json.dumps(args)
    query = """
        UPDATE history SET progress = ? WHERE func_name = ? AND args = ? AND status = 'IN PROGRESS'
    """
    cursor.execute(query, (progress, func_name, args_str))
    conn.commit()
    conn.close()
