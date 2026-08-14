# 遗传算法自实现

> **难度**:进阶 · **预计学习时长**:60 分钟 · **主讲智能体**:🧩 求解器 · **方法类别**:编程工具

## 🎯 学习目标

学完本单元,你应该能够:

- 说出遗传算法(GA)的五大组件:编码、适应度、选择、交叉、变异
- 从零实现一个可运行的二进制编码 GA,并理解每一行代码的作用
- 掌握实数编码 + 罚函数处理约束问题,以及排列编码求解 TSP
- 理解精英保留、轮盘赌/锦标赛选择、交叉率与变异率的作用
- 用收敛曲线判断算法是否早熟,并写出论文级的 GA 实验报告

## 📖 核心概念

### 1. GA 的框架:五步循环

遗传算法模拟自然选择:把候选解编码为「染色体」,用适应度模拟「生存能力」,通过选择、交叉、变异逐代进化。伪代码:

```python
def genetic_algorithm(pop_size, generations):
    pop = init_population(pop_size)        # ① 随机初始种群
    for gen in range(generations):
        fitness = evaluate(pop)            # ② 计算适应度
        parents = select(pop, fitness)     # ③ 选择:适者多繁殖
        offspring = crossover(parents)     # ④ 交叉:交换基因片段
        offspring = mutate(offspring)      # ⑤ 变异:随机扰动
        pop = offspring                    #    换代(通常保留精英)
    return best(pop)
```

与经典优化方法的关键区别:**GA 不依赖梯度、不需要凸性**,靠种群并行搜索 + 随机算子跳出局部最优。代价是无法保证全局最优,且每次运行结果随机——竞赛论文中必须报告「多次运行的均值与最优值」。

### 2. 编码设计:解的「基因型」

| 编码 | 染色体形式 | 适用问题 |
|------|-----------|---------|
| **二进制** | 0/1 串 | 连续变量离散化、0-1 决策 |
| **实数** | 浮点向量 | 连续优化(可直接交叉变异) |
| **排列** | 城市/任务的顺序 | TSP、调度、排序类 |

二进制解码公式(把 $L$ 位 0/1 串映射到 $[lb, ub]$):

$$x = lb + \frac{ub - lb}{2^L - 1} \sum_{k=0}^{L-1} b_k \cdot 2^{L-1-k}$$

### 3. 选择算子:让好基因多繁殖

- **轮盘赌**:个体 $i$ 被选中的概率与其适应度成正比,

$$p_i = \frac{f_i}{\sum_{j=1}^{N} f_j}$$

- **锦标赛**:随机抽 $k$ 个个体,取其中最优者(共抽 $N$ 次)。不依赖适应度绝对大小,只依赖排序——**适应度为负也能用**,是工程上更稳的选择

### 4. 交叉与变异:探索与开发的分工

- **交叉**(开发):父母基因重组,子代继承双方片段——二进制用单点/两点交叉,实数用算术交叉 $\alpha p_1 + (1-\alpha) p_2$,排列用 PMX/OX(必须保证子代仍是合法排列)
- **变异**(探索):小概率随机扰动——二进制位翻转、实数高斯噪声、排列交换两个位置;变异率过小易早熟,过大退化成随机搜索
- 经验参数:交叉率 $p_c \in [0.7, 0.9]$,二进制变异率 $p_m \in [0.001, 0.05]$;**精英保留**(每代把历史最优个体原样复制进下一代)几乎必加

### 5. 约束处理:罚函数法

把约束违反量加权塞进目标,统一成无约束问题:

$$F(x) = f(x) + \lambda \sum_i \max(0,\ g_i(x))^2$$

- $g_i(x) \leq 0$ 是约束(先统一成 ≤ 形式),$\lambda$ 是罚系数
- $\lambda$ 太小 → 不可行解混入最优;太大 → 搜索被罚项主导,难收敛到边界上的最优解(约束取等时最优解常恰在边界)

## 🧮 公式与结论

