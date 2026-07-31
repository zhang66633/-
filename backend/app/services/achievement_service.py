"""成就计算服务 — 基于学习事件判定 8 种成就的解锁状态。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from ..learning.mastery_tracker import get_mastery_tracker
from ..learning.schemas import LearningEvent

ACHIEVEMENT_DEFS = [
    {
        "id": "first_practice",
        "name": "初出茅庐",
        "desc": "完成第一次建模练习",
        "icon": "🌱",
        "check": "first_practice",
    },
    {
        "id": "streak_7",
        "name": "坚持不懈",
        "desc": "连续学习 7 天",
        "icon": "🔥",
        "check": "streak_7",
    },
    {
        "id": "master_10",
        "name": "方法大师",
        "desc": "掌握 10 种建模方法",
        "icon": "🧠",
        "check": "master_10",
    },
    {
        "id": "full_solution",
        "name": "实战达人",
        "desc": "完成一次完整实战",
        "icon": "⚔️",
        "check": "full_solution",
    },
    {
        "id": "code_10",
        "name": "代码高手",
        "desc": "完成 10 道编程练习",
        "icon": "💻",
        "check": "code_10",
    },
    {
        "id": "first_paper",
        "name": "论文新星",
        "desc": "完成一次论文写作练习",
        "icon": "📄",
        "check": "first_paper",
    },
    {
        "id": "all_rounder",
        "name": "全能选手",
        "desc": "三个角色各完成 5 个单元",
        "icon": "🌟",
        "check": "all_rounder",
    },
    {
        "id": "grade_a",
        "name": "竞赛勇士",
        "desc": "在实战中取得 A 级评价",
        "icon": "🏆",
        "check": "grade_a",
    },
]


class AchievementService:
    """成就判定服务（无状态，纯计算）。"""

    def __init__(self):
        self._events: list[LearningEvent] = []
        self._records: list[dict] = []  # ExerciseRecord dicts

    def load_events(self, user_id: str) -> None:
        """加载用户的学习事件和练习记录（内存中，后续可持久化到 SQLite）。"""
        # TODO: 从 SQLite / JSON 文件加载历史事件
        pass

    def add_event(self, event: LearningEvent) -> None:
        self._events.append(event)

    def check_all(
        self,
        user_id: str = "default",
        extra: Optional[dict] = None,
    ) -> list[dict]:
        """返回所有成就的解锁状态列表。"""
        tracker = get_mastery_tracker()
        results = []

        for ach in ACHIEVEMENT_DEFS:
            unlocked = False
            check = ach["check"]

            if check == "first_practice":
                unlocked = any(
                    e.event_type == "practice" and e.score is not None
                    for e in self._events
                )
            elif check == "streak_7":
                unlocked = _calc_streak(self._events) >= 7
            elif check == "master_10":
                all_skills = tracker.skills.get(user_id, {})
                unlocked = sum(
                    1 for s in all_skills.values() if s.mastery >= 0.6
                ) >= 10
            elif check == "full_solution":
                unlocked = any(
                    e.event_type == "learn" and "实战" in (e.unit_id or "")
                    for e in self._events
                )
            elif check == "code_10":
                code_events = [
                    e for e in self._events
                    if e.event_type == "practice" and "code" in str(e.skill_ids).lower()
                ]
                unlocked = sum(
                    1 for e in code_events if (e.score or 0) >= 0.6
                ) >= 10
            elif check == "first_paper":
                unlocked = any(
                    e.event_type == "practice" and "writing" in str(e.skill_ids).lower()
                    for e in self._events
                )
            elif check == "all_rounder":
                # 三个角色各 >= 5 个单元完成
                modeler_count = _count_by_role(self._events, "modeler")
                programmer_count = _count_by_role(self._events, "programmer")
                writer_count = _count_by_role(self._events, "writer")
                unlocked = (
                    modeler_count >= 5
                    and programmer_count >= 5
                    and writer_count >= 5
                )
            elif check == "grade_a":
                unlocked = any(
                    (e.score or 0) >= 0.9 and "实战" in (e.unit_id or "")
                    for e in self._events
                )

            results.append({
                "id": ach["id"],
                "name": ach["name"],
                "desc": ach["desc"],
                "icon": ach["icon"],
                "unlocked": unlocked,
            })

        return results


def _calc_streak(events: list[LearningEvent]) -> int:
    """计算连续学习天数（从最近一天往前数）。"""
    if not events:
        return 0

    # 提取所有有活动的日期（按 UTC 日期去重）
    dates = sorted(
        {e.created_at.date() for e in events if e.created_at},
        reverse=True,
    )
    if not dates:
        return 0

    today = datetime.now(timezone.utc).date()
    if dates[0] < today:
        # 今天没学习，从最近一天开始算
        pass

    streak = 1
    for i in range(1, len(dates)):
        delta = (dates[i - 1] - dates[i]).days
        if delta == 1:
            streak += 1
        else:
            break
    return streak


def _count_by_role(events: list[LearningEvent], role: str) -> int:
    """统计某角色完成的单元数。"""
    completed = set()
    for e in events:
        if e.event_type in ("practice", "learn") and (e.score or 0) >= 0.6:
            completed.add(e.unit_id)
    # 简化：按 unit_id 前缀匹配角色
    return sum(
        1 for uid in completed
        if uid and uid.startswith(f"{role[:3]}_") or role in (uid or "")
    )


# ── 全局单例 ──────────────────────────────────────────

_service: Optional[AchievementService] = None


def get_achievement_service() -> AchievementService:
    global _service
    if _service is None:
        _service = AchievementService()
    return _service