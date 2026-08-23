"""Session manager — task CRUD with optional JSON persistence.

Provides a SessionManager class to replace the in-memory dict in the API router.
"""

from __future__ import annotations

import json
import logging
import threading
from datetime import UTC, datetime
from pathlib import Path

from app.config import get_settings

logger = logging.getLogger(__name__)


class SessionManager:
    """Thread-safe task session store with optional JSON persistence and cancellation support.

    Usage:
        manager = SessionManager(persist_path=Path("data/sessions.json"))
        task = manager.create(problem="...", mode="execute")
        manager.update(task_id, status="completed", final_response="...")
        manager.cancel(task_id)  # sets cancel event, stops orchestrator
    """

    def __init__(self, persist_path: Path | None = None):
        # RLock 而非 Lock：cancel() 曾持锁调用 get_cancel_event() 二次抢锁，
        # 非重入锁直接自死锁，把 uvicorn 单 worker 主循环永久卡死（py-spy 实锤）。
        # 可重入锁是防御底线，嵌套取锁的结构问题在 cancel() 内另行消除。
        self._lock = threading.RLock()
        self._tasks: dict[str, dict] = {}
        self._cancel_events: dict[str, threading.Event] = {}
        self._persist_path = persist_path

        # Load existing sessions if persist file exists
        if self._persist_path and self._persist_path.exists():
            self._load()

    # ── CRUD ───────────────────────────────────────────────────────

    def create(self, problem: str, mode: str = "execute") -> dict:
        """Create a new task and return its dict."""
        import uuid

        task_id = str(uuid.uuid4())[:8]
        now = datetime.now(UTC).isoformat()

        task = {
            "task_id": task_id,
            "status": "running",
            "problem": problem,
            "mode": mode,
            "final_response": None,
            "messages": [],
            "artifacts": [],  # 文件区：上传的附件 + 生成的图表/结果文件
            "created_at": now,
            "updated_at": now,
        }

        with self._lock:
            self._tasks[task_id] = task
        self._save()

        return task

    def add_artifact(self, task_id: str, artifact: dict) -> dict | None:
        """向任务的文件区追加一个文件记录。

        artifact 形如:
          {"type": "uploaded"|"figure"|"result", "name": 文件名,
           "url": 访问地址, "size": 字节数(可选)}
        同 name+url 已存在则跳过，避免重复。
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            arts = task.setdefault("artifacts", [])
            if any(
                a.get("name") == artifact.get("name") and a.get("url") == artifact.get("url")
                for a in arts
            ):
                return task
            arts.append(artifact)
            task["updated_at"] = datetime.now(UTC).isoformat()
            self._save()
            return task

    def get(self, task_id: str) -> dict | None:
        """Get a task by ID (returns None if not found)."""
        with self._lock:
            return self._tasks.get(task_id)

    def list_all(self) -> list[dict]:
        """List all tasks."""
        with self._lock:
            return list(self._tasks.values())

    def update(self, task_id: str, **fields) -> dict | None:
        """Update task fields. Returns updated task or None."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            fields["updated_at"] = datetime.now(UTC).isoformat()
            task.update(fields)
        # 磁盘写在锁外（_save 内部只短暂持锁取内存快照）
        self._save()
        return task

    def delete(self, task_id: str) -> bool:
        """Delete a task. Returns True if it existed."""
        with self._lock:
            existed = task_id in self._tasks
            if existed:
                del self._tasks[task_id]
        if existed:
            self._save()
        return existed

    def cancel(self, task_id: str) -> bool:
        """Mark a task as cancelled and signal the orchestrator to stop.

        惰性创建取消事件——若取消请求早于编排器首次检查，信号不会丢失；
        否则任务会在最后被 update(status="completed") 覆盖回 completed。

        注意：这里必须内联操作 _cancel_events。曾通过 get_cancel_event()
        在持锁状态下二次抢锁，Lock 不可重入直接自死锁、uvicorn 主循环
        永久停摆（py-spy 实锤的事故）——勿改回嵌套调用。
        """
        with self._lock:
            event = self._cancel_events.setdefault(task_id, threading.Event())
            event.set()  # 通知后台编排器停止
            task = self._tasks.get(task_id)
            found = task is not None
            if found:
                task["status"] = "cancelled"
                task["updated_at"] = datetime.now(UTC).isoformat()
        self._save()
        return found

    def get_cancel_event(self, task_id: str) -> threading.Event:
        """Get or create a cancel event for a task.

        The orchestrator checks event.is_set() between nodes to abort early.
        """
        with self._lock:
            if task_id not in self._cancel_events:
                self._cancel_events[task_id] = threading.Event()
            return self._cancel_events[task_id]

    def cleanup_cancel_event(self, task_id: str):
        """Remove the cancel event after task completes."""
        with self._lock:
            self._cancel_events.pop(task_id, None)

    # ── persistence ────────────────────────────────────────────────

    def _save(self):
        """持久化会话。dumps 在锁内取一致性快照，磁盘写在锁外。

        write_text 是可能被杀毒软件/磁盘卡顿放大的系统 IO，绝不能持锁做——
        否则所有等 _lock 的线程（含 uvicorn 主循环里的端点）都会被 IO 卡顿
        连坐阻塞。
        """
        if not self._persist_path:
            return
        with self._lock:
            payload = json.dumps(self._tasks, ensure_ascii=False, indent=2)
        try:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            self._persist_path.write_text(payload, encoding="utf-8")
        except Exception:
            logger.warning("Failed to persist sessions", exc_info=True)

    def _load(self):
        try:
            data = json.loads(self._persist_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                self._tasks = data
                logger.info("Loaded %d sessions from %s", len(self._tasks), self._persist_path)
        except Exception:
            logger.warning("Failed to load sessions", exc_info=True)
            self._tasks = {}


# ── module-level singleton ──────────────────────────────────────────

_session_manager: SessionManager | None = None


def get_session_manager() -> SessionManager:
    """Get or create the global session manager."""
    global _session_manager
    if _session_manager is None:
        settings = get_settings()
        persist_path = settings.project_root / "data" / "sessions.json"
        _session_manager = SessionManager(persist_path=persist_path)
    return _session_manager
