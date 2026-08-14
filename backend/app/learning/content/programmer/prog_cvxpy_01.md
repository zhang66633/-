# cvxpy凸优化编程

> **难度**:进阶 · **预计学习时长**:50 分钟 · **主讲智能体**:🧩 求解器 · **方法类别**:编程工具

## 🎯 学习目标

学完本单元,你应该能够:

- 理解「声明式建模」:用 cvxpy 把优化问题**照抄**成代码,而不是自己写算法
- 写出 LP、QP、SOCP 与混合整数问题的 cvxpy 模型
- 理解 DCP(规范化凸编程)规则,能自己诊断并修复 `DCPError`
- 掌握 `prob.status` / `prob.value` / `var.value` 的取值时机
- 根据问题类型选择求解器(ECOS/CLARABEL/OSQP/HiGHS/商业求解器)

## 📖 核心概念

### 1. 声明式建模 vs 命令式求解

`scipy.optimize` 是**命令式**:你要把问题手工整理成矩阵/函数形式再喂给求解器。cvxpy 是**声明式**:直接用数学表达式描述目标与约束,由 cvxpy 自动转成标准形式并选择求解器。以「最小化 $\|Ax - b\|_2$」为例:

```python
import cvxpy as cp
import numpy as np

A = np.random.default_rng(0).normal(size=(10, 4))
b = np.random.default_rng(1).normal(size=10)

x = cp.Variable(4)
prob = cp.Problem(cp.Minimize(cp.norm2(A @ x - b)))
prob.solve()
print("最优解:", x.value.round(4))
print("最优值:", prob.value)
```

**一个模型,两种读法**:数学上写什么,代码里就写什么——这种「模型即论文」的对应关系,让 cvxpy 代码可以直接粘贴进论文附录。

### 2. 基本构件

| 构件 | 语法 | 说明 |
|------|------|------|
| 变量 | `cp.Variable(n)` / `(n, m)` | 可加 `nonneg=True`、`integer=True`、`boolean=True` |
| 目标 | `cp.Minimize(expr)` / `cp.Maximize(expr)` | 目标必须是凸/凹表达式 |
| 约束 | `[expr <= expr, expr == expr]` | 等式的两边曲率必须匹配 |
| 求解 | `prob.solve(solver=...)` | 返回最优值;`prob.status` 看状态 |
| 取值 | `prob.value` / `x.value` | **solve() 之后**才有意义 |

### 3. DCP 规则:cvxpy 的「语法检查」

cvxpy 的每个表达式都带有**曲率标签**:constant / affine / convex / concave / unknown。规则:

- `Minimize` 的目标必须是 **convex**,`Maximize` 的目标必须是 **concave**
- 等式约束两边必须是 **affine** 或「convex == concave」这类可化为凸的形式
- 不等式 `<=` 左边须 convex、右边须 concave;`>=` 反之
- 保凸运算的原子函数:`sum_squares`、`norm1`、`norm2`、`quad_form(x, P)`($P \succeq 0$)、`log_sum_exp`、`max` 等

违反规则会抛出 `DCPError`——这是**好事**:它在建模阶段就拦住了「数学上就不是凸问题」的错误。常见修复手段:换原子函数、拆约束、或承认问题非凸改用其他方法(见《scipy.optimize求解优化问题》单元)。

### 4. 支持的问题族

| 问题族 | 典型原子函数 | 默认求解器 |
|------|------|------|
| LP | `cp.sum`、`@`、`<=` | CLARABEL / HiGHS |
| QP | `cp.quad_form`、`sum_squares` | OSQP / CLARABEL |
| SOCP | `cp.norm2`、`cp.quad_over_lin` | ECOS / CLARABEL |
| SDP | `cp.trace`、半定约束 `expr >> 0` | SCS / MOSEK |
| MIP | `integer=True` / `boolean=True` | HiGHS(SCIPY 接口)/ CBC / Gurobi |

