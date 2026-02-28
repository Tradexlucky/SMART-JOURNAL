"""
Database initialization and connection management
SQLite with WAL mode for better concurrent reads
"""

import sqlite3
import os
import logging

logger = logging.getLogger(__name__)
DB_PATH = os.getenv("DB_PATH", "swingtrader.db")


def get_db():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize all database tables."""
    conn = get_db()
    cur = conn.cursor()

    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            github_id TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL,
            email TEXT,
            avatar_url TEXT,
            role TEXT DEFAULT 'user',
            status TEXT DEFAULT 'pending',
            telegram_chat_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Login activity log
    cur.execute("""
        CREATE TABLE IF NOT EXISTS login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            ip_address TEXT,
            user_agent TEXT,
            login_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

# Algo scan results
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scan_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_date DATE NOT NULL,
            symbol TEXT NOT NULL,
            signal TEXT,
            price REAL,
            entry REAL,
            sl REAL,
            tp REAL,
            conditions_met TEXT,
            scanned_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Trading journal
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            trade_date DATE NOT NULL,
            symbol TEXT NOT NULL,
            direction TEXT DEFAULT 'LONG',
            entry_price REAL NOT NULL,
            stop_loss REAL NOT NULL,
            target_price REAL NOT NULL,
            exit_price REAL,
            quantity INTEGER,
            result TEXT,
            pnl REAL,
            r_multiple REAL,
            notes TEXT,
            screenshot_path TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # News cache
    cur.execute("""
        CREATE TABLE IF NOT EXISTS news_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            summary TEXT,
            url TEXT,
            source TEXT,
            published_at TEXT,
            fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create default admin if none exists
    cur.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
    if cur.fetchone()[0] == 0:
        admin_github = os.getenv("ADMIN_GITHUB_ID")
        if admin_github:
            cur.execute("""
                INSERT OR IGNORE INTO users (github_id, username, role, status)
                VALUES (?, 'admin', 'admin', 'approved')
            """, (admin_github,))

    conn.commit()
    conn.close()
    logger.info("Database initialized")
