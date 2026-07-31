"""学习路径生成器 — 基于真实数学建模学习资源构建.

参考来源:
- QInzhengk/Math-Model-and-Machine-Learning (623 stars)
- hacheyz/PMMAA (420 stars)
- RabbitWhite1/Mathematical-Modeling-In-Python (220 stars)
- Giyn/MathematicalModelingAlgorithm (107 stars)
- CQULeaf/MCM-ICM_Study_Resources (51 stars)
"""

from ..learning.schemas import (
    AgentRole, LearningPath, LearningUnit, LearningPhase,
    UnitStatus, UnitType, UserLevel,
)


def _u(unit_id, title, role, cat, diff, tags, agent, minutes=30,
       prereqs=None, unit_type=UnitType.KNOWLEDGE):
    return LearningUnit(
        unit_id=unit_id, title=title, role=role, type=unit_type,
        difficulty=diff, method_category=cat, tags=tags,
        primary_agent=agent, estimated_minutes=minutes,
        prerequisites=prereqs or [],
    )


# ══════════════════════════════════════════════════════════
# 建模手 — 优化类
# ══════════════════════════════════════════════════════════

_MODELER_OPTIMIZATION = [
    # 入门
    _u("modeler_lp_01", "线性规划与单纯形法", "modeler", "优化", UserLevel.BEGINNER,
       ["线性规划", "LP", "单纯形法", "对偶理论"], "modeler", 45),
    _u("modeler_lp_02", "线性规划建模实战", "modeler", "优化", UserLevel.BEGINNER,
       ["线性规划", "建模", "灵敏度分析"], "verifier", 30,
       [{"unit_id": "modeler_lp_01", "required_mastery": 0.6}], UnitType.PRACTICE),
    _u("modeler_ip_01", "整数规划与分支定界", "modeler", "优化", UserLevel.BEGINNER,
       ["整数规划", "IP", "分支定界", "割平面"], "modeler", 45,
       [{"unit_id": "modeler_lp_01", "required_mastery": 0.6}]),
    _u("modeler_ip_02", "0-1规划与指派问题", "modeler", "优化", UserLevel.BEGINNER,
       ["0-1规划", "指派问题", "匈牙利算法"], "modeler", 30,
       [{"unit_id": "modeler_ip_01", "required_mastery": 0.5}]),

    # 进阶
    _u("modeler_dp_01", "动态规划与最优子结构", "modeler", "优化", UserLevel.INTERMEDIATE,
       ["动态规划", "DP", "最优子结构", "Bellman方程"], "modeler", 60,
       [{"unit_id": "modeler_lp_01", "required_mastery": 0.7}]),
    _u("modeler_ga_01", "遗传算法原理与应用", "modeler", "优化", UserLevel.INTERMEDIATE,
       ["遗传算法", "GA", "选择", "交叉", "变异"], "modeler", 50),
    _u("modeler_sa_01", "模拟退火算法", "modeler", "优化", UserLevel.INTERMEDIATE,
       ["模拟退火", "SA", "Metropolis准则", "降温策略"], "modeler", 45),
    _u("modeler_pso_01", "粒子群优化算法", "modeler", "优化", UserLevel.INTERMEDIATE,
       ["粒子群", "PSO", "群体智能", "全局优化"], "modeler", 45),
    _u("modeler_multiobj", "多目标优化与NSGA-II", "modeler", "优化", UserLevel.INTERMEDIATE,
       ["多目标优化", "NSGA-II", "Pareto前沿", "非支配排序"], "modeler", 60,
       [{"unit_id": "modeler_ga_01", "required_mastery": 0.5}]),
    _u("modeler_heuristic_practice", "启发式算法综合实战", "modeler", "优化", UserLevel.INTERMEDIATE,
       ["启发式", "GA", "SA", "PSO", "对比"], "solver", 45,
       [{"unit_id": "modeler_ga_01", "required_mastery": 0.5},
        {"unit_id": "modeler_sa_01", "required_mastery": 0.5}], UnitType.PRACTICE),

    # 实战
    _u("modeler_ant_colony", "蚁群算法与组合优化", "modeler", "优化", UserLevel.ADVANCED,
       ["蚁群算法", "ACO", "TSP", "组合优化"], "modeler", 50),
    _u("modeler_convex_opt", "凸优化与KKT条件", "modeler", "优化", UserLevel.ADVANCED,
       ["凸优化", "KKT条件", "对偶理论", "Lagrange乘子"], "modeler", 60),
]

