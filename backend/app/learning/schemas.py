"""学习子系统数据模型 — Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── 枚举 ────────────────────────────────────────────

class AgentRole(str, Enum):
    """三人团队角色"""
    MODELER = "modeler"         # 建模手
    PROGRAMMER = "programmer"   # 编程手
    WRITER = "writer"           # 论文手


class UserLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    COMPETITION = "competition"


class UnitType(str, Enum):
    KNOWLEDGE = "knowledge"     # 知识讲解
    PRACTICE = "practice"       # 练习
    PROJECT = "project"         # 综合项目


class UnitStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class ExerciseType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    CODE = "code"
    WRITING = "writing"
    MODELING = "modeling"


# ── 用户画像 ─────────────────────────────────────────

class RoleProfile(BaseModel):
    role: AgentRole
    level: UserLevel = UserLevel.BEGINNER
    is_primary: bool = False
    focus_areas: list[str] = Field(default_factory=list)


class SelfAssessment(BaseModel):
    math_level: int = Field(default=1, ge=1, le=5)
    programming_level: int = Field(default=1, ge=1, le=5)
    writing_level: int = Field(default=1, ge=1, le=5)
    modeling_experience: int = Field(default=1, ge=1, le=5)


class LearningGoal(BaseModel):
    competition: str = "国赛"          # 国赛 | 美赛 | 研赛 | 兴趣
    target_date: Optional[str] = None  # YYYY-MM
    weekly_hours: int = 10


class SkillMastery(BaseModel):
    """单个技能的贝叶斯掌握度"""
    skill_id: str
    name: str
    mastery: float = Field(default=0.2, ge=0.0, le=1.0)  # P(掌握)
    prior: float = 0.2
    correct_count: int = 0
    incorrect_count: int = 0
    last_practiced_at: Optional[datetime] = None


class RoleSkills(BaseModel):
    """某角色的技能掌握度汇总"""
    overall: float = Field(default=0.0, ge=0.0, le=1.0)
    skills: dict[str, float] = Field(default_factory=dict)  # skill_id → mastery


class UserProfile(BaseModel):
    user_id: str
    nickname: str = ""
    roles: list[RoleProfile] = Field(default_factory=list)
    goal: LearningGoal = Field(default_factory=LearningGoal)
    self_assessment: SelfAssessment = Field(default_factory=SelfAssessment)
    calibrated_skills: dict[str, RoleSkills] = Field(default_factory=dict)
    # key: "modeler" | "programmer" | "writer"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


# ── 学习路径 ─────────────────────────────────────────

class Prerequisite(BaseModel):
    unit_id: str
    required_mastery: float = 0.6


class LearningUnit(BaseModel):
    unit_id: str
    title: str
    role: AgentRole
    type: UnitType = UnitType.KNOWLEDGE
    difficulty: UserLevel = UserLevel.BEGINNER
    method_category: str = ""                # 优化/预测/评价/统计/图论/...
    tags: list[str] = Field(default_factory=list)
    prerequisites: list[Prerequisite] = Field(default_factory=list)
    kb_refs: dict[str, str] = Field(default_factory=dict)  # {method_card: mc_xxx, paper: paper_xxx}
    primary_agent: str = "modeler"           # 主讲智能体
    estimated_minutes: int = 30
    content_md: str = ""                     # Markdown 学习文档内容
    status: UnitStatus = UnitStatus.PENDING
    mastery_score: float = 0.0


class LearningPhase(BaseModel):
    name: str
    description: str = ""
    duration_weeks: int = 2
    units: list[LearningUnit] = Field(default_factory=list)


class LearningPath(BaseModel):
    path_id: str
    user_id: str
    role: AgentRole
    generated_at: datetime = Field(default_factory=datetime.now)
    phases: list[LearningPhase] = Field(default_factory=list)

    @property
    def total_units(self) -> int:
        return sum(len(p.units) for p in self.phases)

    @property
    def completed_units(self) -> int:
        return sum(1 for p in self.phases for u in p.units if u.status == UnitStatus.COMPLETED)

    @property
    def overall_mastery(self) -> float:
        units = [u for p in self.phases for u in p.units if u.mastery_score > 0]
        if not units:
            return 0.0
        return sum(u.mastery_score for u in units) / len(units)


# ── 练习记录 ─────────────────────────────────────────

class ExerciseFeedback(BaseModel):
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    external_resources: list[str] = Field(default_factory=list)  # B站/教材推荐


class ExerciseRecord(BaseModel):
    record_id: str
    user_id: str
    unit_id: str
    exercise_type: ExerciseType
    question: str
    user_answer: str
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    is_correct: bool = False
    time_spent_seconds: int = 0
    feedback: ExerciseFeedback = Field(default_factory=ExerciseFeedback)
    created_at: datetime = Field(default_factory=datetime.now)


# ── 学习事件 (用于知识图谱 + 遗忘追踪) ─────────────────

class LearningEvent(BaseModel):
    """学习行为事件，喂入 mastery_tracker"""
    event_id: str
    user_id: str
    unit_id: str
    skill_ids: list[str] = Field(default_factory=list)  # 关联的技能点
    event_type: str  # "learn" | "practice" | "review"
    score: Optional[float] = None  # 练习分数 (0-1)
    created_at: datetime = Field(default_factory=datetime.now)
