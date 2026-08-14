# 凸优化与KKT条件

> **难度**:实战 · **预计学习时长**:60 分钟 · **主讲智能体**:🧩 建模手 · **方法类别**:优化

## 🎯 学习目标

学完本单元,你应该能够:

- 判断一个集合是否凸集、一个函数是否凸函数(定义 + Hessian 半正定两种方法)
- 写出一般约束优化问题的 Lagrange 函数,并完整列出 KKT 四条件
- 用 KKT 条件手工求解小型凸优化问题,并能解释每个乘子的符号与互补松弛含义
- 写出对偶问题,理解弱对偶/强对偶,知道 Slater 条件保证什么
- 用 cvxpy 求解凸优化问题,并说出「凸优化 = 全局最优有保证」这句话成立的前提

## 📖 核心概念

### 1. 凸集与凸函数

- **凸集**:集合 $C$ 内任意两点的连线仍在 $C$ 内,即 $\forall x,y \in C,\ \theta x + (1-\theta)y \in C,\ \theta \in [0,1]$。线性规划的可行域(半空间的交集)是凸集
- **凸函数**:定义域为凸集,且满足 $\forall x,y,\ \theta \in [0,1]$:

$$f(\theta x + (1-\theta)y) \leq \theta f(x) + (1-\theta)f(y)$$

几何含义:函数图像**在任意弦的下方**。常见凸函数:$x^2$、$e^x$、$-\ln x$、范数 $\|x\|$、线性函数(既是凸也是凹)

- **二阶判定**(可微函数):$f$ 凸 $\iff$ Hessian 矩阵 $\nabla^2 f(x) \succeq 0$(处处半正定)

### 2. 凸优化问题的标准形式

$$\min f_0(x) \quad \text{s.t.} \quad f_i(x) \leq 0 \ (i=1..m), \quad Ax = b$$

其中 $f_0, f_1, \dots, f_m$ 都是**凸函数**,等式约束是**仿射**的。关键性质:

> **凸优化的局部最优解就是全局最优解**——这是它与一般非线性规划的本质区别。在数学建模竞赛里,「把问题写成凸问题」意味着你找到的解不需要担心陷入局部极小,这是论文里非常有说服力的论点。

### 3. Lagrange 函数与 KKT 条件

对一般约束问题(Lagrange 函数):

$$L(x, \lambda, \mu) = f_0(x) + \sum_{i=1}^{m} \lambda_i f_i(x) + \sum_{j=1}^{p} \mu_j h_j(x)$$

**KKT 条件**(凸问题下是最优解的充分必要条件):

1. **稳定性**:$\nabla_x L = 0$,即 $\nabla f_0(x) + \sum \lambda_i \nabla f_i(x) + \sum \mu_j \nabla h_j(x) = 0$
2. **原始可行性**:$f_i(x) \leq 0$,$h_j(x) = 0$
3. **对偶可行性**:$\lambda_i \geq 0$(不等式约束的乘子必须非负!)
4. **互补松弛**:$\lambda_i f_i(x) = 0$——约束「松」($f_i(x)<0$)时乘子必为 0;乘子 $>0$ 时约束必「紧」

### 4. 对偶问题与强对偶

- **对偶函数**:$g(\lambda, \mu) = \inf_x L(x,\lambda,\mu)$,对 $\lambda \geq 0$ 它是原问题最优值的**下界**
- **弱对偶**:$d^* \leq p^*$(对偶最优值不超过原问题最优值)——对任何问题都成立
- **强对偶**:$d^* = p^*$。**Slater 条件**(存在严格可行点 $f_i(x) < 0$)保证凸问题强对偶成立

## 🧮 公式与结论

### KKT 求解套路(手工求解四步)

1. 把约束写成标准方向:$f_i(x) \leq 0$(注意方向,方向写反乘子符号就反了)
2. 写 Lagrange 函数并求 $\nabla_x L = 0$,把 $x$ 用乘子表示
3. 用互补松弛分类讨论:哪些 $\lambda_i = 0$、哪些约束取等
4. 求解并验证:对偶可行性($\lambda \geq 0$)与原始可行性全部满足

### 凸函数判别速查