> `prob.solve(solver=cp.GUROBI)` 这类写法可显式指定;装了 Gurobi/MOSEK 学术版后,大规模问题性能与 scipy 完全不在一个量级。

## 🧮 核心 API 速查

| 任务 | API | 说明 |
|------|-----|------|
| 创建变量 | `cp.Variable(n, nonneg=True)` | 整数/布尔用 `integer` / `boolean` |
| 线性目标 | `cp.Minimize(c @ x)` | `@` 是表达式矩阵乘 |
| 平方和 | `cp.sum_squares(A @ x - b)` | 最小二乘的凸写法 |
| 二次型 | `cp.quad_form(x, P)` | 要求 $P$ 半正定 |
| L1 范数 | `cp.norm1(x)` | 稀疏正则化/压缩感知 |
| L2 范数 | `cp.norm2(x)` | SOCP |
| 逐元素乘 | `cp.multiply(a, x)` | 不要用 `*`(那是标量/矩阵乘) |
| 分段函数 | `cp.pos(x)` / `cp.maximum(a, b)` / `cp.max(x)` | 保凸 |
| 逻辑变量 | `cp.Variable(n, boolean=True)` | 选址、指派 |
| 求解与取值 | `prob.solve()` → `prob.status / prob.value / x.value` | solve 后取值 |
| 敏感性 | `prob.constraints[i].dual_value` | 对偶变量 = 影子价格 |

## 💡 经典例题

### 例题 1:投资组合优化(QP)

> 4 种资产的期望收益 $\mu$ 与协方差矩阵 $\Sigma$ 已知。求满足「全额投资、不得做空、期望收益不低于 11%」的最小风险组合:

$$\min_x \ x^T\Sigma x \quad \text{s.t.} \quad \mathbf{1}^Tx = 1,\ x \geq 0,\ \mu^Tx \geq 0.11$$

**代码**:

```python
import numpy as np
import cvxpy as cp

mu = np.array([0.12, 0.10, 0.15, 0.08])
Sigma = np.array([[0.10, 0.02, 0.01, 0.00],
                  [0.02, 0.08, 0.01, 0.01],
                  [0.01, 0.01, 0.20, 0.02],
                  [0.00, 0.01, 0.02, 0.05]])

x = cp.Variable(4)
risk = cp.quad_form(x, Sigma)
constraints = [cp.sum(x) == 1, x >= 0, mu @ x >= 0.11]
prob = cp.Problem(cp.Minimize(risk), constraints)
prob.solve()

print("状态:", prob.status)
print("最优权重:", x.value.round(4))
print("组合风险(方差):", risk.value.round(4))
print("组合期望收益:", (mu @ x).value.round(4))
print("收益约束的对偶值:", float(constraints[2].dual_value))
```

**输出解读**:

```
状态: optimal
最优权重: [0.3045 0.2207 0.1915 0.2833]
组合风险(方差): 0.0326
组合期望收益: 0.1100
收益约束的对偶值: 0.8291
```

数学公式与代码逐行对应——这就是声明式建模的价值。两个解读要点:①期望收益恰等于下限 0.1100,说明收益约束是**紧的**,其**对偶值 0.8291 即影子价格**:每把收益要求放松 1 个百分点(0.01),风险约可降 $0.8291 \times 0.01 \approx 0.0083$;②「风险最小化 + 收益下限」的对偶关系,正是均值-方差前沿上取点的标准做法,把收益下限扫一遍(循环 `r_min`)就能画出**有效前沿**曲线,是投资类赛题的标配图。

### 例题 2:稀疏信号恢复(压缩感知,L1 优化)

> 未知向量 $x_0 \in \mathbb{R}^{60}$ 只有 3 个非零元(稀疏),只能观测到 $b = Ax_0$(30 次线性测量)。方程组 $Ax = b$ 欠定,有无穷多解;利用稀疏先验,解 $\ell_1$ 最小化问题:

$$\min_x \ \|x\|_1 \quad \text{s.t.} \quad Ax = b$$

**代码**:

