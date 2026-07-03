"""SQLite setup for Task/Reminder store, Notes log, and Budget tracker."""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shundo.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, due_date TEXT,
        completed INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, agent TEXT NOT NULL, content TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS budget_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT NOT NULL, description TEXT,
        amount REAL NOT NULL, currency TEXT DEFAULT 'INR', created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()
    conn.close()


init_db()
