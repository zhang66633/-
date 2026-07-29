"""学习路径生成器 — 基于知识图谱 + 用户角色 + 水平生成学习路径."""

from ..learning.schemas import (
    AgentRole, LearningPath, LearningUnit, LearningPhase,
    UnitStatus, UnitType, UserLevel,
)


# ── 预定义学习单元模板 ─────────────────────────────────

# 建模手 - 优化类 入门单元
_MODELER_OPTIMIZATION_BEGINNER = [
    LearningUnit(
        unit_id="modeler_lp_01",
        title="线性规划基础",
        role=AgentRole.MODELER,
        type=UnitType.KNOWLEDGE,
        difficulty=UserLevel.BEGINNER,
        method_category="优化",
        tags=["线性规划", "LP", "单纯形法"],
        primary_agent="modeler",
        estimated_minutes=45,
    ),
    LearningUnit(
        unit_id="modeler_lp_02",
        title="线性规划建模实践",
        role=AgentRole.MODELER,
        type=UnitType.PRACTICE,
        difficulty=UserLevel.BEGINNER,
        method_category="优化",
        tags=["线性规划", "LP", "建模"],
        prerequisites=[{"unit_id": "modeler_lp_01", "required_mastery": 0.6}],
        primary_agent="verifier",
        estimated_minutes=30,
    ),
    LearningUnit(
        unit_id="modeler_ip_01",
        title="整数规划与0-1规划",
        role=AgentRole.MODELER,
        type=UnitType.KNOWLEDGE,
        difficulty=UserLevel.BEGINNER,
        method_category="优化",
        tags=["整数规划", "IP", "0-1规划", "分支定界"],
        prerequisites=[{"unit_id": "modeler_lp_01", "required_mastery": 0.6}],
        primary_agent="modeler",
        estimated_minutes=45,
    ),
    LearningUnit(
        unit_id="modeler_ip_02",
        title="指派问题与运输问题",
        role=AgentRole.MODELER,
        type=UnitType.PRACTICE,
        difficulty=UserLevel.BEGINNER,
        method_category="优化",
        tags=["指派问题", "运输问题", "匈牙利算法"],
        prerequisites=[{"unit_id": "modeler_ip_01", "required_mastery": 0.6}],
        primary_agent="verifier",
        estimated_minutes=30,
    ),
    LearningUnit(
        unit_id="modeler_dp_01",
        title="动态规划入门",
        role=AgentRole.MODELER,
        type=UnitType.KNOWLEDGE,
        difficulty=UserLevel.INTERMEDIATE,
        method_category="优化",
        tags=["动态规划", "DP", "最优子结构", "Bellman方程"],
        prerequisites=[{"unit_id": "modeler_lp_01", "required_mastery": 0.7}],
        primary_agent="modeler",
        estimated_minutes=60,
    ),
]

# 建模手 - 评价类 入门单元
_MODELER_EVALUATION_BEGINNER = [
    LearningUnit(
        unit_id="modeler_ahp_01",
        title="层次分析法(AHP)原理",
        role=AgentRole.MODELER,
        type=UnitType.KNOWLEDGE,
        difficulty=UserLevel.BEGINNER,
        method_category="评价",
        tags=["AHP", "层次分析法", "成对比较矩阵", "一致性检验"],
        primary_agent="modeler",
        estimated_minutes=45,
    ),
    LearningUnit(
        unit_id="modeler_ahp_02",
        title="AHP建模实践",
        role=AgentRole.MODELER,
        type=UnitType.PRACTICE,
        difficulty=UserLevel.BEGINNER,
        method_category="评价",
        tags=["AHP", "层次分析法", "建模"],
        prerequisites=[{"unit_id": "modeler_ahp_01", "required_mastery": 0.6}],
        primary_agent="verifier",
        estimated_minutes=30,
    ),
    LearningUnit(
        unit_id="modeler_topsis_01",
        title="TOPSIS理想解逼近法",
        role=AgentRole.MODELER,
        type=UnitType.KNOWLEDGE,
        difficulty=UserLevel.BEGINNER,
        method_category="评价",
        tags=["TOPSIS", "理想解", "负理想解", "贴近度"],
        prerequisites=[{"unit_id": "modeler_ahp_01", "required_mastery": 0.5}],
        primary_agent="modeler",
        estimated_minutes=45,
    ),
]

# 建模手 - 预测类 入门单元
_MODELER_PREDICTION_BEGINNER = [
    LearningUnit(
        unit_id="modeler_reg_01",
        title="回归分析基础",
        role=AgentRole.MODELER,
        type=UnitType.KNOWLEDGE,
        difficulty=UserLevel.BEGINNER,
        method_category="预测",
        tags=["回归分析", "线性回归", "最小二乘法", "拟合优度"],
        primary_agent="modeler",
        estimated_minutes=45,
    ),
    LearningUnit(
        unit_id="modeler_reg_02",
        title="回归分析建模实践",
        role=AgentRole.MODELER,
        type=UnitType.PRACTICE,
        difficulty=UserLevel.BEGINNER,
        method_category="预测",
        tags=["回归分析", "建模", "残差分析"],
        prerequisites=[{"unit_id": "modeler_reg_01", "required_mastery": 0.6}],
        primary_agent="solver",
        estimated_minutes=30,
    ),
]

