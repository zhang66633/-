"""学习路径生成器 — 基于真实数学建模学习资源构建.

参考来源:
- QInzhengk/Math-Model-and-Machine-Learning (623 stars)
- hacheyz/PMMAA (420 stars)
- RabbitWhite1/Mathematical-Modeling-In-Python (220 stars)
- Giyn/MathematicalModelingAlgorithm (107 stars)
- CQULeaf/MCM-ICM_Study_Resources (51 stars)

学习单元内容与定义见 unit_content.py（数据与逻辑分离，god-files 拆分 #31）。
"""

from ..learning.schemas import (
    AgentRole, LearningPath, LearningPhase, LearningUnit, UserLevel,
)

from .unit_content import ALL_MODELER, ALL_UNITS


def generate_learning_path(
    role: AgentRole = AgentRole.MODELER,
    level: UserLevel = UserLevel.BEGINNER,
    goal: str = "国赛",
) -> LearningPath:
    """生成学习路径 — 展示所有内容，用难度标签标注.

    不做筛选隐藏，全部单元按类别+难度分组展示。
    诊断水平用于推荐但不禁用内容。
    """
    all_units = ALL_UNITS.get(role.value, ALL_MODELER)

    # 按类别和难度分组 (不过滤, 全部展示)
    cats: dict[str, dict[str, list[LearningUnit]]] = {}
    for u in all_units:
        cat = u.method_category or "通用"
        diff = u.difficulty.value
        cats.setdefault(cat, {}).setdefault(diff, []).append(u)

    phases = []
    cat_labels = {"优化": "优化方法", "预测": "预测与拟合", "评价": "评价与决策",
                  "统计": "统计分析方法", "图论": "图论与网络", "微分方程": "微分方程建模",
                  "综合": "综合应用", "": "通用基础"}
    diff_labels = {"beginner": "入门", "intermediate": "进阶", "advanced": "实战", "competition": "竞赛"}

    # 入门在前，进阶次之，实战最后
    diff_order = ["beginner", "intermediate", "advanced", "competition"]

    for cat, diffs in cats.items():
        for diff in diff_order:
            if diff not in diffs:
                continue
            units = diffs[diff]
            # 路径列表只做导航,不携带全文: content_md 置空,按需走 /units/{id} 详情接口
            # (内容文件化后单篇 10KB+,38 篇全文会让路径响应膨胀到 ~500KB)
            nav_units = [u.model_copy(update={"content_md": ""}) for u in units]
            phases.append(LearningPhase(
                name=f"{cat_labels.get(cat, cat)} · {diff_labels.get(diff, diff)}",
                description=f"{cat_labels.get(cat, cat)}的{diff_labels.get(diff, diff)}级内容",
                duration_weeks=2 if len(units) <= 3 else 3,
                units=nav_units,
            ))

    return LearningPath(
        path_id=f"path_{role.value}",
        user_id="default", role=role, phases=phases,
    )


def get_unit_detail(unit_id: str) -> LearningUnit | None:
    for role_units in ALL_UNITS.values():
        for u in role_units:
            if u.unit_id == unit_id:
                return u
    return None