# ══════════════════════════════════════════════════════════
# 建模手 — 预测类
# ══════════════════════════════════════════════════════════

_MODELER_PREDICTION = [
    _u("modeler_reg_01", "线性回归与最小二乘法", "modeler", "预测", UserLevel.BEGINNER,
       ["回归分析", "最小二乘法", "拟合优度", "残差分析"], "modeler", 45),
    _u("modeler_reg_02", "多元回归与变量选择", "modeler", "预测", UserLevel.BEGINNER,
       ["多元回归", "逐步回归", "多重共线性", "正则化"], "modeler", 45,
       [{"unit_id": "modeler_reg_01", "required_mastery": 0.6}]),
    _u("modeler_arima_01", "时间序列与ARIMA模型", "modeler", "预测", UserLevel.INTERMEDIATE,
       ["时间序列", "ARIMA", "平稳性", "ACF", "PACF"], "modeler", 60),
    _u("modeler_grey_01", "灰色预测GM(1,1)", "modeler", "预测", UserLevel.BEGINNER,
       ["灰色预测", "GM(1,1)", "小样本预测", "累加生成"], "modeler", 40),
    _u("modeler_nn_01", "神经网络预测入门", "modeler", "预测", UserLevel.INTERMEDIATE,
       ["神经网络", "BP算法", "激活函数", "过拟合"], "modeler", 60,
       [{"unit_id": "modeler_reg_01", "required_mastery": 0.5}]),
    _u("modeler_rf_01", "随机森林与集成学习", "modeler", "预测", UserLevel.ADVANCED,
       ["随机森林", "集成学习", "Bagging", "特征重要性"], "modeler", 50),
]

# ══════════════════════════════════════════════════════════
# 建模手 — 评价类
# ══════════════════════════════════════════════════════════

_MODELER_EVALUATION = [
    _u("modeler_ahp_01", "层次分析法(AHP)", "modeler", "评价", UserLevel.BEGINNER,
       ["AHP", "层次分析", "成对比较矩阵", "一致性检验"], "modeler", 45),
    _u("modeler_ahp_02", "模糊AHP与改进方法", "modeler", "评价", UserLevel.INTERMEDIATE,
       ["模糊AHP", "三角模糊数", "群体决策"], "modeler", 45,
       [{"unit_id": "modeler_ahp_01", "required_mastery": 0.6}]),
    _u("modeler_topsis_01", "TOPSIS理想解逼近法", "modeler", "评价", UserLevel.BEGINNER,
       ["TOPSIS", "理想解", "负理想解", "贴近度", "熵权TOPSIS"], "modeler", 45,
       [{"unit_id": "modeler_ahp_01", "required_mastery": 0.4}]),
    _u("modeler_entropy", "熵权法与客观赋权", "modeler", "评价", UserLevel.BEGINNER,
       ["熵权法", "信息熵", "客观权重", "组合赋权"], "modeler", 40),
    _u("modeler_fuzzy_eval", "模糊综合评价", "modeler", "评价", UserLevel.INTERMEDIATE,
       ["模糊数学", "隶属函数", "模糊综合评价"], "modeler", 50),
    _u("modeler_dea_01", "数据包络分析(DEA)", "modeler", "评价", UserLevel.ADVANCED,
       ["DEA", "CCR模型", "BCC模型", "效率评价"], "modeler", 50),
    _u("modeler_grey_rel", "灰色关联分析", "modeler", "评价", UserLevel.INTERMEDIATE,
       ["灰色关联", "邓氏关联度", "综合评价"], "modeler", 40),
]

