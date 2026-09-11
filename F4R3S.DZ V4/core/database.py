#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""F4R3S.DZ – Database Manager"""

import sqlite3
import os

class DatabaseManager:
    def __init__(self, db_path='database/scans.db'):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = self._get_conn()
        conn.execute('''CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target TEXT, status TEXT, results TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()