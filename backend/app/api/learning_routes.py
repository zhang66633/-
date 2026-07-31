"""学习 API — 学习路径、学习单元、推荐."""

from datetime import datetime
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..learning.schemas import (
    AgentRole, LearningPath, LearningUnit, LearningPhase,
    UnitStatus, UnitType, UserLevel, LearningEvent,
)
from ..learning.path_generator import generate_learning_path, get_unit_detail
from ..learning.mastery_tracker import get_mastery_tracker
from ..services.achievement_service import get_achievement_service

learning_router = APIRouter(prefix="/learning", tags=["Learning"])


# ── 学习路径 ──────────────────────────────────────────

class GeneratePathRequest(BaseModel):
    role: str = "modeler"   # modeler | programmer | writer
    level: str = "beginner" # beginner | intermediate | advanced
    goal: str = "国赛"       # 国赛 | 美赛 | 兴趣


class PathResponse(BaseModel):
    path: LearningPath


@learning_router.post("/path/generate", response_model=PathResponse)
async def generate_path(req: GeneratePathRequest):
    """为指定角色和水平生成学习路径."""
    role = AgentRole(req.role)
    level = UserLevel(req.level)
    path = generate_learning_path(role=role, level=level, goal=req.goal)
    return PathResponse(path=path)


@learning_router.get("/path/{role}", response_model=PathResponse)
async def get_path(role: str):
    """获取某个角色的默认学习路径."""
    try:
        r = AgentRole(role)
    except ValueError:
        r = AgentRole.MODELER
    path = generate_learning_path(role=r, level=UserLevel.BEGINNER)
    return PathResponse(path=path)


# ── 学习单元 ──────────────────────────────────────────

class UnitResponse(BaseModel):
    unit: LearningUnit


@learning_router.get("/units/{unit_id}", response_model=UnitResponse)
async def get_unit(unit_id: str):
    """获取单个学习单元的详情."""
    unit = get_unit_detail(unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail=f"学习单元 {unit_id} 不存在")
    return UnitResponse(unit=unit)


class UnitCompleteRequest(BaseModel):
    user_id: str = "default"


@learning_router.post("/units/{unit_id}/complete")
async def complete_unit(unit_id: str, req: UnitCompleteRequest):
    """标记学习单元为完成，并更新贝叶斯掌握度。"""
    unit = get_unit_detail(unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail=f"学习单元 {unit_id} 不存在")

    # 更新掌握度追踪
    tracker = get_mastery_tracker()
    skill_ids = unit.tags or [unit_id]
    event = LearningEvent(
        event_id=f"evt_{uuid.uuid4().hex[:8]}",
        user_id=req.user_id,
        unit_id=unit_id,
        skill_ids=skill_ids,
        event_type="learn",
        score=1.0,  # 标记完成视为满分
        created_at=datetime.utcnow(),
    )
    tracker.update_from_event(req.user_id, event)

    # 记录到成就系统
    achievement_service = get_achievement_service()
    achievement_service.add_event(event)

    # 更新单元状态
    unit.status = UnitStatus.COMPLETED
    unit.mastery_score = tracker.get_role_overall(
        req.user_id,
        skill_ids,
    )

    return {
        "status": "ok",
        "message": f"单元 {unit_id} 已标记完成",
        "mastery": unit.mastery_score,
    }


# ── 下一步推荐 ────────────────────────────────────────

class NextRecommendResponse(BaseModel):
    recommended_unit: LearningUnit | None
    review_units: list[LearningUnit]
    message: str


@learning_router.get("/next/{role}", response_model=NextRecommendResponse)
async def get_next_recommendation(role: str = "modeler"):
    """获取下一个推荐学习单元."""
    path = generate_learning_path(role=AgentRole(role), level=UserLevel.BEGINNER)
    next_unit = None
    review_units = []
    for phase in path.phases:
        for unit in phase.units:
            if unit.status == UnitStatus.PENDING and not next_unit:
                next_unit = unit
    return NextRecommendResponse(
        recommended_unit=next_unit,
        review_units=review_units,
        message=f"推荐继续学习: {next_unit.title}" if next_unit else "全部完成！",
    )