| 函数 | 凸? | 条件 |
|------|-----|------|
| $ax+b$ | 凸且凹 | — |
| $x^2$ | 凸 | — |
| $e^{ax}$ | 凸 | 任意 $a$ |
| $-\ln x$ | 凸 | $x>0$ |
| $x^p$ | $p \geq 1$ 或 $p \leq 0$ 时凸 | $x>0$ |
| $\|x\|$ 类范数 | 凸 | — |
| $\max\{f_1, f_2\}$ | 凸 | $f_1, f_2$ 凸 |
| $f(x) = x^TAx$ | 凸 | $A \succeq 0$ |

## 💡 经典例题

### 例题 1:不等式约束的 KKT 求解

求解:

$$\min x_1^2 + x_2^2 \quad \text{s.t.} \quad x_1 + x_2 \geq 1, \quad x_2 \leq 2$$

**第一步:约束标准化**。写成 $\leq 0$ 方向:

$$g_1(x) = 1 - x_1 - x_2 \leq 0, \quad g_2(x) = x_2 - 2 \leq 0$$

**第二步:Lagrange 函数与稳定性**:

$$L = x_1^2 + x_2^2 + \lambda_1(1 - x_1 - x_2) + \lambda_2(x_2 - 2), \quad \lambda_1, \lambda_2 \geq 0$$

$$\frac{\partial L}{\partial x_1} = 2x_1 - \lambda_1 = 0 \Rightarrow x_1 = \frac{\lambda_1}{2}, \qquad \frac{\partial L}{\partial x_2} = 2x_2 - \lambda_1 + \lambda_2 = 0 \Rightarrow x_2 = \frac{\lambda_1 - \lambda_2}{2}$$

**第三步:分类讨论**。

- 情形 A:$\lambda_2 = 0$,$\lambda_1 > 0$ → $g_1 = 0$ 取等:$x_1 + x_2 = \lambda_1 = 1$,得 $x_1 = x_2 = 0.5$,$\lambda_1 = 1$。检验 $g_2$:$x_2 - 2 = -1.5 < 0$ 满足,互补松弛一致 ✓
- 情形 B:$\lambda_1 = 0$ → $x_1 = x_2 = 0$,违反 $g_1 \leq 0$(即 $x_1+x_2 \geq 1$)✗
- 情形 C:两个约束都紧:$x_1+x_2 = 1$ 且 $x_2 = 2$ → $x = (-1, 2)$,$\lambda_1 = -2 < 0$,违反对偶可行性 ✗

**第四步:结论**。唯一 KKT 点:

$$x^* = (0.5, 0.5), \quad \lambda_1 = 1, \quad \lambda_2 = 0, \quad f^* = 0.5$$

**解析**:目标函数是凸函数($\nabla^2 f = 2I \succ 0$),约束集是凸集(半空间交),所以这是凸问题,KKT 点即全局最优。$\lambda_1 = 1$ 的灵敏度含义:把约束 $x_1+x_2 \geq 1$ 的右端放松到 $0.9$,最优值近似改善 $1 \times 0.1$;$x_2 \leq 2$ 是松约束,$\lambda_2 = 0$,放松它无收益。

### 例题 2:等式约束(Lagrange 乘子法)

求解:

$$\min x_1^2 + 2x_2^2 \quad \text{s.t.} \quad x_1 + x_2 = 1$$

$$L = x_1^2 + 2x_2^2 + \mu(1 - x_1 - x_2)$$

$$\frac{\partial L}{\partial x_1} = 2x_1 - \mu = 0, \quad \frac{\partial L}{\partial x_2} = 4x_2 - \mu = 0 \Rightarrow x_1 = \frac{\mu}{2}, \ x_2 = \frac{\mu}{4}$$

代入等式约束:$\frac{\mu}{2} + \frac{\mu}{4} = 1 \Rightarrow \mu = \frac{4}{3}$

$$x^* = \left(\frac{2}{3}, \frac{1}{3}\right), \quad f^* = \frac{4}{9} + \frac{2}{9} = \frac{2}{3}$$

**解析**:等式约束的乘子 $\mu$ **没有符号限制**——只有不等式约束才要求 $\lambda \geq 0$,这是最常被搞混的一点。验证:$f(1,0) = 1 > 2/3$,$f(0,1) = 2 > 2/3$,确实 $x^*$ 更优。

### 例题 3:对偶函数与强对偶

对例题 1 只保留第一个约束,求对偶函数并验证强对偶:

$$\min x_1^2 + x_2^2 \quad \text{s.t.} \quad 1 - x_1 - x_2 \leq 0 \quad (\lambda \geq 0)$$