| 组件 | 公式 / 规则 | 说明 |
|------|------|------|
| 二进制解码 | $x = lb + (ub-lb)\cdot D/(2^L-1)$ | $D$ 为位串的十进制值 |
| 轮盘赌概率 | $p_i = f_i / \sum_j f_j$ | 要求 $f_i \geq 0$ |
| 锦标赛 | 随机 $k$ 取最优,$k=2\sim 5$ | 只依赖排序,适应度可负 |
| 算术交叉 | $c = \alpha p_1 + (1-\alpha)p_2$ | 实数编码专用 |
| 罚函数 | $F = f + \lambda\sum\max(0, g_i)^2$ | 约束转无约束 |
| min → max 变换 | $f' = -f$ 或 $f' = 1/(1+f)$ | GA 惯例按「适应度越大越好」设计 |
| 参数经验值 | $p_c \in [0.7,0.9]$,$p_m \in [0.001,0.05]$ | 二进制;实数变异率更高 |

## 💡 经典例题

### 例题 1:二进制 GA 求多峰函数最大值(完整实现)

> 求 $f(x) = x\sin(10\pi x) + 2$ 在 $[0, 4]$ 上的最大值。该函数多峰,传统方法依赖初值(见《scipy.optimize求解优化问题》单元例题 3),请从零实现二进制编码 GA,并与 scipy 的差分进化结果对照。

**代码**:

```python
import numpy as np
from scipy.optimize import differential_evolution

def objective(x):
    return x * np.sin(10 * np.pi * x) + 2

POP, GEN, L = 60, 80, 22          # 种群、代数、染色体位数
LB, UB = 0.0, 4.0
PC, PM = 0.85, 0.01               # 交叉率、变异率

def decode(pop):
    powers = 2 ** np.arange(L - 1, -1, -1)
    return LB + (UB - LB) * (pop @ powers) / (2**L - 1)

def run_ga(seed=0):
    rng = np.random.default_rng(seed)
    pop = rng.integers(0, 2, size=(POP, L))
    history = []
    for _ in range(GEN):
        x = decode(pop)
        raw = objective(x)
        fit = raw - raw.min() + 1e-9          # 平移到非负:轮盘赌要求 f≥0
        history.append(float(raw.max()))
        elite = pop[int(fit.argmax())].copy()    # 精英保留
        # 轮盘赌选择
        p = fit / fit.sum()
        parents = pop[rng.choice(POP, size=POP, p=p)]
        # 单点交叉(相邻配对)
        pairs = parents.reshape(POP // 2, 2, L)
        for i in range(pairs.shape[0]):
            if rng.random() < PC:
                k = int(rng.integers(1, L))
                pairs[i, 0, k:], pairs[i, 1, k:] = (
                    pairs[i, 1, k:].copy(), pairs[i, 0, k:].copy())
        pop = pairs.reshape(POP, L)
        # 变异:按位翻转
        pop ^= (rng.random((POP, L)) < PM)
        pop[0] = elite                             # 精英顶掉第一个
    x = decode(pop)
    best = x[np.argmax(objective(x))]
    return best, history

best_x, history = run_ga(seed=0)
print(f"GA 最优解: x={best_x:.4f}, f={objective(best_x):.4f}")

ref = differential_evolution(lambda x: -objective(x[0]),
                             bounds=[(0, 4)], seed=0)
print(f"差分进化: x={ref.x[0]:.4f}, f={-ref.fun:.4f}")

# 收敛曲线
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(history, lw=2)
ax.set_xlabel("代数"); ax.set_ylabel("当前最优值")
ax.set_title("GA 收敛曲线")
ax.grid(alpha=0.3)
fig.savefig("ga_convergence.png", dpi=200)
```

**输出解读**:

```
GA 最优解: x=3.8502, f=5.8501
差分进化: x=3.8503, f=5.8501
```

