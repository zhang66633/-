# scipy.optimize求解优化问题

> **难度**:进阶 · **预计学习时长**:50 分钟 · **主讲智能体**:🧩 求解器 · **方法类别**:编程工具

## 🎯 学习目标

学完本单元,你应该能够:

- 用 `linprog` 求解线性规划,并读懂最优解、目标值与对偶信息
- 用 `minimize` 求解无约束与带约束的非线性规划,会选方法与传约束
- 正确书写 `bounds` 与 `constraints`(特别注意不等式方向约定)
- 识别「多峰问题」,用 `differential_evolution` 做全局寻优
- 用 `least_squares` / `curve_fit` 处理最小二乘类建模问题

## 📖 核心概念

### 1. scipy.optimize 的问题地图

| 问题类型 | 函数 | 特点 |
|------|------|------|
| 线性规划(LP) | `linprog` | 全局最优,HiGHS 求解器 |
| 一元函数寻优 | `minimize_scalar` | 有界区间内求最值 |
| 无约束非线性 | `minimize`(Nelder-Mead/BFGS) | 局部最优,依赖初值 |
| 带约束非线性 | `minimize`(SLSQP/trust-constr) | 支持等式/不等式约束 |
| 非线性最小二乘 | `least_squares` / `curve_fit` | 拟合问题的正解 |
| 全局优化(多峰) | `differential_evolution` | 差分进化,慢但全局 |
| 方程求根 | `root` / `root_scalar` | 方程组数值解 |

> 💡 拿到优化问题先分类:线性?无约束光滑?带约束?多峰?——分类决定用哪个函数、会不会被局部最优坑到。

### 2. linprog:线性规划的行业默认

`linprog` 求解标准形式:

$$\min \ c^T x \quad \text{s.t.} \quad A_{ub}x \leq b_{ub},\ A_{eq}x = b_{eq},\ x \in [lb, ub]$$

理论细节(标准形式化归、对偶、影子价格)参见《线性规划与单纯形法》单元,这里只讲调用:

```python
from scipy.optimize import linprog

c = [-3, -5]  # min -3x1-5x2 ⇔ max 3x1+5x2
res = linprog(
    c,
    A_ub=[[1, 3], [2, 1]],
    b_ub=[9, 8],  # ≤ 约束
    bounds=[(0, None), (0, None)],  # x1,x2 ≥ 0
    method="highs",
)
print(res.x, -res.fun)  # [3. 2.] 19.0
```

- **`method="highs"`**:开源 HiGHS 求解器,精度高速度快,是 scipy 1.6+ 的默认项,竞赛直接用它
- **对偶信息**:`res.ineqlin.marginals`(不等式约束的影子价格)与 `res.eqlin.marginals`(等式约束的影子价格)可直接用于灵敏度分析的论文段落

### 3. minimize:方法与初值

`minimize(fun, x0, method=...)` 方法族:

- **Nelder-Mead**:不用梯度,函数不光滑/噪声大时用
- **BFGS/L-BFGS-B**:拟牛顿,光滑无约束问题的首选,快
- **SLSQP / trust-constr**:支持 `bounds` 与 `constraints`,建模竞赛最常用

**初值决定命运**:非线性规划的局部最优与初值强相关。技巧——多组初值启动,取最优;或先 `differential_evolution` 粗搜,再以粗搜结果作初值精修。

### 4. 约束的写法:方向约定要背下来

```python
from scipy.optimize import minimize

# 不等式约束:fun(x) >= 0 为可行!<= 要变号
# 想表达 x + y <= 10,就写 fun(x) = 10 - x - y
constraints = [
    {"type": "ineq", "fun": lambda x: 10 - x[0] - x[1]},  # x+y ≤ 10
    {"type": "eq", "fun": lambda x: x[0] ** 2 + x[1] - 5},  # x1²+x2 = 5
]
bounds = [(0, None), (0, None)]  # 每个变量都要给上下界
```

`bounds` 是所有变量的**逐变量**界;`constraints` 是「跨变量」的等式/不等式。SLSQP 要求 `bounds` 与 `constraints` 同时提供或同时省略。

### 5. 全局优化:differential_evolution

