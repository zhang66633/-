# 数据包络分析(DEA)

> **难度**:实战 · **预计学习时长**:50 分钟 · **主讲智能体**:🧩 建模手 · **方法类别**:效率评价

## 🎯 学习目标

学完本单元,你应该能够:

- 解释 DEA 的建模思想:不预设生产函数,从数据中「包络」出效率前沿
- 写出 CCR 与 BCC 模型的分式规划、线性化形式与包络形式
- 区分技术效率、纯技术效率与规模效率,并会做分解
- 用 NIRS 模型判断规模报酬递增/递减
- 独立完成一次小规模 DEA 计算,并写出可运行的求解代码

> 前置:DEA 的求解核心是线性规划,建议先复习《线性规划与单纯形法》单元。

## 📖 核心概念

### 1. DEA 评价什么

数据包络分析(Data Envelopment Analysis)由 Charnes、Cooper 与 Rhodes 于 1978 年提出,用于评价一组**同类型决策单元(DMU, Decision Making Unit)的相对效率**。典型对象:银行分行、医院、高校、城市、企业——它们都用多种**投入**(人员、资金、设施)生产多种**产出**(服务量、成果、产值)。

DEA 的独特之处:**不需要预先假设生产函数形式**(如柯布-道格拉斯函数),而是从样本数据本身构造「效率前沿面」,把 DMU 与前沿面的距离作为效率。因此它特别适合投入产出关系复杂、难以参数化的场景。

### 2. 效率的几何含义

设每个 DMU 有 $m$ 种投入 $x$、$s$ 种产出 $y$。**投入导向**的效率问的是:在产出不减少的前提下,投入最多能按比例压缩到多少?

$$\text{技术效率 } \theta = \frac{\text{前沿面上的目标投入}}{\text{实际投入}} \in (0, 1]$$

$\theta = 1$ 表示 DMU 在前沿面上(相对有效);$\theta = 0.8$ 表示「同样的产出,别人只需要你 80% 的投入」。1 减 $\theta$ 就是可节约的比例。

### 3. CCR 模型:规模报酬不变(CRS)

CCR 假设**规模报酬不变**:投入翻倍产出也翻倍,任何规模下效率比较基准相同。分式规划形式(DMU $k$):

$$\max \frac{\sum_{r=1}^{s} u_r y_{rk}}{\sum_{i=1}^{m} v_i x_{ik}} \quad \text{s.t.} \quad \frac{\sum_r u_r y_{rj}}{\sum_i v_i x_{ij}} \le 1 \ (\forall j), \quad u_r, v_i \ge 0$$

含义:为 DMU $k$ 寻找一组**对它最有利的权重** $(u, v)$,使它的「加权产出/加权投入」最大化;约束保证同一组权重下没有任何 DMU 的比值超过 1。这是典型的「自己给自己打最高分,但不允许别人超满分」的自我评价。

### 4. Charnes-Cooper 变换与包络形式

分式规划非线性,作变换 $t = 1\big/\sum_i v_i x_{ik}$、$\mu = t u$、$\nu = t v$,化为线性规划(乘子形式):

$$\max \sum_{r} \mu_r y_{rk} \quad \text{s.t.} \quad \sum_i \nu_i x_{ik} = 1, \quad \sum_r \mu_r y_{rj} - \sum_i \nu_i x_{ij} \le 0 \ (\forall j), \quad \mu_r, \nu_i \ge 0$$

其对偶(包络形式,投入导向)是计算中最常用的:

$$\min \theta \quad \text{s.t.} \quad \sum_j \lambda_j y_{rj} \ge y_{rk} \ (\forall r), \quad \sum_j \lambda_j x_{ij} \le \theta\, x_{ik} \ (\forall i), \quad \lambda_j \ge 0$$

$\lambda$ 的直观意义:用其他 DMU 的线性组合「合成」一个虚拟 DMU,要求产出不低于 DMU $k$、投入不超过 $\theta$ 倍的 DMU $k$;$\theta$ 压缩得越小,说明 DMU $k$ 越远离前沿。

### 5. BCC 模型:可变规模报酬(VRS)与效率分解

Banker、Charnes 与 Cooper 于 1984 年放宽 CRS 假设,在包络形式中加入凸性约束 $\sum_j \lambda_j = 1$,即 BCC 模型(VRS)。由此得到效率分解:

