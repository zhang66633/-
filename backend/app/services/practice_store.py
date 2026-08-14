"""练习记录与错题本存储 — SQLite 持久化(重启不清零)。

沿用 sqlite_session_store 的 threading.local 每线程连接模式。
表 practice_records: 每次作答一条记录,错题以「同题最新一次作答正确」判定掌握。
"""

from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS practice_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL DEFAULT 'default',
    question_id TEXT NOT NULL,
    choice INTEGER NOT NULL,
    is_correct INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_practice_user_qid
    ON practice_records(user_id, question_id, created_at);
"""


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class PracticeStore:
    """选择题作答记录/错题本存储。"""

    def __init__(self, db_path: Path):
        self._db_path = db_path
        self._lock = threading.Lock()
        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn = conn
        return conn

    def _init_db(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with self._get_conn() as conn:
                conn.executescript(SCHEMA_SQL)
                conn.commit()

    # ── 记录 ─────────────────────────────────────────────

    def record_answer(
        self,
        question_id: str,
        choice: int,
        is_correct: bool,
        user_id: str = "default",
    ) -> None:
        with self._lock:
            with self._get_conn() as conn:
                conn.execute(
                    "INSERT INTO practice_records(user_id, question_id, choice, is_correct, created_at)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (user_id, question_id, choice, int(is_correct), _utcnow()),
                )
                conn.commit()

    # ── 错题本 ───────────────────────────────────────────

    def get_wrong_question_ids(self, user_id: str = "default") -> set[str]:
        """当前处于「错题」状态的题目 id 集合(最新一次作答错误)。"""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT question_id, is_correct FROM practice_records"
                " WHERE user_id = ?"
                " ORDER BY id DESC",
                (user_id,),
            ).fetchall()
        latest: dict[str, bool] = {}
        for row in rows:
            latest.setdefault(row["question_id"], bool(row["is_correct"]))
        return {qid for qid, ok in latest.items() if not ok}

    def get_mistake_detail(self, question_id: str, user_id: str = "default") -> Optional[dict[str, Any]]:
        """某题的错题详情(最后一次错误作答)。"""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT choice, is_correct, created_at FROM practice_records"
                " WHERE user_id = ? AND question_id = ? AND is_correct = 0"
                " ORDER BY id DESC LIMIT 1",
                (user_id, question_id),
            ).fetchone()
        return dict(row) if row else None

    def get_wrong_count(self, question_id: str, user_id: str = "default") -> int:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM practice_records"
                " WHERE user_id = ? AND question_id = ? AND is_correct = 0",
                (user_id, question_id),
            ).fetchone()
        return int(row["n"])

    def get_correct_count(self, question_id: str, user_id: str = "default") -> int:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM practice_records"
                " WHERE user_id = ? AND question_id = ? AND is_correct = 1",
                (user_id, question_id),
            ).fetchone()
        return int(row["n"])

    def get_wrong_counts(self, user_id: str = "default") -> dict[str, int]:
        """每道题的累计错误次数(一次查询,供题库列表批量标注)。"""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT question_id, COUNT(*) AS n FROM practice_records"
                " WHERE user_id = ? AND is_correct = 0"
                " GROUP BY question_id",
                (user_id,),
            ).fetchall()
        return {r["question_id"]: int(r["n"]) for r in rows}

    def get_tried_ids(self, user_id: str = "default") -> set[str]:
        """作答过的全部题目 id。"""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT DISTINCT question_id FROM practice_records WHERE user_id = ?",
                (user_id,),
            ).fetchall()
        return {r["question_id"] for r in rows}

    def get_stats(self, user_id: str = "default") -> dict[str, Any]:
        """统计: 总作答次数 / 作对次数 / 错题数 / 已掌握题数。"""
        with self._get_conn() as conn:
            total = conn.execute(
                "SELECT COUNT(*) AS n FROM practice_records WHERE user_id = ?",
                (user_id,),
            ).fetchone()["n"]
            correct = conn.execute(
                "SELECT COUNT(*) AS n FROM practice_records"
                " WHERE user_id = ? AND is_correct = 1",
                (user_id,),
            ).fetchone()["n"]
        wrong_ids = self.get_wrong_question_ids(user_id)
        tried_ids: set[str] = set()
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT DISTINCT question_id FROM practice_records WHERE user_id = ?",
                (user_id,),
            ).fetchall()
            tried_ids = {r["question_id"] for r in rows}
        return {
            "total_answers": total,
            "correct_answers": correct,
            "wrong_questions": len(wrong_ids),
            "mastered_questions": len(tried_ids - wrong_ids),
        }


_store: Optional[PracticeStore] = None


def get_practice_store() -> PracticeStore:
    """全局单例,DB 位于项目 data/ 目录。"""
    global _store
    if _store is None:
        from ..config import get_settings

        settings = get_settings()
        db_path = settings.project_root / "data" / "practice.db"
        _store = PracticeStore(db_path=db_path)
    return _store
