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
    """获取各角色学习进度."""
    from ..learning.mastery_tracker import get_mastery_tracker
    tracker = get_mastery_tracker()
    return {
        "modeler": tracker.get_role_overall("default", []),
        "programmer": tracker.get_role_overall("default", []),
        "writer": tracker.get_role_overall("default", []),
        "weakest": [
            {"skill_id": s.skill_id, "name": s.name, "mastery": s.mastery}
            for s in tracker.get_weakest_skills("default", top_n=5)
        ],
    }