$$\underbrace{\theta_{\text{CCR}}}_{\text{技术效率 TE}} = \underbrace{\theta_{\text{BCC}}}_{\text{纯技术效率 PTE}} \times \underbrace{SE}_{\text{规模效率}}$$

- **纯技术效率**(PTE):剔除规模因素后,管理/技术层面的效率
- **规模效率**(SE):当前规模距离「最优规模」的差距;$SE < 1$ 时需判断是规模报酬递增(IRS,规模太小,应扩张)还是递减(DRS,规模太大,应收缩)

**判断 IRS/DRS 的方法**:加解一个 NIRS 模型(约束改为 $\sum_j \lambda_j \le 1$)。若 $\theta_{\text{NIRS}} = \theta_{\text{CCR}}$,则规模报酬**递增**;若 $\theta_{\text{NIRS}} = \theta_{\text{BCC}}$,则规模报酬**递减**。

### 6. 输出导向与其他扩展

- **输出导向**(产出不增投入的前提下按比例扩张产出):$\max \varphi$ s.t. $\sum_j \lambda_j y_{rj} \ge \varphi y_{rk}$, $\sum_j \lambda_j x_{ij} \le x_{ik}$;效率值取 $1/\varphi$。CRS 下输入、输出导向结果相同
- **超效率 DEA**(Super-efficiency):评价 DMU 时把它自己从参考集中剔除,允许效率 > 1,用于给「有效单元」继续排序
- **SBM 模型**(基于松弛变量):同时考虑径向改进与松弛改进,克服 CCR 对「弱有效」(θ=1 但仍有松弛)不敏感的问题
- **Malmquist 指数**:面板数据下分解效率变化为技术进步与效率追赶,动态分析的标配

## 🧮 公式与结论

### 三个模型一览(投入导向,包络形式)

$$\begin{aligned} \text{CCR(CRS)}: & \quad \min \theta \ \ \text{s.t.} \ Y\lambda \ge y_k,\ X\lambda \le \theta x_k,\ \lambda \ge 0 \\ \text{BCC(VRS)}: & \quad \min \theta \ \ \text{s.t.} \ Y\lambda \ge y_k,\ X\lambda \le \theta x_k,\ \sum_j \lambda_j = 1,\ \lambda \ge 0 \\ \text{NIRS}: & \quad \min \theta \ \ \text{s.t.} \ Y\lambda \ge y_k,\ X\lambda \le \theta x_k,\ \sum_j \lambda_j \le 1,\ \lambda \ge 0 \end{aligned}$$

### 效率分解与规模报酬判定

$$TE = \theta_{\text{CCR}}, \quad PTE = \theta_{\text{BCC}}, \quad SE = \frac{TE}{PTE} = \frac{\theta_{\text{CCR}}}{\theta_{\text{BCC}}} \le 1$$

$$\theta_{\text{NIRS}} = \theta_{\text{CCR}} \Rightarrow \text{IRS(规模报酬递增)}; \qquad \theta_{\text{NIRS}} = \theta_{\text{BCC}} \Rightarrow \text{DRS(规模报酬递减)}$$

### 单投入单产出特例(手算利器)

投入产出各为 1 维时,前沿退化为直线/折线,效率可直接用比值计算:

$$\text{CRS 前沿}: y = \max_j\left(\frac{y_j}{x_j}\right) x, \qquad \theta_k^{\text{CCR}} = \frac{y_k / x_k}{\max_j (y_j / x_j)}$$

## 💡 经典例题

### 例题 1:单投入单产出(全流程手算)

> 4 个同类物流站点,投入为员工数 $x$,产出为年处理订单量 $y$(万单):A(2, 2)、B(3, 4)、C(4, 7)、D(5, 8)。求 CCR、BCC 效率并做规模分析。

**第一步:CCR 效率。** 产出/投入比:$y/x = (1,\ 4/3,\ 7/4,\ 8/5)$,最大为 C 的 $7/4 = 1.75$。CRS 前沿是过原点的直线 $y = 1.75x$:

$$\theta^{\text{CCR}} = \frac{y_k/x_k}{1.75} = \left(\frac{4}{7},\ \frac{16}{21},\ 1,\ \frac{32}{35}\right) = (0.5714,\ 0.7619,\ 1,\ 0.9143)$$

**第二步:BCC 效率。** VRS 前沿是样本点的凹包络:连接 A(2,2)—C(4,7)(斜率 2.5)与 C(4,7)—D(5,8)(斜率 1),斜率递减 ✓。B(3,4) 落在 A-C 线段下方($x=3$ 处前沿产出 $2 + 2.5 = 4.5 > 4$),故 B 纯技术无效:

- B 的投入导向目标:$y = 4$ 时前沿投入 $x^* = 2 + (4-2)\times\dfrac{4-2}{7-2} = 2.8$,故 $\theta^{\text{BCC}}_B = \dfrac{2.8}{3} = 0.9333$
- 其余三点都在前沿上:$\theta^{\text{BCC}} = (1,\ 0.9333,\ 1,\ 1)$

**第三步:效率分解。**

| DMU | TE(CCR) | PTE(BCC) | SE = TE/PTE | 规模状态 |
|-----|---------|----------|-------------|----------|
| A | 0.5714 | 1 | **0.5714** | IRS |
| B | 0.7619 | 0.9333 | **0.8163** | IRS |
| C | 1 | 1 | **1** | CRS |
| D | 0.9143 | 1 | **0.9143** | DRS |

规模状态判定:解 NIRS 模型(见自测练习第 4 题思路)。A、B 位于最优规模点 C 的左侧(规模过小,扩张可提效)→ IRS;D 在 C 右侧(规模过大)→ DRS;C 处于规模报酬不变的最优规模(MPSS)。

**解析**:A 纯技术有效(在自己的规模上是好的)但规模太小、整体效率只有 0.5714——**扩张规模就能显著提效**;B 两头都有问题:规模偏小(SE = 0.8163)加上纯技术无效(PTE = 0.9333);D 则是纯规模问题,收缩或调整业务结构。效率分解让「为什么低效」有了可操作的答案,这是 DEA 区别于简单比值法的核心价值。

### 例题 2:双投入单产出(线性规划视角)

> 4 个同产出(1 单位)的工厂,投入向量:A(2, 4)、B(4, 2)、C(5, 5)、D(8, 3)。求各 DMU 的 CCR 效率。

以 C 为例写包络形式 LP:$\min \theta$ s.t.

$$2\lambda_A + 4\lambda_B + 5\lambda_C + 8\lambda_D \le 5\theta, \quad 4\lambda_A + 2\lambda_B + 5\lambda_C + 3\lambda_D \le 5\theta, \quad \lambda_A + \lambda_B + \lambda_C + \lambda_D \ge 1, \quad \lambda \ge 0$$

代入 $\lambda_A = \lambda_B = 0.5$、$\lambda_C = \lambda_D = 0$:投入合成 $(3, 3) \le (5\theta, 5\theta)$,产出合成 $1 \ge 1$ ✓,得 $\theta \le 0.6$。能否更小?若 $\theta < 0.6$,两约束相加得 $3(\lambda_A + \lambda_B) \le 5\theta - \dots$ 严格推导:两约束相加 $6\lambda_A + 6\lambda_B + 10\lambda_C + 11\lambda_D \le 10\theta$,而 $\lambda_A + \lambda_B + \lambda_C + \lambda_D \ge 1$ 给出 $6\lambda_A + 6\lambda_B + 10\lambda_C + 11\lambda_D \ge 6(\lambda_A + \lambda_B + \lambda_C + \lambda_D) \ge 6$,故 $10\theta \ge 6$,$\theta \ge 0.6$。因此 $\theta_C = 0.6$ ✓。

同理:D(8, 3) 被 B(4, 2) 直接支配(投入各分量都更小、产出相同),径向压缩 $D \to B$:$\theta_D = \dfrac{4}{8} = 0.5$?——注意第二分量:$2 \le 3\theta$ 要求 $\theta \ge 2/3$,故 $\theta_D = 2/3$。A、B 无法被任何组合支配,均为有效:$\theta_A = \theta_B = 1$。

**解析**:本例所有 DMU 产出相同,效率前沿是投入空间的凸包下边界(A—B 连线)。C 的目标投入 $(3,3) = 0.5A + 0.5B$ 恰好落在前沿上;D 的目标投入 $(16/3, 2)$ 在 B 的射线上。注意:**参考集(λ 非零的 DMU)本身就是管理标杆**——C 应该学习 A 与 B 的投入结构,这是 DEA 给出的可操作建议,论文中务必报告。

## ⚠️ 常见易错点