自实现的 GA 与 scipy 差分进化收敛到同一个全局最优($x \approx 3.85$,$f \approx 5.85$),**互验成立**。逐行要点:①解码用向量化 `pop @ powers`,一次解出整个种群;②轮盘赌 `rng.choice(p=...)` 按适应度占比抽样;③`pop ^= mask` 是 NumPy 的位翻转技巧;④`pop[0] = elite` 一行完成精英保留——没有它,最优解可能被交叉变异毁掉,收敛曲线会剧烈震荡。

### 例题 2:实数编码 + 罚函数处理约束

> 求 $\min (x-2)^2 + (y-3)^2$,约束 $x + y \leq 4$,$x, y \in [0, 5]$。用实数编码 GA + 罚函数求解,并与 SLSQP 对照。

**代码**:

```python
import numpy as np
from scipy.optimize import minimize

rng = np.random.default_rng(1)
POP, GEN = 60, 100
LB = np.array([0.0, 0.0]); UB = np.array([5.0, 5.0])
LAMBDA = 100.0                       # 罚系数

def f(v):
    return (v[0] - 2) ** 2 + (v[1] - 3) ** 2

def fitness(v):                      # 罚函数:越大越好
    pen = max(0.0, v[0] + v[1] - 4.0)
    return -(f(v) + LAMBDA * pen ** 2)

pop = rng.uniform(LB, UB, size=(POP, 2))
history = []
for _ in range(GEN):
    fit = np.array([fitness(v) for v in pop])
    history.append(float(-fit.max()))
    elite = pop[int(fit.argmax())].copy()
    # 锦标赛选择(k=3)
    parents = np.empty_like(pop)
    for i in range(POP):
        cand = rng.integers(0, POP, 3)
        parents[i] = pop[cand[np.argmax(fit[cand])]]
    # 算术交叉(相邻配对)
    for i in range(0, POP, 2):
        if rng.random() < 0.8:
            a = rng.random()
            p1, p2 = parents[i].copy(), parents[i + 1].copy()
            parents[i] = a * p1 + (1 - a) * p2
            parents[i + 1] = (1 - a) * p1 + a * p2
    # 高斯变异 + 边界裁剪
    mask = rng.random(POP) < 0.15
    parents += np.where(mask[:, None], rng.normal(0, 0.1, (POP, 2)), 0.0)
    pop = np.clip(parents, LB, UB)
    pop[0] = elite

best = pop[np.argmax([fitness(v) for v in pop])]
print(f"GA 最优解: ({best[0]:.4f}, {best[1]:.4f}), "
      f"f={f(best):.4f}, 约束余量 x+y-4 = {best[0]+best[1]-4:.4f}")

res = minimize(f, x0=[0.0, 0.0], method="SLSQP",
               bounds=[(0, 5), (0, 5)],
               constraints=[{"type": "ineq", "fun": lambda v: 4 - v[0] - v[1]}])
print(f"SLSQP 参考: ({res.x[0]:.4f}, {res.x[1]:.4f}), f={res.fun:.4f}")
print(f"解析解: (1.5, 2.5), f=0.5")
```

**输出解读**:

```
GA 最优解: (1.4998, 2.5050), f=0.4952, 约束余量 x+y-4 = 0.0048
SLSQP 参考: (1.5000, 2.5000), f=0.5000
解析解: (1.5, 2.5), f=0.5
```

三方结论一致,但注意 GA 的解**略微越界**(约束余量 +0.0048)——罚函数法是软约束,允许用轻微违反约束换取更低的目标值($0.4952 < 0.5$),这正是罚函数法与 SLSQP(严格可行)的本质区别,论文里用 GA 解约束问题时必须报告约束违反量。两个设计要点:①**锦标赛选择**取代轮盘赌——因为加了罚函数后适应度可能是很大的负数,轮盘赌要求非负;②罚系数 $\lambda=100$ 把越界压到 $10^{-3}$ 量级;把 `LAMBDA` 改成 1,GA 会给出明显违反约束的解;改成 10000,则收敛变慢且更贴近可行域——罚系数的敏感性实验本身就是论文素材。

### 例题 3:排列编码求解 TSP(与暴力枚举对照)