# 编程手 - Python 基础
_PROGRAMMER_BEGINNER = [
    LearningUnit(
        unit_id="prog_py_01",
        title="Python科学计算入门",
        role=AgentRole.PROGRAMMER,
        type=UnitType.KNOWLEDGE,
        difficulty=UserLevel.BEGINNER,
        method_category="",
        tags=["Python", "NumPy", "SciPy", "科学计算"],
        primary_agent="solver",
        estimated_minutes=45,
    ),
    LearningUnit(
        unit_id="prog_py_02",
        title="NumPy数组操作实战",
        role=AgentRole.PROGRAMMER,
        type=UnitType.PRACTICE,
        difficulty=UserLevel.BEGINNER,
        method_category="",
        tags=["NumPy", "数组", "矩阵运算"],
        prerequisites=[{"unit_id": "prog_py_01", "required_mastery": 0.6}],
        primary_agent="solver",
        estimated_minutes=30,
    ),
    LearningUnit(
        unit_id="prog_py_03",
        title="Pandas数据处理",
        role=AgentRole.PROGRAMMER,
        type=UnitType.KNOWLEDGE,
        difficulty=UserLevel.BEGINNER,
        method_category="",
        tags=["Pandas", "数据处理", "DataFrame"],
        prerequisites=[{"unit_id": "prog_py_01", "required_mastery": 0.5}],
        primary_agent="solver",
        estimated_minutes=45,
    ),
    LearningUnit(
        unit_id="prog_py_04",
        title="Matplotlib数据可视化",
        role=AgentRole.PROGRAMMER,
        type=UnitType.KNOWLEDGE,
        difficulty=UserLevel.BEGINNER,
        method_category="",
        tags=["Matplotlib", "可视化", "图表"],
        prerequisites=[{"unit_id": "prog_py_01", "required_mastery": 0.5}],
        primary_agent="solver",
        estimated_minutes=40,
    ),
]

# 论文手 - 写作基础
_WRITER_BEGINNER = [
    LearningUnit(
        unit_id="writer_abs_01",
        title="摘要撰写技巧",
        role=AgentRole.WRITER,
        type=UnitType.KNOWLEDGE,
        difficulty=UserLevel.BEGINNER,
        method_category="",
        tags=["摘要", "学术写作", "国赛格式"],
        primary_agent="editor",
        estimated_minutes=45,
    ),
    LearningUnit(
        unit_id="writer_abs_02",
        title="摘要写作练习",
        role=AgentRole.WRITER,
        type=UnitType.PRACTICE,
        difficulty=UserLevel.BEGINNER,
        method_category="",
        tags=["摘要", "写作", "练习"],
        prerequisites=[{"unit_id": "writer_abs_01", "required_mastery": 0.6}],
        primary_agent="editor",
        estimated_minutes=30,
    ),
    LearningUnit(
        unit_id="writer_struct_01",
        title="论文结构组织",
        role=AgentRole.WRITER,
        type=UnitType.KNOWLEDGE,
        difficulty=UserLevel.BEGINNER,
        method_category="",
        tags=["论文结构", "学术写作", "章节"],
        primary_agent="editor",
        estimated_minutes=45,
    ),
    LearningUnit(
        unit_id="writer_viz_01",
        title="图表设计与数据可视化",
        role=AgentRole.WRITER,
        type=UnitType.KNOWLEDGE,
        difficulty=UserLevel.BEGINNER,
        method_category="",
        tags=["可视化", "图表", "三线表", "数据呈现"],
        primary_agent="editor",
        estimated_minutes=40,
    ),
]


# ── 路径生成 ──────────────────────────────────────────

def generate_learning_path(
    role: AgentRole = AgentRole.MODELER,
    level: UserLevel = UserLevel.BEGINNER,
    goal: str = "国赛",
) -> LearningPath:
    """根据角色、水平、目标生成学习路径."""
    path_id = f"path_{role.value}_{level.value}"

    if role == AgentRole.MODELER:
        phases = [
            LearningPhase(
                name="阶段1: 优化方法入门",
                description="掌握最常用的优化建模方法，打好建模基础",
                duration_weeks=2,
                units=_MODELER_OPTIMIZATION_BEGINNER,
            ),
            LearningPhase(
                name="阶段2: 评价与决策方法",
                description="学会多准则评价和决策分析",
                duration_weeks=2,
                units=_MODELER_EVALUATION_BEGINNER,
            ),
            LearningPhase(
                name="阶段3: 预测与拟合方法",
                description="掌握数据驱动的预测建模方法",
                duration_weeks=2,
                units=_MODELER_PREDICTION_BEGINNER,
            ),
        ]
    elif role == AgentRole.PROGRAMMER:
        phases = [
            LearningPhase(
                name="阶段1: Python科学计算基础",
                description="掌握Python数据科学生态的核心工具",
                duration_weeks=2,
                units=_PROGRAMMER_BEGINNER,
            ),
        ]
    elif role == AgentRole.WRITER:
        phases = [
            LearningPhase(
                name="阶段1: 学术写作基础",
                description="掌握数学建模论文的写作规范和技巧",
                duration_weeks=2,
                units=_WRITER_BEGINNER,
            ),
        ]
    else:
        phases = []

    return LearningPath(
        path_id=path_id,
        user_id="default",
        role=role,
        phases=phases,
    )


def get_unit_detail(unit_id: str) -> LearningUnit | None:
    """根据 unit_id 获取学习单元详情."""
    all_units = (
        _MODELER_OPTIMIZATION_BEGINNER
        + _MODELER_EVALUATION_BEGINNER
        + _MODELER_PREDICTION_BEGINNER
        + _PROGRAMMER_BEGINNER
        + _WRITER_BEGINNER
    )
    for unit in all_units:
        if unit.unit_id == unit_id:
            return unit
    return None