1. **投入/产出方向搞反**。把产出写成投入(或反之),效率含义完全颠倒;动手前先列表:哪些是「消耗」、哪些是「创造」
2. **忘加 BCC 凸性约束**。只用 CCR 会把规模无效全部归为技术无效,无法区分「管理差」与「规模不对」
3. **效率分解公式记反**。正确:TE = PTE × SE;SE 是 TE 除以 PTE,不是相乘顺序颠倒的版本
4. **用 CCR 判断规模报酬**。CRS 假设下谈规模报酬无意义;必须配合 BCC 与 NIRS 模型
5. **DMU 数量太少**。经验法则:DMU 数 $n \ge 2(m+s)$ 或 $3(m+s)$($m$、$s$ 为投入产出数);样本太少时前沿被个别点决定,效率普遍虚高、区分度差
6. **θ = 1 但松弛非零的「弱有效」**。径向模型只度量等比例压缩,θ = 1 不代表没有可改进的松弛;严谨做法是用 SBM 模型或报告松弛量
7. **指标共线或冗余**。两个高度相关的投入会被算成「双重负担」;先用相关性分析筛指标,总数再砍一刀

## ✏️ 自测练习

**第 1 题(判断)**:某 DMU 的 DEA 效率为 1,说明它经营完美、无需改进。对吗?

<details><summary>查看答案</summary>

**不对,至少两重问题。** ①DEA 评价的是**相对**效率,只与样本内其他 DMU 比较;换一批更强的对手,它的效率可能下降。②径向模型下 θ = 1 只保证「无法等比例压缩投入」,可能仍有松弛(某单项投入冗余),即「弱有效」;强有效要求 θ = 1 且全部松弛为 0。因此论文中「DEA 有效」应表述为「在样本内相对有效」。

</details>

**第 2 题(计算)**:4 个 DMU(单投入单产出):(1, 2)、(2, 3)、(3, 6)、(4, 7)。求各 DMU 的 TE、PTE、SE,并判断规模状态。

<details><summary>查看答案</summary>

$y/x = (2,\ 1.5,\ 2,\ 1.75)$,最大为 2(DMU1 与 DMU3 并列)。CCR:$TE = (1,\ 0.75,\ 1,\ 0.875)$。

VRS 前沿:DMU1(1,2)—DMU3(3,6) 斜率 2,DMU3—DMU4 斜率 1,凹包络成立;DMU2(2,3) 在前沿线 $y = 2x$ 下方($x=2$ 处前沿 $y = 4 > 3$),投入导向目标 $x^* = 3/2 = 1.5$,$PTE_2 = 0.75$;其余点在前沿上,PTE = 1。故:

$$PTE = (1,\ 0.75,\ 1,\ 1), \qquad SE = TE/PTE = (1,\ 1,\ 1,\ 0.875)$$

DMU2 低效**全部来自纯技术**(规模恰在有效段);DMU4 低效全部来自规模(其 $x = 4$ 越过最优规模点 $x = 3$,DRS,规模报酬递减)。

</details>

**第 3 题(概念)**:CCR 与 BCC 的根本区别是什么?什么情况下两者结果相同?

<details><summary>查看答案</summary>

根本区别:CCR 假设规模报酬不变(CRS),前沿是过原点的锥;BCC 允许可变规模报酬(VRS),前沿是样本的凸包络,更贴合实际。两者相同的条件:DMU 处于最优规模(SE = 1),或前沿在局部恰好与过原点的射线相切。实际建模中应**两个都跑**,用 TE 与 PTE 的差解读规模问题——只报 CCR 是常见错误。

</details>

**第 4 题(计算)**:例题 1 中如何用 NIRS 模型判断 A 是 IRS?写出 NIRS 约束并给出结论。

<details><summary>查看答案</summary>

NIRS 模型:$\min \theta$ s.t. $\sum \lambda_j y_j \ge y_A$,$\sum \lambda_j x_j \le \theta x_A$,$\sum \lambda_j \le 1$,$\lambda \ge 0$。

对 A(x=2, y=2):取 $\lambda_C = 2/7$(产出 $7 \times 2/7 = 2 \ge 2$ ✓;投入 $4 \times 2/7 = 8/7 \le 2\theta$ → $\theta \ge 4/7$;$\sum \lambda = 2/7 \le 1$ ✓)。$\theta \ge 4/7$ 且 $\theta = 4/7$ 可行,故 $\theta_{\text{NIRS}} = 4/7 = \theta_{\text{CCR}}$ → **IRS(规模报酬递增)**。直观理解:把 C 缩小 2/7 倍就能覆盖 A 的产出,说明 A 的规模太小、扩张后效率会上升。

</details>

## 🏆 竞赛实战链接

