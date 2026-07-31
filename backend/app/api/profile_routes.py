"""用户画像 API — 角色选择、水平诊断、进度查询."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..learning.schemas import (
    AgentRole, UserLevel, UserProfile, RoleProfile,
    SelfAssessment, LearningGoal,
)

profile_router = APIRouter(prefix="/profile", tags=["Profile"])


# ── 请求/响应模型 ─────────────────────────────────────

class DiagnoseRequest(BaseModel):
    role: str = "modeler"
    self_assessment: dict | None = None  # {math_level, programming_level, writing_level, modeling_experience}
    goal: str = "国赛"
    weekly_hours: int = 10


class ProfileResponse(BaseModel):
    profile: UserProfile


# ── 内存存储 (后续可替换为数据库) ─────────────────────

_profiles: dict[str, UserProfile] = {}


def _get_or_create(user_id: str) -> UserProfile:
    if user_id not in _profiles:
        _profiles[user_id] = UserProfile(user_id=user_id)
    return _profiles[user_id]


# ── 路由 ─────────────────────────────────────────────

@profile_router.post("/diagnose", response_model=ProfileResponse)
async def diagnose(req: DiagnoseRequest):
    """初始诊断: 选择角色 + 水平自评."""
    user_id = "default"  # TODO: 后续对接 auth
    profile = _get_or_create(user_id)

    try:
        role = AgentRole(req.role)
    except ValueError:
        role = AgentRole.MODELER

    # 设置主角色
    profile.roles = [RoleProfile(role=role, is_primary=True)]
    profile.goal = LearningGoal(
        competition=req.goal,
        weekly_hours=req.weekly_hours,
    )

    if req.self_assessment:
        profile.self_assessment = SelfAssessment(**req.self_assessment)

    return ProfileResponse(profile=profile)


@profile_router.get("", response_model=ProfileResponse)
async def get_profile():
    """获取当前用户画像."""
    profile = _get_or_create("default")
    return ProfileResponse(profile=profile)


@profile_router.put("/roles", response_model=ProfileResponse)
async def update_roles(roles: list[dict]):
    """更新角色配置."""
    profile = _get_or_create("default")
    profile.roles = [RoleProfile(**r) for r in roles]
    return ProfileResponse(profile=profile)


@profile_router.get("/progress", response_model=dict)
async def get_progress():
    """获取各角色学习进度 + 成就 + 待复习列表。"""
    from ..learning.mastery_tracker import get_mastery_tracker
    from ..services.achievement_service import get_achievement_service

    tracker = get_mastery_tracker()
    achievement_service = get_achievement_service()

    # 应用艾宾浩斯遗忘衰减
    needs_review = tracker.apply_decay("default")

    return {
        "modeler": tracker.get_role_overall("default", []),
        "programmer": tracker.get_role_overall("default", []),
        "writer": tracker.get_role_overall("default", []),
        "weakest": [
            {"skill_id": s.skill_id, "name": s.name, "mastery": round(s.mastery, 2)}
            for s in tracker.get_weakest_skills("default", top_n=5)
        ],
        "needs_review": [
            {"skill_id": sid, "retention": round(ret, 2)}
            for sid, ret in needs_review.items()
        ],
        "achievements": achievement_service.check_all("default"),
        "stats": {
            "total_units": 45,  # TODO: 从学习路径统计
            "completed_units": sum(
                1 for s in tracker.skills.get("default", {}).values()
                if s.mastery >= 0.6
            ),
            "streak_days": _calc_streak_from_tracker(tracker, "default"),
        },
    }


def _calc_streak_from_tracker(tracker, user_id: str) -> int:
    """从掌握度追踪器计算连续学习天数。"""
    if user_id not in tracker.skills:
        return 0
    dates = sorted(
        {s.last_practiced_at.date() for s in tracker.skills[user_id].values()
         if s.last_practiced_at},
        reverse=True,
    )
    if not dates:
        return 0
    streak = 1
    for i in range(1, len(dates)):
        if (dates[i - 1] - dates[i]).days == 1:
            streak += 1
        else:
            break
    return streak
