"""贝叶斯掌握度建模 + 艾宾浩斯遗忘追踪.

P(掌握) = 先验 + 练习证据 - 时间衰减

艾宾浩斯衰减因子:
  1天后: 0.7, 3天后: 0.5, 7天后: 0.3, 30天后: 0.1
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from .schemas import LearningEvent, SkillMastery


# ── 艾宾浩斯遗忘参数 ──────────────────────────────────

# 遗忘衰减率 (每天)
FORGET_DECAY_RATE = 0.05  # 每天衰减 5%

# 复习阈值: 保留率低于此值触发复习提醒
REVIEW_THRESHOLD = 0.6

# 遗忘警告阈值: 保留率低于此值标记为"需重新学习"
FORGET_WARNING_THRESHOLD = 0.3


def ebbinghaus_retention(days_since_last_practice: float) -> float:
    """艾宾浩斯遗忘曲线: 给定距上次练习的天数, 返回记忆保留率.

    简化模型 (基于 Ebbinghaus 实验数据的指数拟合):
    R(t) ≈ e^(-t/d) 其中 d ≈ 20 (特征衰减天数)
    """
    if days_since_last_practice <= 0:
        return 1.0
    return math.exp(-days_since_last_practice / 20.0)


# ── 贝叶斯掌握度 ──────────────────────────────────────

class MasteryTracker:
    """贝叶斯知识追踪 (BKT 简化版) + 艾宾浩斯遗忘."""

    def __init__(self):
        self.skills: dict[str, dict[str, SkillMastery]] = {}
        # key: user_id → {skill_id → SkillMastery}

    def get_or_create_skill(self, user_id: str, skill_id: str,
                            name: str = "", prior: float = 0.2) -> SkillMastery:
        """获取或创建用户某个技能的掌握度记录."""
        if user_id not in self.skills:
            self.skills[user_id] = {}

        if skill_id not in self.skills[user_id]:
            self.skills[user_id][skill_id] = SkillMastery(
                skill_id=skill_id,
                name=name,
                mastery=prior,
                peak_mastery=prior,
                prior=prior,
            )

        return self.skills[user_id][skill_id]

    def update_from_event(self, user_id: str, event: LearningEvent) -> None:
        """根据学习事件更新峰值掌握度与展示掌握度.

        mastery 已改为派生展示值（峰值 × 保留率），事件只抬升峰值掌握度，
        避免衰减后的展示值被再次当作真实掌握度参与加减，造成掌握度漂移。
        """
        for skill_id in event.skill_ids:
            skill = self.get_or_create_skill(user_id, skill_id)

            # 峰值兜底：存量无 peak_mastery 的技能以当前 mastery 初始化
            peak = getattr(skill, "peak_mastery", None)
            if peak is None:
                peak = skill.mastery
            skill.peak_mastery = max(peak, skill.mastery)

            if event.event_type == "practice" and event.score is not None:
                if event.score >= 0.6:  # 正确
                    skill.peak_mastery = min(1.0, skill.peak_mastery + 0.15)
                    skill.correct_count += 1
                else:  # 错误
                    skill.peak_mastery = max(0.05, skill.peak_mastery - 0.10)
                    skill.incorrect_count += 1
                skill.last_practiced_at = event.created_at

            elif event.event_type == "learn":
                # 学习事件: 先验提升但不等于掌握
                skill.peak_mastery = min(1.0, skill.peak_mastery + 0.05)

            elif event.event_type == "review":
                # 复习事件: 重置衰减
                skill.last_practiced_at = event.created_at

            # 展示掌握度 = 峰值 × 当前保留率（刚练习/复习完保留率≈1）
            days = 0.0
            if skill.last_practiced_at is not None:
                days = max(
                    0.0,
                    (event.created_at - skill.last_practiced_at).total_seconds() / 86400.0,
                )
            skill.mastery = skill.peak_mastery * ebbinghaus_retention(days)

            self.skills[user_id][skill_id] = skill

    def apply_decay(self, user_id: str, now: Optional[datetime] = None) -> dict[str, float]:
        """幂等地计算所有技能的衰减后掌握度, 返回低于阈值的技能列表.

        掌握度改为派生展示值：峰值掌握度 × 艾宾浩斯保留率，
        不再对 mastery 原地相乘，重复调用不会造成指数崩塌。
        """
        if now is None:
            now = datetime.now()

        needs_review: dict[str, float] = {}

        if user_id not in self.skills:
            return needs_review

        for skill_id, skill in self.skills[user_id].items():
            if skill.last_practiced_at is None:
                continue

            days = (now - skill.last_practiced_at).total_seconds() / 86400.0
            retention = ebbinghaus_retention(days)

            # 峰值兜底：存量无 peak_mastery 的技能以当前 mastery 初始化
            peak = getattr(skill, "peak_mastery", None)
            if peak is None:
                peak = skill.mastery
                skill.peak_mastery = peak
            else:
                peak = max(peak, skill.mastery)
                skill.peak_mastery = peak

            # 展示值 = 峰值 × 保留率（幂等：始终由峰值推导，不依赖旧的 mastery）
            skill.mastery = peak * retention

            # 如果保留率低于阈值, 加入复习提醒
            if retention < REVIEW_THRESHOLD:
                needs_review[skill_id] = retention

        return needs_review

    def get_role_overall(self, user_id: str,
                          skill_ids: list[str]) -> float:
        """计算某角色(某组技能)的综合掌握度."""
        if user_id not in self.skills or not skill_ids:
            return 0.0

        values = []
        for sid in skill_ids:
            if sid in self.skills[user_id]:
                values.append(self.skills[user_id][sid].mastery)

        if not values:
            return 0.0
        return sum(values) / len(values)

    def get_weakest_skills(self, user_id: str, top_n: int = 5) -> list[SkillMastery]:
        """返回掌握度最低的 top_n 个技能."""
        if user_id not in self.skills:
            return []
        sorted_skills = sorted(
            self.skills[user_id].values(),
            key=lambda s: s.mastery,
        )
        return sorted_skills[:top_n]

    def get_next_review_date(self, skill_id: str, user_id: str) -> Optional[datetime]:
        """根据当前掌握度计算下次应复习的日期."""
        if user_id not in self.skills:
            return None
        skill = self.skills[user_id].get(skill_id)
        if not skill:
            return None

        # 当保留率将降至 REVIEW_THRESHOLD 时需复习
        # R(t) = e^(-t/20) > 0.6 → t < -20*ln(0.6) ≈ 10.2 天
        review_days = -20.0 * math.log(REVIEW_THRESHOLD)
        last = skill.last_practiced_at or datetime.now()
        return last + timedelta(days=review_days)


# ── 全局单例 ──────────────────────────────────────────

_tracker: Optional[MasteryTracker] = None


def get_mastery_tracker() -> MasteryTracker:
    global _tracker
    if _tracker is None:
        _tracker = MasteryTracker()
    return _tracker