```python
import numpy as np
import cvxpy as cp

rng = np.random.default_rng(1)
m, n = 30, 60
A = rng.normal(size=(m, n))
x_true = np.zeros(n)
x_true[[3, 17, 42]] = [1.5, -2.0, 1.0]      # 稀疏真值:3 个非零元
b = A @ x_true

x = cp.Variable(n)
prob = cp.Problem(cp.Minimize(cp.norm1(x)), [A @ x == b])
prob.solve()

recovered = np.where(np.abs(x.value) > 1e-6)[0]
print("状态:", prob.status)
print("恢复出的非零元下标:", recovered)
print("真值非零元下标:    ", [3, 17, 42])
print("最大分量误差:", float(np.max(np.abs(x.value - x_true))))
```

**输出解读**:

```
状态: optimal
恢复出的非零元下标: [ 3 17 42]
真值非零元下标:     [3, 17, 42]
最大分量误差: 2.2e-09
```

60 维向量只用 30 次测量**精确恢复**——这是压缩感知的核心结论:$\ell_1$ 最小化在欠定条件下自动挑出稀疏解。$\ell_1$ 是 $\ell_0$(非零元个数)的**最紧凸松弛**,这正是「非凸问题凸化」的经典范例,也是国赛/美赛信号处理、特征选择类题目的高级素材。注意:普通最小二乘(求 $\min \|x\|_2$)做不到这一点,解出的会是密密麻麻的非零分量——你可以亲手对比验证。

### 例题 3:带固定成本的仓库选址(混合整数规划)

> 4 个候选仓库、5 个客户。开仓需付固定成本 $f_i$,从仓库 $i$ 到客户 $j$ 的单位运输成本为 $c_{ij}$,客户需求 $d_j$。决定开哪些仓库、运多少货,使总成本最小:

$$\min_{y, x} \ \sum_i f_i y_i + \sum_{i,j} c_{ij} x_{ij} \quad \text{s.t.} \quad \sum_i x_{ij} = d_j,\ \sum_j x_{ij} \leq M y_i,\ y_i \in \{0, 1\}$$

**代码**:

```python
import numpy as np
import cvxpy as cp

rng = np.random.default_rng(3)
n_w, n_c = 4, 5
f = np.array([100.0, 120.0, 90.0, 110.0])         # 开仓固定成本
c = rng.integers(5, 30, size=(n_w, n_c)).astype(float)  # 运输单价
demand = np.array([8.0, 12.0, 10.0, 9.0, 11.0])   # 客户需求
M = demand.sum()                                   # 大 M 上限

y = cp.Variable(n_w, boolean=True)                 # 是否开仓
x = cp.Variable((n_w, n_c), nonneg=True)           # 运输量
total = f @ y + cp.sum(cp.multiply(c, x))
constraints = [
    cp.sum(x, axis=0) == demand,                   # 每个客户需求满足
    cp.sum(x, axis=1) <= M * y,                    # 不开仓则运输量为 0
]
prob = cp.Problem(cp.Minimize(total), constraints)
prob.solve(solver=cp.SCIPY)   # 通过 scipy 的 HiGHS 求解 MIP;也可用 CBC/Gurobi

print("状态:", prob.status)
print("开仓方案(1=开):", y.value.astype(int))
print("总成本:", round(prob.value, 2))
```

**输出解读**:

```
状态: optimal
开仓方案(1=开): [1 0 0 1]
总成本: 570.0
```

两个建模要点:①`boolean=True` 直接声明 0-1 变量,`M * y` 把「固定成本 + 线性运输」耦合进一个模型——$M$ 取需求总和即可(能覆盖任意分配),取太大会拖慢求解;②**混合整数规划是 NP-hard**,规模大时求解时间可能暴涨,此时可考虑:收紧 $M$、加有效不等式、或用启发式(见《遗传算法自实现》单元)。连续松弛解(把 `boolean` 去掉)可作为下界,用于论文里论证整数解的间隙(gap)。

## ⚠️ 常见易错点