# ══════════════════════════════════════════════════════════
# 建模手 — 统计与图论
# ══════════════════════════════════════════════════════════

_MODELER_STATS_GRAPH = [
    _u("modeler_mle_01", "极大似然估计", "modeler", "统计", UserLevel.INTERMEDIATE,
       ["MLE", "似然函数", "参数估计", "EM算法"], "modeler", 50),
    _u("modeler_bayes_01", "贝叶斯推断", "modeler", "统计", UserLevel.INTERMEDIATE,
       ["贝叶斯", "先验", "后验", "MCMC"], "modeler", 50),
    _u("modeler_mc_01", "蒙特卡洛模拟", "modeler", "统计", UserLevel.BEGINNER,
       ["蒙特卡洛", "随机模拟", "大数定律", "方差缩减"], "modeler", 45),
    _u("modeler_shortest", "最短路径与Dijkstra", "modeler", "图论", UserLevel.BEGINNER,
       ["最短路径", "Dijkstra", "Floyd", "图论建模"], "modeler", 45),
    _u("modeler_network", "网络流与最大流", "modeler", "图论", UserLevel.INTERMEDIATE,
       ["网络流", "最大流", "Ford-Fulkerson", "最小割"], "modeler", 50),
    _u("modeler_mst", "最小生成树与TSP", "modeler", "图论", UserLevel.INTERMEDIATE,
       ["MST", "Prim", "Kruskal", "TSP"], "modeler", 45),
    _u("modeler_pca_01", "主成分分析(PCA)", "modeler", "统计", UserLevel.INTERMEDIATE,
       ["PCA", "特征值", "降维", "方差解释率"], "modeler", 50),
]

# ══════════════════════════════════════════════════════════
# 建模手 — 微分方程与综合
# ══════════════════════════════════════════════════════════

_MODELER_DE_COMPREHENSIVE = [
    _u("modeler_ode_01", "常微分方程建模", "modeler", "微分方程", UserLevel.INTERMEDIATE,
       ["ODE", "微分方程建模", "相图", "稳定性"], "modeler", 50),
    _u("modeler_pde_01", "偏微分方程与有限差分", "modeler", "微分方程", UserLevel.ADVANCED,
       ["PDE", "有限差分法", "热传导", "扩散方程"], "modeler", 60),
    _u("modeler_queue_01", "排队论建模", "modeler", "综合", UserLevel.INTERMEDIATE,
       ["排队论", "M/M/1", "Little公式", "服务系统"], "modeler", 45),
    _u("modeler_game_01", "博弈论基础", "modeler", "综合", UserLevel.INTERMEDIATE,
       ["博弈论", "Nash均衡", "囚徒困境", "演化博弈"], "modeler", 50),
    _u("modeler_ca_01", "元胞自动机建模", "modeler", "综合", UserLevel.ADVANCED,
       ["元胞自动机", "交通流", "疏散模拟", "涌现"], "modeler", 50),
    _u("modeler_model_combo", "组合模型设计", "modeler", "综合", UserLevel.ADVANCED,
       ["组合模型", "模型融合", "Stacking", "集成"], "modeler", 60),
]

# ══════════════════════════════════════════════════════════
# 编程手
# ══════════════════════════════════════════════════════════