$$L = x_1^2 + x_2^2 + \lambda(1 - x_1 - x_2)$$

求下确界:$\partial L/\partial x_1 = 2x_1 - \lambda = 0 \Rightarrow x_1 = \lambda/2$,同理 $x_2 = \lambda/2$:

$$g(\lambda) = \frac{\lambda^2}{4} + \frac{\lambda^2}{4} + \lambda(1 - \lambda) = \lambda - \frac{\lambda^2}{2}$$

最大化对偶:$\frac{dg}{d\lambda} = 1 - \lambda = 0 \Rightarrow \lambda^* = 1$

$$d^* = g(1) = 1 - \frac{1}{2} = \frac{1}{2} = p^*$$

**解析**:$d^* = p^* = 0.5$,强对偶成立。原因是该问题满足 Slater 条件:存在严格可行点,如 $(1, 1)$ 使 $1-1-1 = -1 < 0$。对偶最优乘子 $\lambda^* = 1$ 与原问题 KKT 乘子一致——乘子就是对偶变量,这是对偶理论最漂亮的闭环。

## ⚠️ 常见易错点

1. **约束方向写反导致乘子符号错误**。KKT 要求不等式写成 $f_i(x) \leq 0$;把 $x_1+x_2 \geq 1$ 直接当 $g \geq 0$ 代入,会得到 $\lambda \leq 0$ 的错误结论
2. **忘记等式约束乘子无符号限制**。只有不等式约束的乘子要求 $\geq 0$;等式约束乘子 $\mu$ 任意实数
3. **KKT 对非凸问题只是必要条件**。非凸问题中 KKT 点可能是局部最优甚至鞍点;先判断凸性再下结论
4. **不验证就宣称最优**。求出 KKT 点后,要回代验证全部原始可行性 + 对偶可行性 + 互补松弛,漏一个条件都可能错
5. **把 Hessian 正定与函数凸混淆**。半正定即可判定凸;$x^4$ 的 Hessian 在 0 点为零矩阵,但 $x^4$ 是凸函数——二阶条件是充分条件,不是必要条件
6. **忽略 Slater 条件直接断言强对偶**。凸问题一般满足 Slater,但涉及等式约束时需存在同时满足等式与严格不等式的点;用对偶解前先检查

## ✏️ 自测练习(选择题)

**第 1 题**$\min x_1^2 - x_2^2$ s.t. $x_1 + x_2 = 1$ 是凸优化问题吗?

A. 是,目标函数是二次函数,二次函数都是凸的
B. 不是,目标函数的 Hessian 为 $\mathrm{diag}(2, -2)$,不定
C. 是,等式约束是仿射的,已满足凸优化的全部要求
D. 不是,因为约束是等式

<details><summary>查看答案与解析</summary>
**答案:B**。凸优化要求目标与不等式约束都是**凸函数**。$x_1^2 - x_2^2$ 的 Hessian 为 $\mathrm{diag}(2,-2)$,有负特征值,是不定矩阵,函数非凸——所以这不是凸问题,KKT 点只是驻点,不能保证全局最优。「二次函数都是凸的」是最常见的记混($x^TAx$ 要求 $A \succeq 0$ 才凸);约束是仿射的没错,但目标函数已经不合格;等式约束本身不影响凸性判定,它的存在与否与凸性无关。
</details>

**第 2 题**用 KKT 条件求解 $\min x^2$ s.t. $x \geq 2$,最优解与对应乘子为:

A. $x^* = 0,\ \lambda^* = 0$
B. $x^* = 4,\ \lambda^* = 2$
C. $x^* = 2,\ \lambda^* = 0$
D. $x^* = 2,\ \lambda^* = 4$

<details><summary>查看答案与解析</summary>
**答案:D**。标准化:$g(x) = 2 - x \leq 0$;$L = x^2 + \lambda(2-x)$,$\lambda \geq 0$。稳定性:$2x - \lambda = 0 \Rightarrow x = \lambda/2$。若 $\lambda = 0$ 则 $x = 0$,违反 $x \geq 2$,故 $\lambda > 0$;互补松弛得 $2 - x = 0$,即 $x^* = 2$,$\lambda^* = 4$,最优值 4。「$x^*=0$」是无约束最优,漏掉了约束;「$\lambda^*=0$」忽略了约束是紧的;「$x^*=4$」把互补松弛的等式套反了。乘子的灵敏度含义:约束放松到 $x \geq 1.9$,最优值约改善 $4 \times 0.1 = 0.4$。
</details>