1. **`DCPError` 一出现就慌**。它几乎总是意味着模型**数学上不凸**或写法违规(如 `Maximize(sum_squares)`);先自查曲率:目标方向对不对、等号两边是否 affine、是否误用 `*` 做逐元素乘
2. **`*` 与 `cp.multiply` 混淆**。cvxpy 表达式之间的 `*` 是标量乘/矩阵乘;逐元素乘必须 `cp.multiply(c, x)`;两个变量相乘会直接变成非凸表达式报错
3. **solve() 之前取 `x.value`**。`prob.solve()` 之前所有 `.value` 都是 None;先 solve,再检查 `prob.status == "optimal"`,最后取值的顺序不能乱
4. **忽略 `prob.status`**。求解可能以 `infeasible`(约束矛盾)或 `unbounded`(目标无界)结束;此时 `prob.value` 是 ±∞,直接拿去做后续计算会静默出错
5. **MIP 忘了装求解器**。默认求解器不支持整数变量,报 `SolverError`;解决方案:指定 `solver=cp.SCIPY`(走 scipy 的 HiGHS)或安装 CBC(`pip install cylp`)/Gurobi 学术版
6. **`quad_form` 的矩阵非半正定**。$\Sigma$ 必须是半正定的;实际协方差矩阵因样本误差可能带微小负特征值,先用 `(Sigma + Sigma.T)/2` 对称化并投影到 PSD(如特征值截断),否则求解失败

## ✏️ 自测练习(选择题)

**第 1 题** 以下哪个模型是**非 DCP** 的(`prob.is_dcp()` 为 False,`solve()` 时抛 `DCPError`)?

A. cp.Problem(cp.Minimize(cp.sum_squares(x)))
B. cp.Problem(cp.Maximize(cp.sum_squares(x)))
C. cp.Problem(cp.Minimize(cp.norm2(A @ x - b)))
D. cp.Problem(cp.Minimize(c @ x), [x >= 0])

<details><summary>查看答案与解析</summary>
**答案:B**。DCP 规则:`Minimize` 的目标必须是**凸**的,`Maximize` 的目标必须是**凹**的。`sum_squares` 是凸表达式,放在 Maximize 下违反规则 → is_dcp() 为 False,solve() 抛 DCPError。其余三个都是合法模型:sum_squares 与 norm2 的 Minimize 是凸问题,c@x 是仿射(既凸又凹)。DCPError 是好事——它在建模阶段就拦住「数学上就不是凸问题」的错误;报错先怀疑模型本身。
</details>

**第 2 题**

```python
import cvxpy as cp
import numpy as np
x = cp.Variable(2)
prob = cp.Problem(cp.Minimize(cp.sum_squares(x - np.array([1.0, 2.0]))))
print(x.value)      # ①
prob.solve()
print(x.value)      # ②
```

两处输出分别是:

A. ① None,② 约 [1. 2.]
B. ① 约 [0. 0.],② 约 [1. 2.]
C. ① 报 AttributeError,② 约 [1. 2.]
D. ① None,② 仍是 None

<details><summary>查看答案与解析</summary>
**答案:A**。`solve()` 之前变量尚未被赋值,`x.value` 是 None(不是 0,也不是报错);solve() 之后才能取到最优解——本题 min ‖x-(1,2)‖² 的最优解显然就是 [1, 2]。取值顺序不能乱:先 solve → 查 `prob.status == "optimal"` → 再取 value。若 status 是 infeasible/unbounded,此时 value 是 ±∞ 或 None,直接拿去做后续计算会静默出错。
</details>

**第 3 题** `c` 是单位运输成本矩阵(np.ndarray),`x = cp.Variable((2, 2))` 是运输量矩阵,
目标函数 $\sum_{i,j} c_{ij} x_{ij}$ 的正确写法是:

A. cp.sum(c @ x)
B. cp.sum(c * x)
C. cp.sum(cp.multiply(c, x))
D. cp.sum(x) * c

