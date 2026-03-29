#!/usr/bin/env python3
"""
SQLite to MySQL Migration Script for personalmemo

Usage:
    1. Make sure MySQL is running and accessible
    2. Set environment variables or edit MYSQL_CONFIG below
    3. Run: python migrate_to_mysql.py

Environment Variables:
    MEMO_MYSQL_HOST     - MySQL host (default: localhost)
    MEMO_MYSQL_PORT     - MySQL port (default: 3306)
    MEMO_MYSQL_USER     - MySQL user (default: root)
    MEMO_MYSQL_PASSWORD - MySQL password (default: empty)
    MEMO_MYSQL_DATABASE - Database name (default: personalmemo)
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import pymysql

# Configuration
SQLITE_DB_PATH = Path(__file__).resolve().parent / "personalmemo.db"
SQLITE_MEMOS_JSON = Path(__file__).resolve().parent / "memos.json"

MYSQL_CONFIG = {
    "host": os.environ.get("MEMO_MYSQL_HOST", "localhost"),
    "port": int(os.environ.get("MEMO_MYSQL_PORT", "3306")),
    "user": os.environ.get("MEMO_MYSQL_USER", "root"),
    "password": os.environ.get("MEMO_MYSQL_PASSWORD", ""),
    "database": os.environ.get("MEMO_MYSQL_DATABASE", "personalmemo"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}


def create_database_and_table():
    """Create database and table if they don't exist."""
    init_config = MYSQL_CONFIG.copy()
    db_name = init_config.pop("database")
    
    # Connect without database
    conn = pymysql.connect(**init_config)
    try:
        with conn.cursor() as cursor:
            print(f"[1/4] Creating database '{db_name}' if not exists...")
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit()
        print(f"      Database ready.")
    finally:
        conn.close()
    
    # Connect to database and create table
    conn = pymysql.connect(**MYSQL_CONFIG)
    try:
        with conn.cursor() as cursor:
            print(f"[2/4] Creating memos table if not exists...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memos (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    content TEXT NOT NULL,
                    timestamp VARCHAR(64) NOT NULL,
                    metadata JSON,
                    deleted TINYINT DEFAULT 0,
                    deleted_at VARCHAR(64),
                    INDEX idx_deleted (deleted),
                    INDEX idx_timestamp (timestamp)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
        conn.commit()
        print(f"      Table ready.")
    finally:
        conn.close()


def load_from_sqlite() -> list:
    """Load memos from SQLite database."""
    if not SQLITE_DB_PATH.exists():
        print(f"[WARN] SQLite DB not found at {SQLITE_DB_PATH}")
        return []
    
    print(f"[3/4] Loading memos from SQLite: {SQLITE_DB_PATH}")
    conn = sqlite3.connect(str(SQLITE_DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, content, timestamp, metadata, deleted FROM memos')
    rows = cursor.fetchall()
    
    memos = []
    for row in rows:
        metadata = row["metadata"]
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        memos.append({
            "id": row["id"],
            "content": row["content"],
            "timestamp": row["timestamp"],
            "metadata": metadata or {},
            "deleted": row["deleted"],
            "deleted_at": row["deleted_at"],
        })
    
    conn.close()
    print(f"      Loaded {len(memos)} memos from SQLite.")
    return memos


def export_to_mysql(memos: list):
    """Export memos to MySQL."""
    print(f"[4/4] Exporting memos to MySQL...")
    
    conn = pymysql.connect(**MYSQL_CONFIG)
    try:
        with conn.cursor() as cursor:
            for memo in memos:
                cursor.execute('''
                    INSERT INTO memos (id, content, timestamp, metadata, deleted, deleted_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    memo["id"],
                    memo["content"],
                    memo["timestamp"],
                    json.dumps(memo["metadata"], ensure_ascii=False),
                    memo.get("deleted", 0),
                    memo.get("deleted_at"),
                ))
        conn.commit()
        print(f"      Exported {len(memos)} memos to MySQL.")
    finally:
        conn.close()


def verify_migration():
    """Verify the migration was successful."""
    print(f"\n[VERIFY] Checking MySQL data...")
    
    # Load from MySQL
    conn = pymysql.connect(**MYSQL_CONFIG)
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) as count FROM memos WHERE deleted = 0')
            active_count = cursor.fetchone()["count"]
            
            cursor.execute('SELECT COUNT(*) as count FROM memos WHERE deleted = 1')
            deleted_count = cursor.fetchone()["count"]
            
            cursor.execute('SELECT id, content, timestamp FROM memos WHERE deleted = 0 ORDER BY id DESC LIMIT 3')
            recent = cursor.fetchall()
    finally:
        conn.close()
    
    print(f"      Active memos: {active_count}")
    print(f"      Deleted memos: {deleted_count}")
    print(f"      Most recent 3:")
    for r in recent:
        print(f"        - #{r['id']}: {r['content'][:50]}...")
    
    return active_count, deleted_count


def main():
    print("=" * 50)
    print("  personalmemo: SQLite → MySQL Migration")
    print("=" * 50)
    print()
    
    # Check MySQL connection
    print("Checking MySQL connection...")
    try:
        test_conn = pymysql.connect(
            host=MYSQL_CONFIG["host"],
            port=MYSQL_CONFIG["port"],
            user=MYSQL_CONFIG["user"],
            password=MYSQL_CONFIG["password"],
            connect_timeout=5,
        )
        test_conn.close()
        print(f"✓ MySQL connection OK ({MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']})")
    except Exception as e:
        print(f"✗ MySQL connection failed: {e}")
        print("\nPlease check:")
        print("  1. MySQL server is running")
        print("  2. Environment variables are set correctly")
        print("  3. User has permissions")
        sys.exit(1)
    
    print()
    
    # Run migration
    create_database_and_table()
    memos = load_from_sqlite()
    
    if memos:
        export_to_mysql(memos)
    else:
        print("[SKIP] No memos to migrate.")
    
    print()
    verify_migration()
    
    print()
    print("=" * 50)
    print("  Migration complete!")
    print("=" * 50)
    print()
    print("Next steps:")
    print("  1. Update your environment variables for production:")
    print("     export MEMO_MYSQL_HOST=your_mysql_host")
    print("     export MEMO_MYSQL_USER=your_user")
    print("     export MEMO_MYSQL_PASSWORD=your_password")
    print("     export MEMO_MYSQL_DATABASE=personalmemo")
    print()
    print("  2. Use server_mysql.py instead of server.py:")
    print("     python server_mysql.py")


if __name__ == "__main__":
    main()