多峰函数上 `minimize` 只会爬到初值附近的山头。`differential_evolution`(差分进化)在**整个可行域内**撒种群并进化,不依赖初值:

```python
import numpy as np
from scipy.optimize import differential_evolution


def f(x):
    return -(x[0] * np.sin(10 * np.pi * x[0]) + 2)  # 求最大 → 取负求最小


res = differential_evolution(f, bounds=[(0, 4)], seed=0, tol=1e-6)
print(res.x, -res.fun)  # [3.8503] 5.8501
```

代价是调用目标函数数千次——适合「目标函数本身便宜」的中小规模问题。大规模组合问题用遗传算法自实现(见《遗传算法自实现》单元)或启发式库。

## 🧮 核心 API 速查

| 任务 | API | 关键参数 |
|------|-----|------|
| 线性规划 | `linprog(c, A_ub, b_ub, A_eq, b_eq, bounds)` | `method="highs"` |
| 无约束优化 | `minimize(fun, x0, method="BFGS")` | 光滑函数首选 |
| 带约束优化 | `minimize(fun, x0, method="SLSQP", bounds=, constraints=)` | 不等式方向 `fun≥0` |
| 一元寻优 | `minimize_scalar(fun, bounds=(a,b), method="bounded")` | 有界区间 |
| 全局优化 | `differential_evolution(func, bounds)` | 多峰问题 |
| 非线性最小二乘 | `least_squares(fun, x0)` | 残差向量形式 |
| 曲线拟合 | `curve_fit(f, x, y, p0=)` | 拟合参数 + 协方差 |
| 方程求根 | `root(fun, x0)` / `root_scalar(f, bracket=[a,b])` | 方程组 / 一元 |
| 结果检查 | `res.success` / `res.message` / `res.fun` / `res.x` | 每次求解必查 |

## 💡 经典例题

### 例题 1:生产计划(linprog 与手工单纯形对照)

> 某工厂生产 A、B 两种产品:每件 A 需 1 小时机加工、2 小时装配,利润 3 万元;每件 B 需 3 小时机加工、1 小时装配,利润 5 万元。每周机加工可用 9 小时,装配可用 8 小时。求利润最大的生产计划,并输出两种资源的影子价格。

**代码**:

```python
import numpy as np
from scipy.optimize import linprog

# max 3x1 + 5x2  ⇔  min -3x1 - 5x2
c = [-3, -5]
A_ub = [[1, 3], [2, 1]]  # 机加工、装配
b_ub = [9, 8]

res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=[(0, None), (0, None)], method="highs")

print("最优解:", res.x)
print("最大利润:", -res.fun)
# 影子价格:linprog 求 min,对偶变量为负;转回 max 问题取相反数
print("机加工影子价格:", -res.ineqlin.marginals[0], "(万元/小时)")
print("装配影子价格:", -res.ineqlin.marginals[1], "(万元/小时)")
print("求解状态:", res.message)
```

**输出解读**:

```
最优解: [3. 2.]
最大利润: 19.0
机加工影子价格: 1.4 (万元/小时)
装配影子价格: 0.8 (万元/小时)
求解状态: Optimization terminated successfully.
```

结果与《线性规划与单纯形法》单元手工迭代完全一致:$(x_1, x_2) = (3, 2)$,$z_{\max} = 19$。两条约束都取等号(资源用满),影子价格分别为 1.4 与 0.8 万元/小时——「多给 1 小时机加工,利润增加 1.4 万;多给 1 小时装配,增加 0.8 万」,机加工是更稀缺的瓶颈资源。这个结论直接写进灵敏度分析小节。两个细节:①`linprog` 只能求 **min**,最大化问题必须先给目标系数取负;②`linprog` 的对偶变量对应 min 问题(为负),转回 max 问题要取相反数。

### 例题 2:圆柱容器最小用料(非线性约束优化)

> 设计一个体积 $V = 1000$ cm³ 的圆柱形容器,半径 $r$ 与高 $h$ 均为正。求使表面积 $S = 2\pi r^2 + 2\pi r h$ 最小的 $r, h$,并与解析解对照。