<details><summary>查看答案与解析</summary>
**答案:C**。逐元素乘必须用 `cp.multiply`:成本矩阵与变量矩阵逐元素相乘再求和,才是总运输成本。`@` 是矩阵乘:`c @ x` 算出的是另一个矩阵,求和后语义完全不对(实跑:c=[[1,2],[3,4]]、x 全 1 时,cp.sum(cp.multiply(c, x)) = 10 而 cp.sum(c @ x) = 20);`*` 在 cvxpy 中同样按矩阵乘法处理(该用法已弃用并发出警告),不是逐元素乘;最后一项先求和再乘矩阵,维度与语义都不对。
</details>

## 🏆 竞赛实战链接

- **出镜频率**:投资组合(美赛常客)、物流选址、指派问题、稀疏恢复与图像去噪,凡是能写成凸形式的模型,用 cvxpy 都显著降低编码出错率
- **论文加分点**:①把 cvxpy 模型代码与数学模型**并列**放进论文,评审一眼看懂「模型 = 代码」;②输出对偶变量做影子价格/敏感性分析(见《scipy.optimize求解优化问题》单元例题 1 的同类做法);③说明所选求解器与 `prob.status`,体现工程严谨
- **工具**:Gurobi/MOSEK 学术版免费申请,竞赛期间用它们求解大规模 LP/MIP/SDP,速度远超开源默认求解器

## 💻 代码实现

本单元三类模型的骨架汇总(可直接改造):

```python
import numpy as np
import cvxpy as cp

# ---- QP:投资组合最小风险 ----
n = 4
mu = np.array([0.12, 0.10, 0.15, 0.08])
Sigma = np.diag([0.10, 0.08, 0.20, 0.05])
x = cp.Variable(n)
prob_qp = cp.Problem(cp.Minimize(cp.quad_form(x, Sigma)),
                     [cp.sum(x) == 1, x >= 0, mu @ x >= 0.11])
prob_qp.solve()
print("QP 最优权重:", x.value.round(4))

# ---- LP:最小化成本,多面体约束 ----
c = np.array([3.0, 1.0, 2.0])
y = cp.Variable(3, nonneg=True)
prob_lp = cp.Problem(cp.Minimize(c @ y),
                     [cp.sum(y) == 1, y <= 1])
prob_lp.solve()
print("LP 最优解:", y.value.round(4))

# ---- MIP:0-1 选址(需支持整数规划的求解器) ----
f = np.array([100.0, 90.0, 110.0])
z = cp.Variable(3, boolean=True)
prob_mip = cp.Problem(cp.Minimize(f @ z), [cp.sum(z) >= 2])
prob_mip.solve(solver=cp.SCIPY)   # 或 cp.CBC / cp.GUROBI
print("MIP 开仓方案:", z.value.astype(int), "成本:", prob_mip.value)
```

## 📚 延伸阅读

- **官方文档**:cvxpy 教程(https://www.cvxpy.org/tutorial/index.html)— DCP 规则一节是精华
- **理论配套**:本单元与《凸优化与KKT条件》单元互为正反面:一个讲「怎么写模型」,一个讲「为什么这样写是最优的」
- **姊妹单元**:《scipy.optimize求解优化问题》(非凸问题的工具);《线性规划与单纯形法》(LP 理论与对偶)

## 🧠 小结

1. cvxpy 是声明式建模语言:数学公式怎么写,代码就怎么写,「模型即论文」
2. DCP 规则是自动的数学检查:Minimize 配凸目标、Maximize 配凹目标、等式两边 affine;报错先怀疑模型本身
3. 问题族与原子函数对应:LP(`sum`)、QP(`quad_form`)、SOCP(`norm2`)、SDP(`>> 0`)、MIP(`boolean`)
4. 取值顺序:solve → 查 `status` → 取 `value`;对偶值 `.dual_value` 是免费送的影子价格
5. 分工:凸问题交给 cvxpy(清晰、不易错),非凸问题回到 scipy 的全局优化——两把工具都要在工具箱里