> 8 个城市随机分布,求最短哈密顿回路(TSP)。用排列编码 + 顺序交叉(OX)+ 交换变异实现 GA,并与 8! 全枚举的精确最优值对照。

**代码**:

```python
import numpy as np
from itertools import permutations

rng = np.random.default_rng(2)
N = 8
coords = rng.uniform(0, 100, size=(N, 2))
D = np.linalg.norm(coords[:, None, :] - coords[None, :, :], axis=2)

def route_len(route):
    return float(D[route, np.roll(route, -1)].sum())

# 暴力枚举(8! = 40320)得到精确最优(向量化计算全部回路长度)
perms = np.array(list(permutations(range(N))))
exact = min(D[perms[:, :-1], perms[:, 1:]].sum(axis=1)
            + D[perms[:, -1], perms[:, 0]])
print(f"精确最优: {exact:.2f}")

POP, GEN = 100, 300

def ox_cross(p1, p2):
    a, b = sorted(rng.choice(N, 2, replace=False))
    c1, c2 = np.full(N, -1), np.full(N, -1)
    c1[a:b], c2[a:b] = p1[a:b], p2[a:b]              # 拷贝父母片段
    fill1 = [g for g in p2 if g not in p1[a:b]]      # 按对方顺序补齐
    fill2 = [g for g in p1 if g not in p2[a:b]]
    pos = [i for i in range(N) if not (a <= i < b)]
    c1[pos], c2[pos] = fill1, fill2
    return c1, c2

def swap_mutate(r):
    r = r.copy()
    i, j = rng.choice(N, 2, replace=False)
    r[i], r[j] = r[j], r[i]
    return r

pop = np.array([rng.permutation(N) for _ in range(POP)])
history = []
for _ in range(GEN):
    fit = np.array([route_len(r) for r in pop])      # 越短越好
    history.append(float(fit.min()))
    elite = pop[int(fit.argmin())].copy()
    parents = np.empty_like(pop)
    for i in range(POP):                             # 锦标赛:取较短的
        cand = rng.integers(0, POP, 3)
        parents[i] = pop[cand[np.argmin(fit[cand])]]
    for i in range(0, POP, 2):                       # OX 交叉
        if rng.random() < 0.8:
            parents[i], parents[i + 1] = ox_cross(parents[i], parents[i + 1])
    for i in range(POP):                             # 交换变异
        if rng.random() < 0.25:
            parents[i] = swap_mutate(parents[i])
    pop = parents
    pop[0] = elite

best = pop[np.argmin([route_len(r) for r in pop])]
gap = (route_len(best) - exact) / exact
print(f"GA 最优路线长度: {route_len(best):.2f}, "
      f"与精确最优的差距: {gap:.2%}")
print("GA 最优路线:", best.tolist())
print("最优值演化(每 100 代):", history[::100])
```

**输出解读**:

```
精确最优: 229.48
GA 最优路线长度: 229.48, 与精确最优的差距: 0.00%
GA 最优路线: [7, 4, 0, 3, 5, 1, 2, 6]
最优值演化(每 100 代): [297.50, 229.48, 229.48]
```

小规模 TSP 上 GA 追平了暴力枚举——而真实赛题的城市数是几十上百,枚举($n!$)完全不可行,GA 的复杂度只取决于种群 × 代数。排列编码的关键纪律:**交叉和变异算子必须保证子代仍是合法排列**(每个城市恰好出现一次),OX 交叉的「拷贝片段 + 按对方顺序补齐」就做到了这一点;若不做修复,重复/缺失城市的「非法解」会迅速污染种群。300 代内从 297.5 收敛到 229.5,进化轨迹本身就是论文里的好素材。

## ⚠️ 常见易错点