**建模**:变量 $x = (r, h)$;等式约束 $\pi r^2 h = V$;解析解为 $r^* = (V / 2\pi)^{1/3}$,$h^* = 2r^*$(等径高圆柱)。

**代码**:

```python
import numpy as np
from scipy.optimize import minimize

V = 1000.0
S = lambda x: 2 * np.pi * x[0] ** 2 + 2 * np.pi * x[0] * x[1]

constraints = [{"type": "eq", "fun": lambda x: np.pi * x[0] ** 2 * x[1] - V}]
bounds = [(0.1, 50), (0.1, 100)]  # r、h 必须为正

res = minimize(S, x0=[5.0, 15.0], method="SLSQP", bounds=bounds, constraints=constraints)
r, h = res.x

r_exact = (V / (2 * np.pi)) ** (1 / 3)
h_exact = 2 * r_exact
print(f"数值解: r={r:.4f}, h={h:.4f}, S_min={res.fun:.3f}")
print(f"解析解: r={r_exact:.4f}, h={h_exact:.4f}, S_min={S([r_exact, h_exact]):.3f}")
print(f"约束残差 πr²h - V = {np.pi * r**2 * h - V:.2e}")
```

**输出解读**:

```
数值解: r=5.4193, h=10.8385, S_min=553.581
解析解: r=5.4193, h=10.8385, S_min=553.581
约束残差 πr²h - V = -1.05e-09
```

三个细节:①等式约束写作 `fun(x) = 0` 的形式($\pi r^2 h - V = 0$),残差 $10^{-11}$ 量级说明约束满足得很好;②数值解与解析解吻合到 4 位小数,「数值 + 解析互验」再次出场;③若 $r, h$ 的界忘写正数限制,SLSQP 可能给出负半径的荒谬解——**变量的物理界永远要显式传给 bounds**。

### 例题 3:多峰函数全局寻优(局部 vs 全局)

> 求 $f(x) = x\sin(10\pi x) + 2$ 在 $[0, 4]$ 上的最大值。先用 `minimize`(BFGS)从 $x_0 = 1.5$ 出发,再用 `differential_evolution` 全局搜索,对比两者结果。

**代码**:

```python
import numpy as np
from scipy.optimize import minimize, differential_evolution

f = lambda x: x * np.sin(10 * np.pi * x) + 2

# 局部:BFGS 从 x0=1.5 出发
local = minimize(lambda x: -f(x[0]), x0=[1.5], method="BFGS")
print(f"局部最优(BFGS, 初值1.5): x={local.x[0]:.3f}, f={-local.fun:.3f}")

# 全局:差分进化,整个 [0,4] 撒种群
global_ = differential_evolution(lambda x: -f(x[0]), bounds=[(0, 4)], seed=0)
print(f"全局最优(差分进化): x={global_.x[0]:.4f}, f={-global_.fun:.4f}")

# 画出全貌,验证「多峰」
import matplotlib.pyplot as plt

xs = np.linspace(0, 4, 2000)
fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(xs, f(xs), lw=1.5)
ax.scatter([local.x[0]], [-local.fun], s=60, c="tab:orange", label=f"局部 {local.x[0]:.2f}")
ax.scatter(
    [global_.x[0]], [-global_.fun], s=60, c="tab:red", marker="*", label=f"全局 {global_.x[0]:.2f}"
)
ax.set_xlabel("x")
ax.set_ylabel("f(x)")
ax.legend()
ax.grid(alpha=0.3)
fig.savefig("multimodal.png", dpi=200)
```

**输出解读**:

```
局部最优(BFGS, 初值1.5): x=0.452, f=2.451
全局最优(差分进化): x=3.8503, f=5.8501
```

同一道题,方法不同,最优值相差一倍以上。这就是**多峰问题的本质**:`minimize` 沿着梯度爬,停在它遇到的第一个山头(0.45,值 2.45)——比初值 1.5 处的函数值还差;而差分进化在 $[0,4]$ 全域搜索,找到了真正的最高峰(3.85,值 5.85)。注意 BFGS 的结果与**初值强相关**且不可预测:初值落在哪个峰的「引力范围」,梯度就把它带向哪个峰。竞赛中的参数辨识、非凸拟合都可能踩这个坑。应对口诀:**先画图判断单峰多峰 → 多峰就用全局方法 → 不确定就全局粗搜 + 局部精修**。