**第 3 题**关于对偶问题与强对偶,下列说法**正确**的是:

A. 凸问题满足 Slater 条件(存在严格可行点)时,强对偶成立,即 $d^* = p^*$
B. 任何优化问题都满足强对偶
C. 弱对偶($d^* \leq p^*$)只在凸问题中成立
D. Slater 条件与对偶性无关,可以忽略

<details><summary>查看答案与解析</summary>
**答案:A**。弱对偶 $d^* \leq p^*$ 对**任何**问题都成立(对偶最优值不超过原问题最优值);强对偶 $d^* = p^*$ 则需要条件——凸问题满足 Slater 条件时强对偶成立。「任何问题都强对偶」忽略了非凸问题存在对偶间隙(duality gap);「弱对偶只在凸问题成立」说反了,弱对偶是无条件成立的;涉及等式约束时,Slater 条件要求存在同时满足等式与严格不等式的点,用对偶解之前先检查,忽略它可能误用对偶解。
</details>

## 🏆 竞赛实战链接

- **什么时候用**:当模型出现二次目标(最小二乘、投资组合风险、能耗最小)与线性/凸约束时,主动检查凸性;能写成凸问题就写——「本问题为凸优化,求得全局最优解」是论文模型章节的强力卖点
- **投资组合(Portfolio)**:Markowitz 均值-方差模型是经典凸二次规划:$\min \frac{1}{2}x^T\Sigma x$ s.t. $\mu^Tx \geq r_0,\ \sum x_i = 1,\ x \geq 0$,是金融类赛题的标配
- **论文表述建议**:①写出凸性论证(目标 Hessian 半正定 + 约束集为半空间交);②给出 KKT 条件或引用求解器返回的对偶变量做灵敏度分析;③若原问题非凸,说明松弛为凸问题后的误差界
- **工具**:`cvxpy`(竞赛首选,建模语言极简)、`scipy.optimize.minimize(method='SLSQP')`(通用但无全局保证)、Gurobi/COPT 学术版

## 💻 代码实现

```python
import cvxpy as cp

# 例题 1: min x1^2 + x2^2  s.t. x1 + x2 >= 1, x2 <= 2
x = cp.Variable(2)
objective = cp.Minimize(cp.sum_squares(x))
constraints = [x[0] + x[1] >= 1, x[1] <= 2]

prob = cp.Problem(objective, constraints)
prob.solve()

print("最优解:", x.value)  # [0.5 0.5]
print("最优值:", prob.value)  # 0.5
print("约束1对偶(影子价):", constraints[0].dual_value)  # 1.0
print("约束2对偶:", constraints[1].dual_value)  # 0.0 (松约束)
```

> `dual_value` 就是 KKT 乘子——例题 1 里手算的 $\lambda_1 = 1, \lambda_2 = 0$ 在这里原样出现,手算与求解器互相印证。

## 📚 延伸阅读

- **教材**:Boyd & Vandenberghe, *Convex Optimization* — 领域圣经,免费 PDF,竞赛只需读第 1-5 章(凸性、对偶、KKT)
- **中文入门**:王书宁等译《凸优化》;B 站「凸优化 中科大 凌青」口碑极佳
- **实战**:cvxpy 官方教程 [Disciplined Convex Programming](https://www.cvxpy.org/tutorial/dcp/index.html);「DCP 规则」决定了什么样的模型它能解,必看
- **进阶关联**:本单元是《线性规划与单纯形法》与《多目标优化与NSGA-II》的理论升级;对偶理论部分可回头对照 LP 的强对偶定理

## 🧠 小结

1. 凸集 + 凸函数 + 仿射等式 = 凸优化问题;凸优化的局部最优即全局最优
2. KKT 四条件:稳定性、原始可行、对偶可行($\lambda \geq 0$)、互补松弛;凸问题下是充要条件
3. 手工求解的套路:约束标准化 → Lagrange → 分类讨论 → 逐条验证,四个条件一个都不能少
4. 对偶函数是对偶可行乘子下的下确界;Slater 条件保证凸问题强对偶,$d^* = p^*$
5. 竞赛用法:能写成凸问题就写,配合 cvxpy 求解 + 对偶变量做灵敏度分析,论文质感立升一级
