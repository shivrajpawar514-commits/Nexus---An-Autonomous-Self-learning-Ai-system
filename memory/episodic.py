"""Episodic memory backed by SQLite for structured, persistent execution traces."""

from __future__ import annotations
import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from memory.db import DatabaseAdapter, DATABASE_URL

DB_PATH = Path("episodes.db").resolve()


class EpisodeRecord(BaseModel):
    id: Optional[int] = None
    goal: str
    plan_json: str
    trajectory_json: str
    passed: bool
    score: float
    total_steps: int
    total_tokens: int
    duration_sec: float
    created_at: float = 0.0


class EpisodicMemory:
    def __init__(self, db_path: Optional[Path] = None, db_url: Optional[str] = None):
        self.db_path = db_path or DB_PATH
        self.db_adapter = DatabaseAdapter(db_url=db_url or (f"sqlite:///{self.db_path}" if db_path else DATABASE_URL))
        self.db_adapter.init_schema()

    def _get_connection(self):
        return self.db_adapter.get_connection()

    def _init_db(self):
        self.db_adapter.init_schema()

    def record_episode(
        self,
        goal: str,
        plan: Any,
        trajectory: Any,
        passed: bool,
        score: float,
        total_steps: int,
        total_tokens: int,
        duration_sec: float,
    ) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        plan_str = json.dumps(
            plan.model_dump() if hasattr(plan, "model_dump")
            else (plan if isinstance(plan, (dict, list)) else getattr(plan, "dict", lambda: str(plan))())
        )
        traj_str = json.dumps(
            [t.model_dump() if hasattr(t, "model_dump") else (t.dict() if hasattr(t, "dict") else str(t)) for t in trajectory]
            if isinstance(trajectory, list)
            else str(trajectory)
        )
        now = time.time()
        cursor.execute(
            """
            INSERT INTO episodes (goal, plan_json, trajectory_json, passed, score, total_steps, total_tokens, duration_sec, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (goal, plan_str, traj_str, passed, score, total_steps, total_tokens, duration_sec, now),
        )
        ep_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return ep_id

    def get_recent_episodes(self, limit: int = 10) -> List[EpisodeRecord]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, goal, plan_json, trajectory_json, passed, score, total_steps, total_tokens, duration_sec, created_at FROM episodes ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        rows = cursor.fetchall()
        conn.close()
        return [
            EpisodeRecord(
                id=r[0],
                goal=r[1],
                plan_json=r[2],
                trajectory_json=r[3],
                passed=bool(r[4]),
                score=r[5],
                total_steps=r[6],
                total_tokens=r[7],
                duration_sec=r[8],
                created_at=r[9],
            )
            for r in rows
        ]

    def get_summary_stats(self) -> Dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                COUNT(*),
                AVG(passed),
                AVG(total_steps),
                AVG(total_tokens),
                AVG(duration_sec)
            FROM episodes
            """
        )
        row = cursor.fetchone()
        conn.close()
        total_runs = row[0] or 0
        if total_runs == 0:
            return {"total_runs": 0, "total_episodes": 0, "success_rate": 0.0, "avg_steps": 0.0, "avg_tokens": 0.0}

        return {
            "total_runs": total_runs,
            "total_episodes": total_runs,
            "success_rate": round(row[1] or 0.0, 3),
            "avg_steps": round(row[2] or 0.0, 2),
            "avg_tokens": round(row[3] or 0.0, 1),
            "avg_duration_sec": round(row[4] or 0.0, 2),
        }