## ⚠️ 常见易错点

1. **最大化忘记取负**。`linprog`、`minimize`、`differential_evolution` 一律求 **min**;$\max f \iff \min -f$,最后结果再取负回来,论文里别把符号弄丢
2. **不等式约束方向反**。`{"type": "ineq", "fun": g}` 的可行条件是 **$g(x) \geq 0$**;要表达 $x + y \leq 10$ 必须写 `fun: 10 - x - y`,写反了可行域就完全错了
3. **没看 `res.success`**。求解器可能因为数值问题悄悄失败;每次求解后检查 `res.success` 与 `res.message`,失败时换初值/换方法/放宽精度
4. **把整数变量交给连续求解器**。`linprog`/`minimize` 只处理连续变量,整数问题需要分支定界(见《整数规划与分支定界》单元)或遗传算法(见《遗传算法自实现》单元),直接四舍五入通常不是最优甚至不可行
5. **非线性规划只跑一个初值**。多峰问题一个初值一个答案;多组初值(如网格采样)启动,取目标最优者,是论文里「解的稳健性」论述的素材
6. **`bounds` 缺漏变量**。`bounds` 的长度必须等于变量个数,且每个变量都要明确上下界;省略变量界常常得到负产量、负价格这类物理上荒谬的解

## ✏️ 自测练习(选择题)

**第 1 题**

```python
from scipy.optimize import linprog

res = linprog(
    [-3, -5], A_ub=[[1, 3], [2, 1]], b_ub=[9, 8], bounds=[(0, None), (0, None)], method="highs"
)
print(res.x, -res.fun)
```

输出是:

A. [3. 2.] 19.0
B. [0. 0.] 0.0
C. [3. 2.] -19.0
D. [2. 3.] 19.0

<details><summary>查看答案与解析</summary>
**答案:A**。`linprog` 只能求 **min**:max 3x₁+5x₂ 等价于 min -3x₁-5x₂,系数取负;求解后真实最优值 = `-res.fun` = 19.0,最优解 (3, 2)。[0. 0.] 0.0 是忘给目标取负(用 c=[3,5] 求 min,最优解跑到原点);[3. 2.] -19.0 是忘了把 res.fun 取负回 max 问题;[2. 3.] 19.0 违反约束 1×2+3×3=11>9,不可行——是把解分量记反。每次求解后还应检查 res.success 与 res.message。
</details>

**第 2 题** 用 SLSQP 求 $\min\ f(x,y) = x^2 + y^2$,约束 $x + y \geq 3$。以下约束写法**正确**的是:

A. {"type": "ineq", "fun": lambda v: 3 - v[0] - v[1]}
B. {"type": "ineq", "fun": lambda v: v[0] + v[1] - 3}
C. {"type": "ineq", "fun": lambda v: v[0] + v[1]}
D. bounds=[(0, 3), (0, 3)] 即可表达 x+y≥3,无需 constraints

<details><summary>查看答案与解析</summary>
**答案:B**。`ineq` 约束的可行条件是 **fun(x) ≥ 0**:要表达 x+y ≥ 3,直写 v[0]+v[1]-3。
正确写法解得 (1.5, 1.5),f=4.5。
第一个选项方向反了,可行域变成 x+y ≤ 3,求解器给出 (0,0)、f=0——约束完全失效;
第三个漏掉常数项 -3,约束变成 x+y ≥ 0,原约束没生效;
bounds 是**逐变量**的矩形界,[0,3]² 不能表达「x+y ≥ 3」这种跨变量约束(如 (0,0) 在界内却不满足原约束)。
</details>

**第 3 题** 求 $f(x) = x\sin(10\pi x) + 2$ 在 $[0, 4]$ 上的最大值。用 `minimize`(BFGS)从 $x_0 = 1.5$ 出发得到
$x \approx 0.452,\ f \approx 2.451$;用 `differential_evolution` 得到 $x \approx 3.8503,\ f \approx 5.8501$。
以下判断正确的是:

A. 两个结果都正确,取平均即可
B. differential_evolution 不基于梯度,结果必然不如 minimize 可靠
C. 函数多峰,minimize 陷入初值附近的局部最优;应先画图判断多峰,再改用全局方法(或全局粗搜 + 局部精修)
D. minimize 的结果是求解器 bug,增大 maxiter 重新求解即可

<details><summary>查看答案与解析</summary>
**答案:C**。f 在 [0,4] 上有约 40 个峰,`minimize` 类方法沿梯度爬到**初值附近的**山头就停:初值 1.5 落在 0.45 峰的引力范围内,得到的 2.45 甚至比初值处的函数值还差——这是多峰问题的本质,不是 bug。增大 maxiter 只会让局部收敛更精确,不会跳出局部极值;差分进化在可行域全域撒种群,多峰场景更可靠(代价是慢);两个结果「取平均」毫无意义。应对口诀:画图判断多峰 → 全局粗搜 + 局部精修,多组初值启动取最优。
</details>

## 🏆 竞赛实战链接

- **出镜频率**:规划类问题(生产、运输、选址、投资)是国赛 B 题的常客,scipy 负责「快速验证模型」;美赛的连续优化问题也常用它做基准解
- **论文加分点**:①数值解与解析/手工解对照(如例题 1 与单纯形表互验);②输出 `marginals` 做影子价格与灵敏度分析;③全局寻优问题给出「多组初值 + 全局方法」的双保险说明
- **工具链**:scipy 零安装、适合小中规模;变量成百上千或需要整数变量时,升级到 PuLP/Gurobi(学术版免费),或参见《cvxpy凸优化编程》单元

## 💻 代码实现

三类问题的完整求解骨架汇总:

```python
import numpy as np
from scipy.optimize import linprog, minimize, differential_evolution

# ---- 1. 线性规划:max 3x1+5x2, s.t. x1+3x2≤9, 2x1+x2≤8 ----
res_lp = linprog(
    [-3, -5], A_ub=[[1, 3], [2, 1]], b_ub=[9, 8], bounds=[(0, None)] * 2, method="highs"
)
assert res_lp.success
print("LP:", res_lp.x, "目标:", -res_lp.fun)

# ---- 2. 带约束非线性规划 ----
res_nlp = minimize(
    lambda x: 2 * np.pi * x[0] ** 2 + 2 * np.pi * x[0] * x[1],
    x0=[5.0, 15.0],
    method="SLSQP",
    bounds=[(0.1, 50), (0.1, 100)],
    constraints=[{"type": "eq", "fun": lambda x: np.pi * x[0] ** 2 * x[1] - 1000.0}],
)
assert res_nlp.success
print("NLP:", res_nlp.x.round(4), "目标:", round(res_nlp.fun, 3))

# ---- 3. 全局优化(多峰) ----
res_global = differential_evolution(
    lambda x: -(x[0] * np.sin(10 * np.pi * x[0]) + 2), bounds=[(0, 4)], seed=0
)
print("全局:", res_global.x.round(4), "目标:", round(-res_global.fun, 4))
```

## 📚 延伸阅读

- **官方文档**:scipy.optimize 教程(https://docs.scipy.org/doc/scipy/tutorial/optimize.html)— linprog、minimize、differential_evolution 三节必读
- **理论配套**:《线性规划与单纯形法》单元(linprog 背后的算法)→ 《凸优化与KKT条件》单元(约束最优性的理论)
- **工具升级**:《cvxpy凸优化编程》单元(声明式建模、锥规划);Gurobi 学术许可证官网申请,处理大规模 LP/MIP

## 🧠 小结

1. 先给问题分类:线性 → `linprog`;光滑无约束 → `minimize`+BFGS;带约束 → SLSQP/trust-constr;多峰 → `differential_evolution`
2. 两个「方向约定」要刻进肌肉记忆:优化函数都求 **min**;不等式约束写成 **$g(x) \geq 0$**
3. `bounds` 是变量界(必写、逐变量),`constraints` 是跨变量约束;物理界(非负、上限)永远显式声明
4. 非线性规划 = 初值游戏:多初值、先粗搜后精修、画图判断多峰,三招保平安
5. 每次求解必查 `res.success`;数值解用解析解或手工解互验后再进论文