- **出镜频率**:DEA 是国赛/美赛「效率评价」题型的标准答案,典型场景:区域创新效率、银行/医院/高校绩效、城市绿色发展效率、碳减排效率;面板数据再配 Malmquist 指数做动态分解
- **论文加分点**:①报告 TE、PTE、SE 三张表 + 规模状态列;②给出**每个无效 DMU 的参考集与目标值**(谁是最佳标杆、投入该压缩到多少);③投入产出指标的选取依据(相关性检验、文献支撑);④超效率排序解决「一堆 DMU 都是 1」的排序问题
- **常见翻车点**:只报 CCR 不谈 BCC;把效率为 1 说成「绝对最优」;DMU 太少导致一半以上有效;投入产出方向混淆
- **工具**:Python + scipy.linprog 可解小规模问题;专业软件 DEAP 2.1、MaxDEA、DEA-Solver;论文注明所用求解器与模型形式(投入/产出导向)

## 💻 代码实现

```python
import numpy as np
from scipy.optimize import linprog

X = np.array([[2., 3., 4., 5.]])      # 1 种投入 × 4 个 DMU
Y = np.array([[2., 4., 7., 8.]])      # 1 种产出 × 4 个 DMU
m, n = X.shape

def dea(k, rts="crs"):
    """投入导向径向 DEA。rts: 'crs'=CCR, 'vrs'=BCC, 'nirs'=NIRS"""
    c = np.zeros(n + 1); c[0] = 1.0                    # min θ
    A_ub, b_ub = [], []
    for i in range(m):                                 # Xλ ≤ θ·x_k
        row = np.zeros(n + 1); row[0], row[1:] = -X[i, k], X[i, :]
        A_ub.append(row); b_ub.append(0.0)
    for r in range(Y.shape[0]):                        # Yλ ≥ y_k
        row = np.zeros(n + 1); row[1:] = -Y[r, :]
        A_ub.append(row); b_ub.append(-Y[r, k])
    if rts == "vrs":                                   # BCC: Σλ = 1
        A_ub.append([0] + [1.0] * n); b_ub.append(1.0)
        A_ub.append([0] + [-1.0] * n); b_ub.append(-1.0)
    elif rts == "nirs":                                # NIRS: Σλ ≤ 1
        A_ub.append([0] + [1.0] * n); b_ub.append(1.0)
    bounds = [(None, None)] + [(0, None)] * n
    res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")
    return res.fun

for rts in ["crs", "vrs", "nirs"]:
    print(rts.upper(), ":", np.round([dea(k, rts) for k in range(n)], 4))
# CRS : [0.5714 0.7619 1.     0.9143]
# VRS : [1.     0.9333 1.     1.    ]
# NIRS: [0.5714 0.7619 1.     1.    ]  → A、B 为 IRS;D 为 DRS
```

## 📚 延伸阅读

- **原始文献**:Charnes, A., Cooper, W. W., & Rhodes, E. (1978). Measuring the efficiency of decision making units. *European Journal of Operational Research*, 2(6): 429-444;Banker, R. D., Charnes, A., & Cooper, W. W. (1984). Some models for estimating technical and scale inefficiencies in data envelopment analysis. *Management Science*, 30(9): 1078-1092
- **教材**:成刚《数据包络分析方法与 MaxDEA 软件》;魏权龄《数据包络分析》
- **视频**:B 站搜索「DEA CCR BCC 教程」,选播放量高的课程配合软件实操
- **进阶关联**:参见《线性规划与单纯形法》单元(DEA 的求解内核)→ 参见《熵权法与客观赋权》单元(DEA 权重内生,与熵权法对比理解主客观路线)→ 参见《灰色关联分析》单元(效率影响因素的后续分析)

## 🧠 小结

1. DEA 不预设生产函数,从数据包络出效率前沿,评价 DMU 的**相对**效率;投入导向 θ 表示「投入可压缩到的比例」
2. 模型三件套:CCR(CRS)算 TE,BCC(VRS)算 PTE,两者之比为规模效率 SE;NIRS 模型判定 IRS/DRS
3. 分式规划 → Charnes-Cooper 线性化 → 包络形式是标准推导路径;包络形式的 λ 参考集即管理标杆
4. 效率分解让结论可操作:纯技术无效 → 改进管理;规模无效 → 调整规模方向
5. 实务注意:DMU 数量够多、指标精选、方向正确、报告参考集与目标值,论文才算完整