1. **轮盘赌用在负适应度上**。轮盘赌要求 $f_i \geq 0$,罚函数/最小化问题直接套会因负概率报错或选偏;min 问题要么先变换($f' = -f$ 或 $1/(1+f)$),要么改用锦标赛选择
2. **没有精英保留**。交叉和变异都是「破坏性」算子,历史最优随时可能被毁掉;每代把最优个体原样保留(如 `pop[0] = elite`),收敛曲线立刻稳定一个档次
3. **排列编码不修非法解**。TSP 交叉后出现重复城市是头号 bug;用 OX/PMX 这类「保证合法性」的算子,并写一个 `assert len(set(route)) == N` 自检
4. **二进制解码分母用错**。分母是 $2^L - 1$ 而不是 $2^L$,否则 $ub$ 永远取不到,边界上的最优解(如本单元例题 2)会系统性错过
5. **罚系数 λ 拍脑袋**。λ 太小 → 最优个体不可行;太大 → 收敛极慢。技巧:先解一次无约束问题估计目标量级,罚系数取「约束违反 1 单位 ≈ 目标值 10%」的刻度,再做敏感性实验
6. **早熟收敛不处理**。收敛曲线早早躺平但离已知下界/参考解很远,说明多样性枯竭;对策:加大变异率、增大种群、锦标赛 k 调小,或引入「移民」(定期注入随机新个体)
7. **只跑一次就下结论**。GA 是随机算法,单次结果有运气成分;论文标准写法是「固定多个种子各跑 20 次,报告最优值/均值/标准差」,并附收敛曲线

## ✏️ 自测练习(选择题)

**第 1 题** 二进制编码 GA 中,10 位染色体、变量区间 $[0, 5]$,位串 `1010101010` 解码后的 $x$ 约等于:

A. 约 3.333
B. 约 3.330
C. 约 5.000
D. 约 1.667

<details><summary>查看答案与解析</summary>
**答案:A**。位串十进制值 D = 2⁹+2⁷+2⁵+2³+2¹ = 682,解码公式 $x = lb + (ub-lb)\cdot D/(2^L-1) = 5 \times 682/1023 \approx 3.3333$。3.330 是分母误写成 $2^L = 1024$(这样 ub 永远取不到,边界上的最优解会系统性错过);1.667 是把位串误读成 0101010101(D=341);5.000 是全 1 串 1111111111 的解码结果。分母是 $2^L - 1$ 不是 $2^L$,这是解码最常见的错误。
</details>

**第 2 题** 罚函数处理约束后,个体适应度可能是负数。为什么此时轮盘赌选择不能用,而锦标赛选择可以用?

A. 轮盘赌计算太慢,拖累进化速度
B. 轮盘赌只支持整数适应度
C. 锦标赛选择比轮盘赌更快收敛到全局最优
D. 轮盘赌按 p_i = f_i/Σf_j 抽样要求 f_i ≥ 0,负适应度破坏概率语义;锦标赛只看排序,与正负无关

<details><summary>查看答案与解析</summary>
**答案:D**。轮盘赌把适应度当概率权重:$p_i = f_i/\sum f_j$ 要求 $f_i \geq 0$,负的 f_i 会产生负概率,抽样语义崩溃(求和也可能抵消为 0 报错)。锦标赛随机抽 k 个个体取最优,只依赖相对大小,与正负无关,是罚函数场景下更稳的选择。轮盘赌的替代方案还有先把 min 问题变换成 max:$f' = -f$ 或 $f' = 1/(1+f)$。速度与收敛快慢的说法都不是本质原因。
</details>

**第 3 题** 若删掉二进制 GA 中「每代把历史最优个体原样复制进下一代」的精英保留步骤,最可能观察到:

A. 程序报错,无法运行
B. 收敛会更快,因为少了复制开销
C. 收敛曲线剧烈震荡,已找到的最优解可能被交叉/变异毁掉
D. 结果与有精英保留完全一致

<details><summary>查看答案与解析</summary>
**答案:C**。交叉和变异都是「破坏性」算子:没有精英保留,历史最优个体随时可能被交叉打散或被变异破坏,收敛曲线会剧烈震荡,最终解也差一截。精英保留一行代码(如 `pop[0] = elite`)就能稳定收敛,几乎必加;它不影响运行(不会报错),也不是冗余——「结果完全一致」与事实相反,「更快收敛」颠倒了因果。
</details>

## 🏆 竞赛实战链接

- **出镜频率**:国赛 B 题(配送、调度、排班)与各类组合优化题的「万能备胎」;问题 NP-hard、精确算法跑不动时,GA 是标准答案之一
- **论文加分点**:①**收敛曲线图**(本单元例题 1 直接产出);②多次运行的统计表(最优/均值/标准差);③与精确解(小规模枚举)或松弛下界(连续松弛)的差距分析;④参数敏感性(变异率、种群规模的影响)与算子选择理由
- **组合拳**:先精确算法求小规模下界,再 GA 求大规模近优解,最后用「差距(gap)」论证解质量——评审最认这套逻辑
- **工具**:本单元代码可直接复用;更复杂的问题可了解 DEAP/PyGAD 等 GA 框架,但**自实现一遍才能讲清楚论文里的算法细节**

## 💻 代码实现

通用二进制 GA 骨架(改 `objective`、`LB/UB`、`L` 即可用于任意连续函数最大化):

```python
import numpy as np

def binary_ga(objective, LB, UB, L=22, POP=60, GEN=80,
              PC=0.85, PM=0.01, seed=0):
    rng = np.random.default_rng(seed)
    powers = 2 ** np.arange(L - 1, -1, -1)
    decode = lambda pop: LB + (UB - LB) * (pop @ powers) / (2**L - 1)
    pop = rng.integers(0, 2, size=(POP, L))
    history = []
    for _ in range(GEN):
        raw = objective(decode(pop))
        fit = raw - raw.min() + 1e-9     # 平移为正:轮盘赌要求非负适应度
        history.append(float(raw.max()))
        elite = pop[int(fit.argmax())].copy()
        parents = pop[rng.choice(POP, size=POP, p=fit / fit.sum())]
        pairs = parents.reshape(POP // 2, 2, L)
        for i in range(pairs.shape[0]):
            if rng.random() < PC:
                k = int(rng.integers(1, L))
                pairs[i, 0, k:], pairs[i, 1, k:] = (
                    pairs[i, 1, k:].copy(), pairs[i, 0, k:].copy())
        pop = pairs.reshape(POP, L)
        pop ^= (rng.random((POP, L)) < PM)
        pop[0] = elite
    x = decode(pop)
    return x[np.argmax(objective(x))], history

f = lambda x: x * np.sin(10 * np.pi * x) + 2
best, hist = binary_ga(f, 0.0, 4.0)
print(f"最优解 x={best:.4f}, f={f(best):.4f}")   # x=3.8502, f=5.8501
```

## 📚 延伸阅读

- **经典书**:Goldberg, *Genetic Algorithms in Search, Optimization and Machine Learning* — GA 的开山教材
- **综述**:Holland 的 Schema 理论(解释 GA 为何有效)值得在论文「算法原理」一节引用
- **框架**:DEAP(https://deap.readthedocs.io/)支持 GA/GP/进化策略的成熟框架,自实现之后再上手框架
- **姊妹单元**:《scipy.optimize求解优化问题》(差分进化等现成全局优化器)→《整数规划与分支定界》(精确算法的对照);TSP 的精确与近似解法可见《networkx图论编程》单元延伸阅读

## 🧠 小结

1. GA 五组件:编码(基因型设计)、适应度(生存标准)、选择(适者繁殖)、交叉(重组)、变异(扰动),外加几乎必加的精英保留
2. 编码决定算子:二进制配位翻转/单点交叉,实数配算术交叉/高斯变异,排列配 OX/PMX/交换变异——**非法解是排列编码的头号杀手**
3. 选择算子按需选:轮盘赌要非负适应度,锦标赛只看排序,罚函数场景优先锦标赛
4. 罚函数把约束折进目标,λ 的选取是艺术:先估目标量级,再做敏感性实验
5. 实验规范:多种子多次运行报均值 ± 标准差 + 收敛曲线 + 与参考解对比 gap——这套组合拳是 GA 进论文的完整姿势
