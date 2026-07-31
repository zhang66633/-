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


# ══════════════════════════════════════════════════════════
# 学习内容库 (Markdown)
# ══════════════════════════════════════════════════════════

CONTENT_LIBRARY: dict[str, str] = {
    # ── 建模手·优化·入门 ──
    "modeler_lp_01": """# 线性规划与单纯形法

## 什么是线性规划？

线性规划是研究线性约束条件下线性目标函数极值问题的数学方法。它是运筹学中最基础也是最重要的分支。

## 标准形式

$$\\begin{aligned} \\min \\quad & c^T x \\\\ \\text{s.t.} \\quad & Ax = b \\\\ & x \\geq 0 \\end{aligned}$$

其中 $c$ 是目标函数系数，$A$ 是约束矩阵，$b$ 是右端项。

## 单纯形法核心思想

1. 从可行域的一个顶点出发
2. 沿着目标函数下降最快的边移动
3. 到相邻顶点继续迭代
4. 直到无法再下降 → 找到最优解

## 关键概念

- **可行域**: 所有满足约束条件的点的集合（凸多边形/多面体）
- **基变量/非基变量**: 单纯形表的结构基础
- **对偶理论**: 每个LP都有一个对偶问题，对偶价格反映资源价值

## 实战技巧

建模时先明确三要素：
1. **决策变量** — 我们要控制什么？
2. **目标函数** — 我们要最大化/最小化什么？
3. **约束条件** — 有什么限制？

> 💡 线性规划在建模竞赛中无处不在——运输问题、资源分配、生产规划...""",

    "modeler_lp_02": """# 线性规划建模实战

## 典型问题：运输问题

某公司有3个工厂供应4个城市，如何安排运输使总运费最小？

**决策变量**: $x_{ij}$ = 从工厂i运往城市j的货物量

$$\\min \\sum_i \\sum_j c_{ij} x_{ij}$$

**约束**: 每个工厂发量不能超过产能，每个城市收量要满足需求。

## 灵敏度分析

线性规划的灵敏度分析回答：
- 目标系数 $c$ 变化多少，最优解不变？
- 右端项 $b$ 增加1，目标值改善多少？（影子价格）

## Python 实现

```python
from scipy.optimize import linprog
c = [2, 3, 1]           # 目标系数
A = [[1, 2, 1], [2, 1, 1]]  # 约束矩阵
b = [10, 8]              # 右端项
res = linprog(c, A_ub=A, b_ub=b)
print(res.x)  # 最优解
```

## 常见建模技巧

- 最大化→ 目标系数取负转最小化
- 等式约束→ 拆成两个不等式
""",

    "modeler_ip_01": """# 整数规划与分支定界

## 什么是整数规划？

当决策变量必须是整数时（如人数、车辆数、是否选择），就是整数规划(IP)。

**分类**:
- 纯整数规划: 所有变量整数
- 混合整数规划(MIP): 部分变量整数
- 0-1规划: 变量只能取0或1

## 为什么比LP难？

LP最优解一定在顶点上（多项式时间）。
IP的可行域不是凸的，需要枚举，是NP-hard问题。

## 分支定界法

1. 先求解松弛的LP（忽略整数约束）
2. 如果解不满足整数，选一个分数变量 $x_i$
3. 分支成两个子问题: $x_i \\leq \\lfloor v \\rfloor$ 和 $x_i \\geq \\lceil v \\rceil$
4. 递归求解，剪枝（定界）已差于当前最优的分支

## 建模典型：设施选址

$y_j \\in \\{0,1\\}$: 是否在位置j建仓库
$x_{ij} \\geq 0$: 仓库j供应客户i的量""",

    "modeler_ip_02": """# 0-1规划与指派问题

## 0-1变量建模力量

0-1变量可以建模"选或不选"：

- $y_i = 1$ 表示选中方案i
- 互斥约束: $\\sum y_i \\leq 1$ (至多选一个)
- 条件约束: $x \\leq My$ (y=1时才允许x>0, M是大常数)

## 指派问题

n个人分配n个任务，第i人做第j任务的成本为 $c_{ij}$：

$$\\min \\sum_i \\sum_j c_{ij} x_{ij}$$

$$\\sum_i x_{ij} = 1 \\quad \\forall j$$
$$\\sum_j x_{ij} = 1 \\quad \\forall i$$
$$x_{ij} \\in \\{0,1\\}$$

**匈牙利算法** 可在 $O(n^3)$ 求解。

## Python求解

```python
from scipy.optimize import linear_sum_assignment
cost = [[4,1,3],[2,0,5],[3,2,2]]
row, col = linear_sum_assignment(cost)
print(list(zip(row, col)))  # 最优指派
```""",

    # ── 建模手·优化·进阶 ──
    "modeler_dp_01": """# 动态规划

## 核心思想

把复杂问题分解成子问题，利用子问题间的关系递推求解。两个关键性质：

1. **最优子结构**: 最优解包含子问题最优解
2. **重叠子问题**: 不同阶段共享相同子问题

## Bellman方程

$$V(s) = \\max_a \\{ R(s,a) + \\gamma V(s') \\}$$

## 经典例子

**背包问题**: n件物品，重量 $w_i$，价值 $v_i$，总容量W

$$dp[i][w] = \\max(dp[i-1][w], dp[i-1][w-w_i] + v_i)$$

**时间复杂度**: $O(nW)$

## DP vs 分治 vs 贪心

- 分治: 子问题独立（归并排序）
- 贪心: 每步最优→全局最优（Dijkstra）
- DP: 子问题重叠，记录避免重复计算""",

    "modeler_ga_01": """# 遗传算法(GA)

## 灵感来源

模拟自然界自然选择——适者生存，优胜劣汰。

## 算法流程

1. **编码**: 把解表示成染色体（二进制串/实数向量）
2. **初始化种群**: 随机生成N个个体
3. **评估适应度**: 计算每个个体的目标函数
4. **选择**: 适应度高的更可能被选中（轮盘赌/锦标赛）
5. **交叉**: 两个父代交换基因段 → 子代
6. **变异**: 小概率随机改变基因
7. 重复3-6直到收敛

## 关键参数

| 参数 | 典型值 | 说明 |
|------|--------|------|
| 种群大小 | 50-200 | 太大慢，太小多样性差 |
| 交叉率 | 0.6-0.9 | 探索新解 |
| 变异率 | 0.01-0.1 | 跳出局部最优 |

> 💡 GA适合复杂非线性、不可微、多峰优化问题""",

    "modeler_sa_01": """# 模拟退火算法(SA)

## 物理类比

加热金属后缓慢冷却——高温时原子剧烈运动(探索)，低温时趋于稳定(收敛)。

## Metropolis准则

从当前解x生成邻域解x'：
- 如果 $\\Delta E < 0$ (x'更优): 接受
- 如果 $\\Delta E > 0$ (x'更差): 以概率 $e^{-\\Delta E / T}$ 接受

温度T越高，接受差解的概率越大 → 跳出局部最优的能力

## 冷却策略

$$T_{k+1} = \\alpha \\cdot T_k, \\quad \\alpha \\in (0.9, 0.99)$$

- 退火太快→陷入局部最优
- 退火太慢→浪费时间

## GA vs SA

| 特性 | GA | SA |
|------|------|------|
| 并行性 | 种群并行 | 单点串行 |
| 全局搜索 | ✅ 强 | ⚠ 依赖冷却 |
| 局部精细 | 较弱 | ✅ 强 |
| 参数调优 | 复杂 | 较简单 |""",

    "modeler_pso_01": """# 粒子群优化(PSO)

## 灵感来源

鸟群觅食——每只鸟追自己的最佳位置，同时被群体最佳位置吸引。

## 速度更新公式

$$v_i^{t+1} = w v_i^t + c_1 r_1 (pbest_i - x_i^t) + c_2 r_2 (gbest - x_i^t)$$

- $w$: 惯性权重
- $c_1$: 个体认知系数
- $c_2$: 社会学习系数
- $pbest_i$: 粒子i的历史最佳位置
- $gbest$: 全局历史最佳位置

## Python实现关键

```python
class Particle:
    def __init__(self, dim):
        self.pos = np.random.uniform(-5, 5, dim)
        self.vel = np.zeros(dim)
        self.best_pos = self.pos.copy()
        self.best_val = float('inf')
```""",

    "modeler_multiobj": """# 多目标优化与NSGA-II

## 多目标困境

当有多个互相冲突的目标时，不存在"唯一最优"解。比如：成本最低 vs 质量最高。

## Pareto前沿

解A支配解B: A在所有目标上都不差于B，且至少一个更好。
Pareto最优解: 没有被任何其他解支配的解。
Pareto前沿: 所有Pareto最优解在目标空间中的像。

## NSGA-II算法

1. **非支配排序**: 将种群分成不同的Pareto层级
2. **拥挤度距离**: 在同一层中保持解的多样性
3. **锦标赛选择**: 优先选低层级 + 同层优先选高拥挤度
4. 交叉+变异生成子代
5. 合并父代子代，重新排序选择

## 应用场景

- 工程设计中成本 vs 性能的权衡
- 投资组合中收益 vs 风险的平衡""",

    "modeler_heuristic_practice": """# 启发式算法综合实战

## 问题选择指南

| 问题特点 | 推荐算法 |
|---------|---------|
| 组合优化(TSP,调度) | GA, ACO(蚁群) |
| 非线性连续优化 | PSO, SA |
| 多目标 | NSGA-II |
| 大规模+复杂约束 | GA + 罚函数 |

## 编码设计是核心

**好的编码 = 成功的一半**
- TSP用城市序列 → Permutation编码
- 背包问题用0/1 → Binary编码
- 连续参数优化 → Real编码

## 常见的坑

- 适应度函数设计不合理 → 收敛慢
- 约束处理不当 → 大量不可行解
- 参数调优不够 → 不如确定性方法""",

    # ── 建模手·预测·入门 ──
    "modeler_reg_01": """# 线性回归

## 最小二乘法

给定数据点 $(x_i, y_i)$，找直线 $y = \\beta_0 + \\beta_1 x$ 使残差平方和最小：

$$\\min_{\\beta_0,\\beta_1} \\sum_{i=1}^n (y_i - \\beta_0 - \\beta_1 x_i)^2$$

求解公式：

$$\\hat{\\beta_1} = \\frac{\\sum(x_i-\\bar{x})(y_i-\\bar{y})}{\\sum(x_i-\\bar{x})^2}, \\quad \\hat{\\beta_0} = \\bar{y} - \\hat{\\beta_1}\\bar{x}$$

## 拟合优度 $R^2$

$$R^2 = 1 - \\frac{SS_{res}}{SS_{tot}}$$

$R^2 \\in [0,1]$ 越接近1拟合越好。但$R^2$高不代表模型好！

## 残差分析

- 残差应随机分布 → 否则模型形式不对
- 残差应等方差 → 否则需加权/变换
- 残差应独立（自相关）→ 时间序列尤其注意""",

    "modeler_reg_02": """# 多元回归

## 从一元到多元

$$y = \\beta_0 + \\beta_1 x_1 + \\beta_2 x_2 + ... + \\beta_p x_p + \\varepsilon$$

矩阵形式: $y = X\\beta + \\varepsilon$

最小二乘解: $\\hat{\\beta} = (X^TX)^{-1}X^Ty$

## 多重共线性

当 $x_1$ 和 $x_2$ 高度相关时，$X^TX$ 接近奇异 → 系数估计不稳定。

**检测**: VIF > 10 表示严重共线性
**处理**: 删除变量 / 正则化(Ridge/Lasso) / PCA降维

## 逐步回归

- **前向**: 逐个加入最显著的变量
- **后向**: 从全模型逐个删除最不显著的
- **逐步**: 每步可能加入或删除

> ⚠ 逐步回归容易过拟合，交叉验证是更好的变量选择方法""",

    "modeler_grey_01": """# 灰色预测

## 适用场景

- 样本量小 (4-10个数据点)
- 信息不完全（灰=部分已知部分未知）
- 趋势单调（递增或递减）

## GM(1,1)模型

对原始序列 $x^{(0)}$ 做一次累加(AGO)：$x^{(1)}(k) = \\sum_{i=1}^k x^{(0)}(i)$

然后建立微分方程：

$$\\frac{dx^{(1)}}{dt} + a x^{(1)} = b$$

用最小二乘估计 $a,b$，再还原得到预测值。

## 精度检验

- **后验差比值C**: C越小越好 (<0.35=优)
- **小误差概率P**: P越大越好 (>0.95=优)

## 常见坑

- 数列必须是非负的
- 预测步数不宜太多 (≤3步)
- 非单调数列效果差""",

    # ── 更多内容继续 ──
    "modeler_arima_01": """# 时间序列与ARIMA

## ARIMA(p,d,q)

- **AR(p)**: 自回归 — $y_t = c + \\phi_1 y_{t-1} + ... + \\phi_p y_{t-p}$
- **I(d)**: 差分 — d阶差分使序列平稳
- **MA(q)**: 移动平均 — $y_t = \\mu + \\varepsilon_t + \\theta_1 \\varepsilon_{t-1} + ...$

## 建模步骤

1. 画时序图，判断趋势/季节/周期
2. 平稳性检验(ADF检验)，不平稳则差分
3. ACF + PACF 图确定 p,q
4. 拟合模型，残差白噪声检验
5. 预测

## Python工具

```python
from statsmodels.tsa.arima.model import ARIMA
model = ARIMA(data, order=(1,1,1))
result = model.fit()
forecast = result.forecast(steps=5)
```""",

    "modeler_nn_01": """# 神经网络预测

## 基本结构

输入层 → 隐藏层(激活函数) → 输出层

$$h = \\sigma(W_1 x + b_1)$$
$$\\hat{y} = W_2 h + b_2$$

## 激活函数

- **Sigmoid**: $\\sigma(z) = 1/(1+e^{-z})$ → (0,1)
- **ReLU**: $f(z) = \\max(0,z)$ → 缓解梯度消失
- **tanh**: $\\tanh(z)$ → (-1,1)

## 反向传播

用链式法则计算每层参数的梯度，从输出层向输入层传播误差。

## 过拟合对策

- 早停(Early Stopping)
- Dropout(训练时随机丢弃神经元)
- L2正则化""",

    "modeler_rf_01": """# 随机森林

## 集成学习思想

多个弱学习器组合成强学习器。

## Bagging

Bootstrap抽样→训练多棵树→投票(分类)/平均(回归)

$$\\hat{f}(x) = \\frac{1}{B}\\sum_{b=1}^B \\hat{f}_b(x)$$

## 随机森林特有

除Bootstrap抽样数据外，每次分裂时还随机选择特征子集 → 树之间更有差异性

## 特征重要性

计算每个特征在分裂时减少的不纯度总和 / 置换后性能下降量

> 💡 RF不容易过拟合，对缺失值和异常值鲁棒""",

    # ── 建模手·评价 ──
    "modeler_ahp_01": """# 层次分析法(AHP)

## 三步法

1. **建立层次结构**: 目标→准则→方案
2. **成对比较矩阵**:

$$A = \\begin{bmatrix} 1 & a_{12} & a_{13} \\\\ 1/a_{12} & 1 & a_{23} \\\\ 1/a_{13} & 1/a_{23} & 1 \\end{bmatrix}$$

用1-9标度: 1=同等, 3=稍微, 5=明显, 7=强烈, 9=极端

3. **一致性检验**:

$$CR = \\frac{CI}{RI} < 0.1 \\text{ 才可接受}$$

$$CI = \\frac{\\lambda_{max} - n}{n-1}$$

当 $CR \\geq 0.1$ 时说明判断矩阵有逻辑矛盾，需要调整。
""",

    "modeler_ahp_02": """# 模糊AHP

## 为什么需要模糊？

传统AHP用精确数字(1,3,5,7,9)，但人的判断其实是模糊的——"稍微重要"和"明显重要"的边界是模糊的。

## 三角模糊数

用 $(l, m, u)$ 替代精确值:
- l: 最低可能值
- m: 最可能值
- u: 最高可能值

## 群体决策

多个专家的判断矩阵如何综合？
- 几何平均: $a_{ij} = \\sqrt[n]{a_{ij}^{(1)} \\cdot ... \\cdot a_{ij}^{(n)}}$
- 加权平均后一致性检验

> 当多个评委意见不一致时，模糊AHP比传统AHP更合理""",

    "modeler_topsis_01": """# TOPSIS法

## 核心思想

最优方案应该最接近理想解，同时最远离负理想解。

## 计算步骤

1. 构建决策矩阵并标准化
2. 加权标准化矩阵（权重要先确定）
3. 确定理想解 $A^+$ 和负理想解 $A^-$
4. 计算各方案到两者的欧氏距离
5. 计算贴近度: $C_i = \\frac{D_i^-}{D_i^+ + D_i^-}$

## TOPSIS vs AHP

- AHP: 主观赋权，适用于指标少的层次决策
- TOPSIS: 需要外部权重，适用于数据多的排序
- **熵权TOPSIS**: 先用熵权法客观赋权，再用TOPSIS排序""",

    "modeler_entropy": """# 熵权法

## 信息熵

$$e_j = -k \\sum_{i=1}^n p_{ij} \\ln(p_{ij})$$

- 熵越小 → 该指标数据差异大 → 提供信息多 → 权重应大
- 熵越大 → 该指标数据差异小 → 提供信息少 → 权重应小

## 权重计算

$$w_j = \\frac{1 - e_j}{\\sum_{j=1}^m (1 - e_j)}$$

## 客观 vs 主观赋权

- 客观: 熵权法、CRITIC、变异系数
- 主观: AHP、专家打分
- **组合赋权**: $w = \\alpha w_{subj} + (1-\\alpha) w_{obj}$

> 熵权法完全基于数据，不受人为主观影响""",

    "modeler_fuzzy_eval": """# 模糊综合评价

## 为什么用模糊数学？

评价"服务态度好"——多少分算好？85? 90? 这种边界是模糊的。

## 隶属函数

把精确值映射到[0,1]，表示"属于某个等级的程度":

- **三角形**: 简单常用
- **梯形**: 中间平顶（完全属于该等级）
- **高斯型**: 平滑过渡

## 评价步骤

1. 确定评价因素集 U 和评语集 V
2. 构造隶属函数，计算模糊关系矩阵 R
3. 确定权重 A
4. 模糊合成: B = A∘R
5. 去模糊化得到最终评价

> 特别适合处理"好/中/差"这种定性指标""",

    "modeler_dea_01": """# 数据包络分析

## 什么是DEA？

评价多投入多产出决策单元(DMU)的相对效率。不需要预设生产函数形式——完全数据驱动。

## CCR模型

$$\\max \\frac{\\sum_r u_r y_{rk}}{\\sum_i v_i x_{ik}}$$

s.t. 所有DMU的效率 ≤ 1

线性化后变成线性规划问题。

## BCC模型

CCR假设规模报酬不变(CRS)，BCC放宽为可变规模报酬(VRS) → 效率分解为纯技术效率×规模效率

## 典型应用

- 银行效率评价
- 学校/医院绩效评估
- 城市发展效率""",

    "modeler_grey_rel": """# 灰色关联分析

## 基本思想

根据序列曲线几何形状的相似程度判断关联度。曲线越接近，关联度越大。

## 邓氏关联度

1. 无量纲化（初值化/均值化）
2. 计算关联系数:
$$\\xi_i(k) = \\frac{\\min\\min + \\rho \\max\\max}{|x_0(k)-x_i(k)| + \\rho \\max\\max}$$
3. 求平均得关联度 $r_i$

$\\rho$ 为分辨系数，通常取0.5。

## 适用场景

- 样本量小的综合评价
- 影响因素排序/筛选
- 当指标间有灰色关系时""",

    # ── 建模手·统计 ──
    "modeler_mle_01": """# 极大似然估计(MLE)

## 核心问题

给定数据，什么样的参数最有可能产生这些数据？

## 似然函数

$$L(\\theta|X) = \\prod_{i=1}^n f(x_i|\\theta)$$

取对数简化计算: $\\ell(\\theta) = \\sum \\ln f(x_i|\\theta)$

求极值: $\\frac{d\\ell}{d\\theta} = 0$

## 经典例子

正态分布 $N(\\mu,\\sigma^2)$ 的MLE:
$\\hat{\\mu} = \\bar{x}, \\hat{\\sigma}^2 = \\frac{1}{n}\\sum (x_i-\\bar{x})^2$

## MLE vs 矩估计

- MLE: 渐近有效，大样本最优；但需要指定分布
- 矩估计: 简单粗暴，不一定有效""",

    "modeler_bayes_01": """# 贝叶斯推断

## 贝叶斯公式

$$P(\\theta|D) = \\frac{P(D|\\theta) \\cdot P(\\theta)}{P(D)}$$

后验 ∝ 似然 × 先验

## 先验选择

- **共轭先验**: 后验与先验同分布（方便计算）
- **无信息先验**: 假设对所有参数值无偏好
- **主观先验**: 基于专家知识

## MCMC方法

当后验分布复杂无法直接采样时，用MCMC(马尔可夫链蒙特卡洛):
- **Metropolis-Hastings**: 提议+接受/拒绝
- **Gibbs抽样**: 逐个条件分布采样

> 贝叶斯的核心优势：自然融入先验知识 + 输出完整概率分布而非点估计""",

    "modeler_mc_01": """# 蒙特卡洛模拟

## 核心思想

用大量随机抽样来近似求解：

$$I = \\int f(x)dx \\approx \\frac{V}{N}\\sum_{i=1}^N f(x_i)$$

$x_i$ 是均匀随机采样点。

## 经典应用

1. 估算 $\\pi$: 在正方形里随机撒点，数圆内点数
2. 期权定价: 模拟股价路径
3. 可靠性分析: 模拟系统各组件失效

## 方差缩减

- **重要性抽样**: 在"重要"区域多采样
- **分层抽样**: 把采样域分层
- **对偶变量**: 成对使用正负相关样本

## 收敛判断

误差 $\\propto 1/\\sqrt{N}$，N需足够大（通常>=10000）""",

    "modeler_pca_01": """# 主成分分析(PCA)

## 目的

降维——用少数几个主成分代表原始多个变量的大部分信息。

## 原理

1. 数据中心化/标准化
2. 计算协方差矩阵
3. 求特征值和特征向量
4. 按特征值大小排序→前k个即k个主成分

## 方差解释率

$$\\frac{\\lambda_i}{\\sum \\lambda_j}$$ 表示第i个主成分解释了多大比例的总方差。累加到80-90%选k。

## 应用场景

- 高维数据可视化(降到2-3维)
- 消除多重共线性
- 数据压缩、去噪
- 综合评价(第一主成分评分)""",

    # ── 建模手·图论 ──
    "modeler_shortest": """# 最短路径算法

## Dijkstra算法

单源最短路径，要求边权非负:

1. 初始化: 源点距离0，其他无穷大
2. 选未访问中距离最小的点u
3. 更新u的邻居 v: d[v] = min(d[v], d[u]+w(u,v))
4. 标记u已访问，重复2-3

时间复杂度: $O((V+E)\\log V)$ (优先队列)

## Floyd算法

所有点对最短路径: $O(V^3)$

$$d[i][j] = \\min(d[i][j], d[i][k] + d[k][j])$$

## 建模中什么时候用？

- 物资配送路径规划
- 网络传输延迟最小化
- 地图导航""",

    "modeler_network": """# 网络流与最大流

## 最大流问题

在网络中从源点s到汇点t能传输的最大流量是多少？

## Ford-Fulkerson算法

1. 找到一条从s到t的增广路径（剩余容量>0）
2. 沿路径推送尽可能多的流量
3. 更新剩余容量
4. 重复直到无增广路径

## 最大流=最小割

网络中s-t最小割的容量 = s-t最大流的值

## Edmonds-Karp

用BFS找最短增广路径 → $O(VE^2)$

## 建模应用

- 交通运输网络容量
- 生产流水线瓶颈分析
- 二分图匹配""",

    "modeler_mst": """# 最小生成树(MST)

## 问题定义

连接n个节点的最小总权重树。

## Prim算法

从任意节点开始，贪心地加入距离当前树最近的节点 → $O(E \\log V)$

## Kruskal算法

按边权排序，贪心地加入不构成环的最小边（并查集判环）→ $O(E \\log E)$

## TSP问题

旅行商问题——访问所有城市恰好一次再返回，路径最短。
NP-hard，常用解法: 动态规划($O(n^2 2^n)$)，贪心，遗传算法，蚁群算法""",

    # ── 建模手·微分方程 ──
    "modeler_ode_01": """# 常微分方程建模

## 经典ODE模型

**人口增长**:
$$\\frac{dN}{dt} = rN(1-\\frac{N}{K})$$ (Logistic方程)

**传染病SIR**:
$$\\frac{dS}{dt} = -\\beta SI, \\frac{dI}{dt} = \\beta SI - \\gamma I$$

**弹簧振动**:
$$m\\frac{d^2x}{dt^2} + c\\frac{dx}{dt} + kx = 0$$

## 求解方法

- 解析解: 分离变量、积分因子
- 数值解: Euler法、Runge-Kutta(4阶)

## Python

```python
from scipy.integrate import solve_ivp
def f(t, y): return -0.5 * y
sol = solve_ivp(f, [0,10], [1])
```""",

    "modeler_pde_01": """# 偏微分方程有限差分

## 三大经典PDE

- **热传导**: $u_t = \\alpha u_{xx}$
- **波动方程**: $u_{tt} = c^2 u_{xx}$
- **Laplace**: $u_{xx} + u_{yy} = 0$

## 有限差分法

用差商近似微商：
$$u_t \\approx \\frac{u(x,t+\\Delta t)-u(x,t)}{\\Delta t}$$
$$u_{xx} \\approx \\frac{u(x+\\Delta x)-2u(x)+u(x-\\Delta x)}{(\\Delta x)^2}$$

## 稳定性条件

显式格式需满足CFL条件: $\\Delta t \\leq (\\Delta x)^2/(2\\alpha)$

> PDE建模常用于物理过程模拟——热扩散、污染物传播、声波""",

    # ── 建模手·综合 ──
    "modeler_queue_01": """# 排队论

## M/M/1模型

- M: 到达间隔指数分布(Poisson过程)
- M: 服务时间指数分布
- 1: 单服务台

## Little公式

$$L = \\lambda W$$
系统中平均人数 = 到达率 × 平均逗留时间

## 性能指标

$$\\rho = \\lambda/\\mu$$ (服务强度, <1才稳定)
$$L_q = \\frac{\\rho^2}{1-\\rho}$$ (队列长度)

## 建模应用

- 银行/医院窗口数量设计
- 呼叫中心人员配置
- 红绿灯周期优化""",

    "modeler_game_01": """# 博弈论

## 基本元素

- 参与者(Players)
- 策略(Strategies)
- 收益(Payoffs)

## Nash均衡

每个参与者在给定他人策略下，没有动机单方面改变自己的策略。

**囚徒困境**: 个体理性导致集体非最优。

## 演化博弈

引入"复制者动态"，策略的增长率与其适应性成比例 → 稳定策略ESS

## 建模应用

- 寡头竞争(定价/产量博弈)
- 环境治理(搭便车问题)
- 拍卖机制设计""",

    "modeler_ca_01": """# 元胞自动机

## 基本概念

网格上每个元胞有有限个状态，根据邻居状态按规则同步更新。

## 经典例子

- **生命游戏**(Game of Life): 2D, 二状态, 简单规则产生复杂模式
- **交通流**(NaSch模型): 1D, 模拟车辆加减速/随机慢化
- **森林火灾**: 树木/燃烧/空地三状态

## 特点

- 简单规则→涌现复杂行为
- 完全离散(空间+时间+状态)
- 适合模拟人群疏散、城市扩张等""",

    "modeler_model_combo": """# 组合模型

## 为什么组合？

单个模型各有优劣，组合可以实现"1+1>2"。

## 组合方式

- **串联**: 模型A的输出→模型B的输入（如先用灰色预测趋势再用ARIMA预测细节）
- **并联**: 多个模型独立预测→加权平均
- **嵌套**: 一个模型优化另一个模型的参数

## 模型融合

- **Bagging**: Bootstrap采样→多个模型→投票
- **Boosting**: 串行训练，后一个修正前一个的误差
- **Stacking**: 多个基模型→元模型做最终预测

> 组合模型的key: 基模型要有差异性(不同类型的模型效果更好)""",

    # ── 进阶·预测 ──
    "modeler_shortest": "# 最短路径算法\n\n## Dijkstra\n单源最短路径，要求边权非负。$O((V+E)\\log V)$\n\n## Floyd\n所有点对最短路径: $O(V^3)$\n$$d[i][j] = \\min(d[i][j], d[i][k] + d[k][j])$$\n\n## 建模应用\n物资配送路径、网络延迟最小化",

    # ── 编程手 ──
    "prog_py_01": """# Python科学计算入门

## 为什么学？
数学建模竞赛中，Python凭借NumPy/SciPy/Pandas/Matplotlib四件套成为最主流的编程语言。

## NumPy基础
```python
import numpy as np
arr = np.array([1,2,3,4,5])
zeros = np.zeros((3,4))
linear = np.linspace(0,1,100)
```
向量化运算不用写循环: `a + b`, `a * b`, `np.sin(a)`

## 矩阵运算
```python
C = A @ B          # 矩阵乘法
inv_A = np.linalg.inv(A)  # 求逆
eigvals = np.linalg.eigvals(A)  # 特征值
```""",

    "prog_py_02": """# NumPy数组实战

## 广播机制
不同形状数组也能运算——NumPy自动扩展维度:
```python
arr = np.array([1,2,3])
print(arr + 10)  # [11 12 13]
```

## 索引与切片
```python
arr[1:5, 2:4]     # 子矩阵
arr[:, 1]         # 第2列
arr[arr > 0]      # 布尔索引
```

## 练习
用向量化实现 $\\sum x_i^2$ (不用for循环)""",

    "prog_pandas_01": """# Pandas数据处理

## DataFrame
```python
import pandas as pd
df = pd.read_csv('data.csv')
df.head()
df.describe()
```

## 数据清洗
```python
df.dropna()            # 删除缺失值
df.fillna(df.mean())   # 均值填充
df.drop_duplicates()   # 去重
```

## GroupBy
```python
df.groupby('category').mean()
df.groupby('year').agg({'price':'mean','amount':'sum'})
```""",

    "prog_viz_01": """# Matplotlib可视化

## 基本绘图
```python
import matplotlib.pyplot as plt
plt.plot(x, y, 'b-', label='数据')
plt.xlabel('x'); plt.ylabel('y')
plt.legend(); plt.show()
```

## 常用图表
- 折线图 `plt.plot()`
- 散点图 `plt.scatter()`
- 柱状图 `plt.bar()`
- 热力图 `plt.imshow()`

## 论文级图表
```python
plt.rcParams['font.size'] = 12
fig, ax = plt.subplots(figsize=(8,5))
ax.plot(x, y, linewidth=2)
ax.grid(True, alpha=0.3)
```""",

    "prog_optimize_01": """# scipy.optimize求解优化

## 线性规划
```python
from scipy.optimize import linprog
res = linprog(c, A_ub=A, b_ub=b, bounds=[(0,None)])
```

## 非线性规划
```python
from scipy.optimize import minimize
def f(x): return (x[0]-1)**2 + (x[1]-2)**2
res = minimize(f, [0,0], method='SLSQP')
```

## 约束
- `bounds`: 变量取值范围
- `constraints`: {'type':'eq','fun':g} 等式或不等式约束""",

    "prog_cvxpy_01": """# cvxpy凸优化

## 为什么用cvxpy？
声明式建模——你描述问题，cvxpy自动选求解器。

```python
import cvxpy as cp
x = cp.Variable(3)
obj = cp.Minimize(cp.sum_squares(x - [1,2,3]))
constraints = [x >= 0, cp.sum(x) == 1]
prob = cp.Problem(obj, constraints)
prob.solve()
```

## 支持的问题类型
- LP, QP, SOCP, SDP
- 支持CPLEX/Gurobi/MOSEK等商业求解器""",

    "prog_sklearn_01": """# sklearn机器学习

## 统一API
```python
from sklearn.ensemble import RandomForestClassifier
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)
```

## 常用模型
- 分类: RandomForest, SVM, LogisticRegression
- 回归: LinearRegression, Ridge, Lasso
- 聚类: KMeans, DBSCAN
- 降维: PCA

## 模型评估
```python
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import cross_val_score
```""",

    "prog_networkx_01": """# networkx图论编程

```python
import networkx as nx
G = nx.Graph()
G.add_edges_from([(1,2),(2,3),(3,1)])
nx.shortest_path(G, 1, 3)    # 最短路径
nx.max_flow(G, s, t)          # 最大流
nx.minimum_spanning_tree(G)   # 最小生成树
```""",

    "prog_ga_impl": """# 遗传算法自实现

## 核心代码
```python
def genetic_algorithm(pop_size, generations):
    pop = init_population(pop_size)
    for gen in range(generations):
        fitness = evaluate(pop)
        parents = select(pop, fitness)
        offspring = crossover(parents)
        offspring = mutate(offspring)
        pop = offspring
    return best(pop)
```

## 关键设计
- 编码: 把解映射到染色体
- 适应度: 目标函数→非负值
- 约束: 罚函数 / 修复算子""",

    "prog_seaborn_01": """# Seaborn高级可视化

```python
import seaborn as sns
sns.heatmap(corr_matrix, annot=True)
sns.pairplot(df, hue='category')
sns.boxplot(x='group', y='value', data=df)
sns.violinplot(x='group', y='value', data=df)
```

比Matplotlib更美观，统计图一行代码搞定。""",

    "prog_sympy_01": """# SymPy符号计算

```python
from sympy import *
x, y = symbols('x y')
diff(sin(x)*exp(x), x)   # 求导
integrate(x**2, x)       # 积分
solve(x**2 - 4, x)       # 解方程
limit(sin(x)/x, x, 0)    # 求极限
```""",

    "prog_perf_01": """# 代码性能优化

## 向量化
```python
# 慢: for循环
result = [f(x) for x in data]
# 快: NumPy向量化
result = np.vectorize(f)(data)
```

## 其他技巧
- 用`numba` JIT编译
- 避免在循环中append
- 用`itertools`处理组合/排列""",

    "prog_pipeline_01": """# 数据处理流水线

## sklearn Pipeline
```python
from sklearn.pipeline import Pipeline
pipe = Pipeline([
    ('scaler', StandardScaler()),
    ('pca', PCA(n_components=10)),
    ('model', RandomForestClassifier())
])
pipe.fit(X_train, y_train)
```

一条龙：预处理→特征工程→模型。避免数据泄露。""",

    # ── 论文手 ──
    "writer_abs_01": """# 摘要撰写

## 黄金公式
**背景+问题+方法+结果+结论** = 完整摘要

## 国赛要求
400-500字，必须包含**具体数值结果**，不能泛泛而谈。

## 模板
针对[问题背景]...建立了[什么模型]...采用[什么方法]求解...得到[具体数值]...结果表明[结论]。

## 常见错误
- "本文对问题进行了分析" → 太泛
- 没有具体数字 → 不合格
- 摘要不包含模型假设""",

    "writer_abs_02": """# 摘要写作练习

## 练习方法
1. 找一篇国赛优秀论文，遮住摘要
2. 自己根据正文写一篇摘要
3. 对照原文找差距

## 检查清单
- [ ] 是否包含具体数值？
- [ ] 是否在400-500字？
- [ ] 是否能独立于正文理解？
- [ ] 是否说明了模型和方法？
- [ ] 有没有关键词？""",

    "writer_struct_01": """# 论文结构

## 国赛标准结构
1. 摘要 (单独页)
2. 问题重述
3. 模型假设与符号说明
4. 模型建立与求解 (核心)
5. 模型检验与灵敏度分析
6. 模型评价与改进
7. 参考文献

## 叙事逻辑
从问题出发→一步步建立模型→验证→反思改进。
读者应该有"顺着一条线读完"的感觉。""",

    "writer_viz_01": """# 图表设计

## 图表选择
- 趋势→折线图
- 对比→柱状图
- 占比→饼图(少用)
- 分布→箱线图/直方图
- 关系→散点图

## 三线表
只有顶线、栏目线、底线，简洁明了。

## 图表原则
- 图表可以独立被理解(标题+坐标标签完整)
- 颜色对比度足够(打印后也能区分)
- 不重复呈现相同数据(图和表选其一)""",

    "writer_hypothesis": """# 模型假设

## 为什么需要假设？
现实世界太复杂，必须简化才能建模。好的假设是模型的基石。

## 假设原则
- **必要性**: 没有这个假设模型无法建立
- **合理性**: 简化的同时不能歪曲本质
- **可验证性**: 模型检验时能回头审视假设

## 典型假设
- 忽略次要因素（摩擦力、空气阻力）
- 线性近似（小范围内曲线≈直线）
- 均匀分布（空间、时间上的简化）""",

    "writer_result": """# 结果分析

## 怎么写？
不只是"结果见图3"，而要**解释**这幅图说明了什么。

## 从数据到结论
1. 展示结果（图/表）
2. 解读结果（这个值意味着什么）
3. 关联模型（这个结果验证了/挑战了模型的什么假设）
4. 引出下一步（基于这个结果，我们进一步...）

## 灵敏度分析
改变关键参数→观察结果变化→得出什么参数最重要。这是区分好论文和普通论文的关键。""",

    "writer_eval": """# 模型评价

## 写作结构
1. **优点**: 模型解决了什么问题？创新点在哪？
2. **缺点**: 模型的局限性？什么情况下不适用？
3. **改进方向**: 如果继续做，有哪些可以优化的地方？
4. **推广价值**: 这个模型还能用在哪些场景？

## 注意事项
- 优缺点要实事求是，不要自卖自夸
- 缺点不能是致命的（否则模型本身就有问题）
- 改进方向要具体，不要说"可以进一步优化模型"这种空话""",

    "writer_latex_01": """# LaTeX模板

## 国赛模板
使用 `cumcmthesis` 文档类：
```latex
\\documentclass{cumcmthesis}
\\begin{document}
\\title{论文标题}
\\maketitle
\\begin{abstract}...\\end{abstract}
\\section{问题重述}...
\\end{document}
```

## 公式排版
```latex
行内公式: $E=mc^2$
独立公式: $$\\sum_{i=1}^{n} x_i$$
多行对齐: \\begin{align}...\\end{align}
```""",

    "writer_reference": """# 文献检索

## 检索渠道
- Google Scholar (学术搜索)
- 知网 (中文论文)
- arXiv (预印本)
- GitHub (代码实现)

## 引用规范
```latex
\\cite{key} 引用某文献
\\bibliographystyle{plain}
\\bibliography{refs}
```

## BibTeX条目
```latex
@article{key,
  author={张三, 李四},
  title={论文标题},
  journal={期刊名},
  year={2024}
}
```""",

    "writer_full_paper": """# 完整论文写作

## 时间规划(3天赛)
- **Day 1上午**: 读懂题目, 查文献, 建初模
- **Day 1下午**: 模型细化, 开始写作(边做边写!)
- **Day 2**: 求解+写论文正文+做图表
- **Day 3上午**: 完成初稿, 修改摘要
- **Day 3下午**: 反复修改/检查格式

## 协作要点
- 论文手从Day 1就要参与, 不是最后才写
- 建模手需要向论文手解释清楚模型思路
- 编程手需要及时输出图表给论文手""",

    # ── 入门·优化·进阶·内容补齐 ──
    "modeler_ant_colony": """# 蚁群算法(ACO)

## 灵感
蚂蚁在路径上留下信息素——路径越短，蚂蚁往返越快→信息素越浓→更多蚂蚁选择。

## 算法
1. 每只蚂蚁从起点出发构建解(概率选择)
2. 更新信息素: $\\tau_{ij} = (1-\\rho)\\tau_{ij} + \\sum \\Delta\\tau_{ij}^k$
3. $\\rho$是挥发率, $\\Delta\\tau$与路径长度成反比
4. 迭代直到收敛

## 经典应用: TSP
```python
# 转移概率: P_ij ∝ (τ_ij)^α · (1/d_ij)^β
# α=信息素权重, β=启发式权重
prob = (tau[i][j]**alpha) * ((1.0/dist)**beta)
```""",

    "modeler_convex_opt": """# 凸优化

## 凸集
集合内任意两点连线上的点仍在集合内。

## 凸函数
$$f(\\lambda x + (1-\\lambda)y) \\leq \\lambda f(x) + (1-\\lambda)f(y)$$

## KKT条件
对凸优化问题: $\\min f(x)$ s.t. $g_i(x) \\leq 0, h_j(x)=0$

KKT条件是最优性的一阶必要条件(对凸问题是充要条件)。

## 对偶理论
每个优化问题有一个对偶问题→对偶间隙(Duality Gap) → 凸问题为0""",
}

# ══════════════════════════════════════════════════════════

def _u(unit_id, title, role, cat, diff, tags, agent, minutes=30,
       prereqs=None, unit_type=UnitType.KNOWLEDGE):
    return LearningUnit(
        unit_id=unit_id, title=title, role=role, type=unit_type,
        difficulty=diff, method_category=cat, tags=tags,
        primary_agent=agent, estimated_minutes=minutes,
        prerequisites=prereqs or [],
        content_md=CONTENT_LIBRARY.get(unit_id, f"# {title}\n\n学习资料正在准备中。"),
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
            phases.append(LearningPhase(
                name=f"{cat_labels.get(cat, cat)} · {diff_labels.get(diff, diff)}",
                description=f"{cat_labels.get(cat, cat)}的{diff_labels.get(diff, diff)}级内容",
                duration_weeks=2 if len(units) <= 3 else 3,
                units=units,
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