_PROGRAMMER = [
    # 入门
    _u("prog_py_01", "Python科学计算入门", "programmer", "", UserLevel.BEGINNER,
       ["Python", "NumPy", "SciPy", "科学计算"], "solver", 45),
    _u("prog_py_02", "NumPy数组操作实战", "programmer", "", UserLevel.BEGINNER,
       ["NumPy", "数组", "矩阵运算", "广播"], "solver", 30,
       [{"unit_id": "prog_py_01", "required_mastery": 0.6}], UnitType.PRACTICE),
    _u("prog_pandas_01", "Pandas数据处理", "programmer", "", UserLevel.BEGINNER,
       ["Pandas", "DataFrame", "数据清洗", "GroupBy"], "solver", 45,
       [{"unit_id": "prog_py_01", "required_mastery": 0.5}]),
    _u("prog_viz_01", "Matplotlib数据可视化", "programmer", "", UserLevel.BEGINNER,
       ["Matplotlib", "可视化", "折线图", "散点图", "热力图"], "solver", 40),

    # 进阶
    _u("prog_optimize_01", "scipy.optimize求解优化问题", "programmer", "", UserLevel.INTERMEDIATE,
       ["scipy.optimize", "linprog", "minimize", "非线性规划"], "solver", 50,
       [{"unit_id": "prog_py_01", "required_mastery": 0.7}]),
    _u("prog_cvxpy_01", "cvxpy凸优化编程", "programmer", "", UserLevel.INTERMEDIATE,
       ["cvxpy", "凸优化", "锥规划", "建模语言"], "solver", 50),
    _u("prog_sklearn_01", "sklearn机器学习实战", "programmer", "", UserLevel.INTERMEDIATE,
       ["sklearn", "分类", "回归", "聚类", "模型选择"], "solver", 60,
       [{"unit_id": "prog_py_01", "required_mastery": 0.7}]),
    _u("prog_networkx_01", "networkx图论编程", "programmer", "", UserLevel.INTERMEDIATE,
       ["networkx", "图论", "最短路径", "网络流", "可视化"], "solver", 45),
    _u("prog_ga_impl", "遗传算法自实现", "programmer", "", UserLevel.INTERMEDIATE,
       ["遗传算法", "Python实现", "适应度函数", "编码设计"], "solver", 60),
    _u("prog_seaborn_01", "Seaborn高级可视化", "programmer", "", UserLevel.INTERMEDIATE,
       ["Seaborn", "统计图", "热力图", "pairplot"], "solver", 35),

    # 实战
    _u("prog_sympy_01", "SymPy符号计算", "programmer", "", UserLevel.ADVANCED,
       ["SymPy", "符号计算", "求导", "积分", "方程求解"], "solver", 45),
    _u("prog_perf_01", "代码性能优化", "programmer", "", UserLevel.ADVANCED,
       ["性能优化", "向量化", "JIT", "Cython"], "solver", 50),
    _u("prog_pipeline_01", "建模数据处理流水线", "programmer", "", UserLevel.ADVANCED,
       ["数据流水线", "预处理", "特征工程", "自动化"], "solver", 50),
]

# ══════════════════════════════════════════════════════════
# 论文手
# ══════════════════════════════════════════════════════════

_WRITER = [
    # 入门
    _u("writer_abs_01", "摘要撰写技巧", "writer", "", UserLevel.BEGINNER,
       ["摘要", "学术写作", "400字", "关键词"], "editor", 45),
    _u("writer_abs_02", "摘要写作练习", "writer", "", UserLevel.BEGINNER,
       ["摘要", "练习", "对比范文"], "editor", 30,
       [{"unit_id": "writer_abs_01", "required_mastery": 0.6}], UnitType.PRACTICE),
    _u("writer_struct_01", "论文结构与逻辑组织", "writer", "", UserLevel.BEGINNER,
       ["论文结构", "叙事逻辑", "章节安排", "国赛格式"], "editor", 45),
    _u("writer_viz_01", "图表设计与可视化", "writer", "", UserLevel.BEGINNER,
       ["可视化", "图表", "三线表", "流程图", "数据呈现"], "editor", 40),

    # 进阶
    _u("writer_hypothesis", "模型假设与符号说明", "writer", "", UserLevel.INTERMEDIATE,
       ["模型假设", "符号说明", "合理性论证"], "editor", 40),
    _u("writer_result", "结果分析与讨论写法", "writer", "", UserLevel.INTERMEDIATE,
       ["结果分析", "灵敏度", "数值实验", "讨论"], "editor", 45),
    _u("writer_eval", "模型评价与改进写作", "writer", "", UserLevel.INTERMEDIATE,
       ["模型评价", "优缺点", "改进方向", "推广"], "editor", 35),
    _u("writer_latex_01", "LaTeX数学建模模板", "writer", "", UserLevel.INTERMEDIATE,
       ["LaTeX", "模板", "公式排版", "表格", "参考文献"], "editor", 50),

    # 实战
    _u("writer_reference", "文献检索与引用规范", "writer", "", UserLevel.ADVANCED,
       ["文献检索", "引用规范", "BibTeX", "知网/Google Scholar"], "editor", 40),
    _u("writer_full_paper", "完整论文写作实战", "writer", "", UserLevel.ADVANCED,
       ["完整论文", "从零到一", "时间规划", "反复修改"], "editor", 90,
       prereqs=[{"unit_id": "writer_abs_01", "required_mastery": 0.7},
                {"unit_id": "writer_struct_01", "required_mastery": 0.7}],
       unit_type=UnitType.PROJECT),
]

