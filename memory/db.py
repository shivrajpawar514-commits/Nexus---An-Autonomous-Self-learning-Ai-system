"""Unified database adapter supporting SQLite and PostgreSQL + pgvector."""

from __future__ import annotations
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///episodes.db")


class DatabaseAdapter:
    """Database interface supporting local SQLite and production PostgreSQL."""

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or DATABASE_URL
        self.is_postgres = self.db_url.startswith("postgresql://") or self.db_url.startswith("postgres://")
        self.is_sqlite = not self.is_postgres
        self.sqlite_path = Path("episodes.db").resolve()
        if self.is_sqlite and ":///" in self.db_url:
            self.sqlite_path = Path(self.db_url.split(":///")[-1]).resolve()

    def get_connection(self):
        if self.is_postgres:
            try:
                import psycopg2
                return psycopg2.connect(self.db_url)
            except ImportError:
                # Fallback to local SQLite if psycopg2 is not installed
                return sqlite3.connect(self.sqlite_path)
        return sqlite3.connect(self.sqlite_path)

    def init_schema(self):
        """Initializes tables for episodes and pgvector embeddings."""
        conn = self.get_connection()
        cursor = conn.cursor()

        if self.is_postgres:
            try:
                # Enable pgvector extension if available
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS episodes (
                        id SERIAL PRIMARY KEY,
                        goal TEXT NOT NULL,
                        plan_json TEXT NOT NULL,
                        trajectory_json TEXT NOT NULL,
                        passed BOOLEAN NOT NULL,
                        score REAL NOT NULL,
                        total_steps INTEGER NOT NULL,
                        total_tokens INTEGER NOT NULL,
                        duration_sec REAL NOT NULL,
                        created_at REAL NOT NULL
                    );
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS semantic_memory (
                        id SERIAL PRIMARY KEY,
                        situation TEXT NOT NULL,
                        what_happened TEXT NOT NULL,
                        root_cause TEXT NOT NULL,
                        rule TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        trust_weight REAL NOT NULL,
                        embedding vector(384)
                    );
                    """
                )
                conn.commit()
                conn.close()
                return
            except Exception:
                pass

        # Standard SQLite Schema
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal TEXT NOT NULL,
                plan_json TEXT NOT NULL,
                trajectory_json TEXT NOT NULL,
                passed BOOLEAN NOT NULL,
                score REAL NOT NULL,
                total_steps INTEGER NOT NULL,
                total_tokens INTEGER NOT NULL,
                duration_sec REAL NOT NULL,
                created_at REAL NOT NULL
            );
            """
        )
        conn.commit()
        conn.close()