# ══════════════════════════════════════════════════════════
# 路径生成
# ══════════════════════════════════════════════════════════

ALL_MODELER = (
    _MODELER_OPTIMIZATION + _MODELER_PREDICTION + _MODELER_EVALUATION +
    _MODELER_STATS_GRAPH + _MODELER_DE_COMPREHENSIVE
)

ALL_UNITS = {"modeler": ALL_MODELER, "programmer": _PROGRAMMER, "writer": _WRITER}


def generate_learning_path(
    role: AgentRole = AgentRole.MODELER,
    level: UserLevel = UserLevel.BEGINNER,
    goal: str = "国赛",
) -> LearningPath:
    """根据角色、水平、目标生成学习路径.

    - beginner: 仅入门级单元
    - intermediate: 入门快速浏览 + 进阶为主
    - advanced: 跳过入门基础 + 进阶 + 实战
    - competition: 全部 + 综合实战
    """
    all_units = ALL_UNITS.get(role.value, ALL_MODELER)

    if level == UserLevel.BEGINNER:
        filtered = [u for u in all_units if u.difficulty == UserLevel.BEGINNER]
    elif level == UserLevel.INTERMEDIATE:
        filtered = [u for u in all_units if u.difficulty in (UserLevel.BEGINNER, UserLevel.INTERMEDIATE)]
        # 入门级标记为已完成
        for u in filtered:
            if u.difficulty == UserLevel.BEGINNER:
                u.status = UnitStatus.COMPLETED
                u.mastery_score = 0.7
    elif level == UserLevel.ADVANCED or level == UserLevel.COMPETITION:
        filtered = [u for u in all_units]
        for u in filtered:
            if u.difficulty == UserLevel.BEGINNER:
                u.status = UnitStatus.COMPLETED
                u.mastery_score = 0.85
            elif u.difficulty == UserLevel.INTERMEDIATE:
                u.status = UnitStatus.COMPLETED
                u.mastery_score = 0.7

    # 按类别和难度分组
    cats: dict[str, dict[str, list[LearningUnit]]] = {}
    for u in filtered:
        cat = u.method_category or "通用"
        diff = u.difficulty.value
        cats.setdefault(cat, {}).setdefault(diff, []).append(u)

    phases = []
    cat_labels = {"优化": "优化方法", "预测": "预测与拟合", "评价": "评价与决策",
                  "统计": "统计分析方法", "图论": "图论与网络", "微分方程": "微分方程建模",
                  "综合": "综合应用", "": "通用基础"}
    diff_labels = {"beginner": "入门", "intermediate": "进阶", "advanced": "实战", "competition": "竞赛"}

    for cat, diffs in cats.items():
        for diff, units in diffs.items():
            phases.append(LearningPhase(
                name=f"{cat_labels.get(cat, cat)} · {diff_labels.get(diff, diff)}",
                description=f"{cat_labels.get(cat, cat)}的{diff_labels.get(diff, diff)}级内容",
                duration_weeks=2 if len(units) <= 3 else 3,
                units=units,
            ))

    return LearningPath(
        path_id=f"path_{role.value}_{level.value}",
        user_id="default", role=role, phases=phases,
    )


def get_unit_detail(unit_id: str) -> LearningUnit | None:
    for role_units in ALL_UNITS.values():
        for u in role_units:
            if u.unit_id == unit_id:
                return u
    return None
