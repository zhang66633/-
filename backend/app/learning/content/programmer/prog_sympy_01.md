# SymPy符号计算

> **难度**:实战 · **预计学习时长**:45 分钟 · **主讲智能体**:🧩 求解器 · **方法类别**:编程工具

## 🎯 学习目标

学完本单元,你应该能够:

- 声明符号变量,构建符号表达式并做化简、代入与数值化
- 用 SymPy 求导、积分、求极限、泰勒展开,验证手工推导
- 求解代数方程(解析解)与用 `nsolve` 求数值根
- 用 `dsolve` 解析求解常微分方程,并与 scipy 数值解互验
- 用 `lambdify` 把符号结果桥接成 NumPy 数值函数

## 📖 核心概念

### 1. 符号世界与数值世界的分野

SymPy 操作的是**符号表达式**(精确、可推导),NumPy 操作的是**数值数组**(近似、可计算)。建模时两者分工:

- **推导阶段**(模型建立):SymPy 求导、解方程、化简——验证手工推导、自动生成公式
- **计算阶段**(模型求解):把符号结果 `lambdify` 成数值函数交给 NumPy/SciPy

```python
import sympy as sp

x, y = sp.symbols("x y", real=True)      # 声明符号
expr = (x + y) ** 2
print(sp.expand(expr))                    # x**2 + 2*x*y + y**2
print(sp.factor(x**2 - 2*x + 1))          # (x - 1)**2
print(expr.subs({x: 1, y: 2}))            # 代入 → 9
print(sp.N(sp.pi, 30))                    # 高精度数值化
```

### 2. 微积分三件套:diff / integrate / limit

```python
import sympy as sp

x = sp.symbols("x")
f = sp.sin(x) * sp.exp(x)

print("一阶导:", sp.diff(f, x))                    # (sin+cos)*exp
print("二阶导:", sp.diff(f, x, 2))
print("不定积分:", sp.integrate(x**2, x))          # x**3/3
print("定积分:", sp.integrate(x**2, (x, 0, 1)))    # 1/3
print("极限:", sp.limit(sp.sin(x) / x, x, 0))      # 1
print("泰勒展开:", sp.series(sp.cos(x), x, 0, 6))  # 1 - x²/2 + x⁴/24 + O(x⁶)
```

### 3. 方程求解:solve 与 nsolve 的分工

```python
import sympy as sp

x = sp.symbols("x")

# 解析解:多项式、线性方程组、可化简的方程
print(sp.solve(sp.Eq(x**2 - 5*x + 6, 0), x))       # [2, 3]

# 无解析解时用 nsolve(数值牛顿法,需给初值)
eq = sp.Eq(sp.cos(x), x)
print("nsolve:", sp.nsolve(eq, x, 0.7))             # 约 0.739

# 方程组
y = sp.symbols("y")
print(sp.solve([x + y - 5, x - y - 1], [x, y]))    # {x: 3, y: 2}
```

`solve` 返回空列表或报错时,不是 SymPy 的锅——而是方程可能真的**没有解析解**(五次以上多项式的一般情形),换 `nsolve` 或数值方法。

### 4. 符号矩阵与微分方程

```python
import sympy as sp

M = sp.Matrix([[1, 2], [3, 4]])
print("特征值:", M.eigenvals())          # {5/2 - √33/2: 1, 5/2 + √33/2: 1}
print("逆矩阵:", M.inv())

t = sp.symbols("t")
P = sp.Function("P")
r = sp.symbols("r", positive=True)
eq = sp.Eq(sp.diff(P(t), t), r * P(t))   # dP/dt = rP
print(sp.dsolve(eq, P(t)))               # P(t) = C1*exp(r*t)
```

### 5. lambdify:符号 → 数值的桥

```python
import sympy as sp
import numpy as np

x = sp.symbols("x")
f = sp.sin(x) ** 2 + sp.cos(x) ** 2
f_num = sp.lambdify(x, f, "numpy")        # 编译成 NumPy 函数
print(f_num(np.array([0.0, 1.0, 2.0])))   # [1. 1. 1.]
```

`lambdify` 把符号表达式转成**向量化**的数值函数,支持数组输入——推导出的复杂公式(梯度、雅可比、特解)从此可以直接参与数值计算与画图。

## 🧮 核心 API 速查

| 任务 | API | 说明 |
|------|-----|------|
| 声明符号 | `sp.symbols("x y", real=True)` | 参数可按需加 positive/integer |
| 求导 | `sp.diff(f, x, n)` | n 阶导;多变量 `diff(f, x, y)` |
| 积分 | `sp.integrate(f, x)` / `(f, (x, a, b))` | 不定 / 定积分 |
| 极限 | `sp.limit(f, x, 0, dir="+")` | 单侧极限用 dir |
| 泰勒展开 | `sp.series(f, x, 0, n)` | 去掉高阶项用 `.removeO()` |
| 解方程 | `sp.solve(eq, x)` / `sp.solveset` | 解析解;方程组传列表 |
| 数值求根 | `sp.nsolve(eq, x, x0)` | 需要初值 |
| 化简 | `sp.simplify` / `expand` / `factor` | 通用 / 展开 / 因式分解 |
| 代入 | `expr.subs({x: 1})` | 表达式不可变,subs 返回新表达式 |
| 符号矩阵 | `sp.Matrix([[1, 2], [3, 4]])` | `.inv()` / `.eigenvals()` / `.det()` |
| 微分方程 | `sp.dsolve(Eq, func)` | 常微分方程解析解 |
| 数值化 | `sp.N(expr, 20)` / `expr.evalf(20)` | 高精度浮点 |
| 桥接数值 | `sp.lambdify(vars, expr, "numpy")` | 转向量化数值函数 |

## 💡 经典例题

### 例题 1:极值问题的符号推导(验证手工计算)

> 用 SymPy 完整推导 $f(x) = x^3 - 3x + 2$ 的极值:求导 → 解驻点方程 → 二阶导判别,输出每个驻点的类型与函数值。

**代码**:

```python
import sympy as sp

x = sp.symbols("x", real=True)
f = x**3 - 3*x + 2

df = sp.diff(f, x)               # 一阶导 3x² - 3
ddf = sp.diff(f, x, 2)           # 二阶导 6x
crit = sp.solve(sp.Eq(df, 0), x)

print("f'(x) =", df)
print("驻点:", crit)
for c in crit:
    kind = "极小值" if ddf.subs(x, c) > 0 else "极大值"
    print(f"x = {c}: f = {f.subs(x, c)}, f'' = {ddf.subs(x, c)} → {kind}")
```

**输出解读**:

```
f'(x) = 3*x**2 - 3
驻点: [-1, 1]
x = -1: f = 4, f'' = -6 → 极大值
x = 1: f = 0, f'' = 6 → 极小值
```

整个推导过程完全符号化:驻点 $-1, 1$ 是**精确**的,判别依据 $f''(c)$ 的符号也是符号比较,没有任何数值误差。竞赛中这类「符号验算」有两种用法:①复杂模型手工推导后,用 SymPy 快速验证导数/极值是否正确(改错比重新推导便宜);②灵敏度分析中的偏导数矩阵(雅可比)用 `sp.Matrix` + `diff` 自动生成,避免手抄公式出错。

### 例题 2:Logistic 方程的解析解与数值解互验

> 人口增长模型 $\dfrac{dP}{dt} = rP\left(1 - \dfrac{P}{K}\right)$。请:(1) 用 `dsolve` 求含初值 $P(0) = P_0$ 的特解;(2) 把特解 `lambdify` 后与 scipy 数值解对照,验证最大偏差。

**代码**:

```python
import sympy as sp
import numpy as np
from scipy.integrate import solve_ivp

t = sp.symbols("t")
r, K, P0 = sp.symbols("r K P0", positive=True)
P = sp.Function("P")
eq = sp.Eq(sp.diff(P(t), t), r * P(t) * (1 - P(t) / K))
sol = sp.dsolve(eq, P(t))

C1 = next(s for s in sol.free_symbols if str(s).startswith("C"))
c1_val = sp.solve(sp.Eq(sol.rhs.subs(t, 0), P0), C1)[0]
solution = sp.simplify(sol.rhs.subs(C1, c1_val))
print("特解:", solution)

# lambdify 成数值函数,与数值解对照
params = {r: 0.5, K: 100.0, P0: 5.0}
P_num = sp.lambdify(t, solution.subs(params), "numpy")
ivp = solve_ivp(lambda t_, y: 0.5 * y * (1 - y / 100.0),
                [0, 20], [5.0], rtol=1e-9, atol=1e-11,
                max_step=0.5, dense_output=True)
ts = np.linspace(0, 20, 100)
err = float(np.max(np.abs(P_num(ts) - ivp.sol(ts).ravel())))
print(f"符号解与数值解的最大偏差: {err:.2e}")
print(f"t=20 时人口: {P_num(20.0):.2f}(趋向 K={params[K]:.0f})")
```

**输出解读**:

```
特解: K*P0*exp(r*t)/(K + P0*exp(r*t) - P0)
符号解与数值解的最大偏差: 2.8e-07
t=20 时人口: 99.91(趋向 K=100)
```

特解 $P(t) = \dfrac{K P_0 e^{rt}}{K + P_0 e^{rt} - P_0}$ 是经典的 S 形曲线:$t \to \infty$ 时 $P \to K$。要点:①`dsolve` 通解含积分常数 $C_1$,用「$t=0$ 代入等于 $P_0$」定出 $C_1$——**定常数**是符号解 ODE 的标准动作;②`solve_ivp` 默认容差较松,符号解与数值解的偏差只能到 $10^{-2}$ 量级,把 `rtol/atol` 收紧到 $10^{-9}/10^{-11}$ 并限制 `max_step` 后,偏差降到 $10^{-7}$(相对误差 $10^{-9}$)——「解析 + 数值互验」时数值求解器的容差设置马虎不得,这是本系列单元的通用纪律。

### 例题 3:符号积分 + lambdify(公式推导全链路)

> 对 $f(x) = e^{-x}\sin(2x)$ 完成:符号定积分 $\int_0^\infty f(x)\,dx$(解析值应等于 $2/5$),再 `lambdify` 与 scipy 数值积分对照;最后对 $f$ 求导并化简,验证 $\lim_{x\to\infty} f(x) = 0$。

**代码**:

```python
import sympy as sp
import numpy as np
from scipy import integrate

x = sp.symbols("x", real=True)
f = sp.exp(-x) * sp.sin(2 * x)

F = sp.integrate(f, (x, 0, sp.oo))         # 符号定积分
print("符号积分:", F, "=", sp.simplify(F))

f_num = sp.lambdify(x, f, "numpy")
val, err = integrate.quad(f_num, 0, np.inf)
print(f"数值积分: {val:.6f} (误差 {err:.1e})")

df = sp.simplify(sp.diff(f, x))            # 导数并化简
print("导数(化简后):", df)
print("x→∞ 极限:", sp.limit(f, x, sp.oo))   # 0
```

**输出解读**:

```
符号积分: 2/5
数值积分: 0.400000 (误差 1.4e-08)
导数(化简后): (-sin(2*x) + 2*cos(2*x))*exp(-x)
x→∞ 极限: 0
```

符号积分给出**精确值** $\dfrac{2}{5}$,数值积分吻合到 6 位小数。这条「符号 → lambdify → 数值验证」的链路是竞赛的高级工作流:公式推导(论文第二章)与数值计算(论文第四章)之间不再有抄写误差——公式由 SymPy 生成、由 `lambdify` 直接执行,论文里的公式与代码里的函数**保证一致**。

## ⚠️ 常见易错点

1. **忘声明符号**。`diff(x**2, x)` 在 `x` 未 `symbols` 时抛 NameError;`sp.symbols("x")` 之后 `x` 才进入符号世界。注意 `sp.Symbol` 与字符串 `"x"` 不是一回事,混用会在 solve 时得到意外结果
2. **浮点污染符号计算**。写 `1/3` 得到 float 0.333…,代入符号公式后精度全失;精确有理数用 `sp.Rational(1, 3)`,小数常数想保留符号语义就用 `sp.sympify("0.1")` 或干脆用分数
3. **`solve` 解不出来就认为无解**。`solve` 对超越方程、高次多项式常返回空集或未完全展开的解;先画图确认根的大致位置,再用 `nsolve(eq, x, x0)` 数值求根
4. **`subs` 以为会修改原表达式**。SymPy 表达式是**不可变**对象,`expr.subs(...)` 返回新表达式,原变量不变;忘记接收返回值是高频 bug
5. **`lambdify` 模块不匹配**。`lambdify(x, expr)` 默认模块的 `sin`/`cos` 不是 NumPy 实现,数组输入会报错;对数组计算一律 `lambdify(x, expr, "numpy")`
6. **`sp.pi` 与 `np.pi` 混用**。符号表达式里写 `np.pi` 会把浮点近似值带进推导,`limit`/`integrate` 的化简识别不了 $\pi$;符号世界用 `sp.pi`、`sp.E`、`sp.oo`(无穷),数值化交给最后的 `evalf`

## ✏️ 自测练习

**第 1 题(判断)**:`sp.solve(sp.Eq(x**5 - x - 1, 0), x)` 会返回什么?想要数值根怎么办?

<details><summary>查看答案</summary>

$x^5 - x - 1 = 0$ 的根**没有根式解析解**(伽罗瓦理论:一般五次方程不可根式求解),`solve` 返回空列表或 RootOf 形式。数值根用 `sp.nsolve(sp.Eq(x**5 - x - 1, 0), x, 1)`(约 1.1673),或 `sp.nroots(x**5 - x - 1)` 一次求全部 5 个复根。

</details>

**第 2 题(计算)**:用 SymPy 求 $f(x) = \sin x \cdot e^x$ 的一阶导,并化简。

<details><summary>查看答案</summary>

```python
import sympy as sp
x = sp.symbols("x")
df = sp.diff(sp.sin(x) * sp.exp(x), x)
print(sp.simplify(df))   # (sin(x) + cos(x))*exp(x)
```

乘法法则:$\dfrac{d}{dx}(\sin x\, e^x) = (\sin x + \cos x) e^x$。手算一遍再对照输出,是练习符号工具的正确姿势。

</details>

**第 3 题(计算)**:用 `lambdify` 把 $g(x) = x^2 + 1$ 转成数值函数并对 `[0, 1, 2]` 求值。

<details><summary>查看答案</summary>

```python
import sympy as sp
import numpy as np
x = sp.symbols("x")
g = sp.lambdify(x, x**2 + 1, "numpy")
print(g(np.array([0, 1, 2])))   # [1 2 5]
```

必须传 `"numpy"` 模块参数,否则对数组输入报 TypeError;`lambdify` 生成的函数是向量化的,可直接用于 `integrate.quad` 或 Matplotlib 画图。

</details>

**第 4 题(概念)**:符号计算与数值计算各适合什么场景?建模竞赛里两者如何配合?

<details><summary>查看答案</summary>

**符号计算**:精确、可推导,适合模型建立阶段的求导/化简/解方程/验证手工推导,但速度慢、很多问题没有解析解。**数值计算**:近似、快,适合大规模求解、模拟、拟合。竞赛配合:①推导阶段用 SymPy 验证公式并自动生成导数/雅可比;②`lambdify` 把公式转成 NumPy 函数参与计算;③同一问题「解析解(若存在)与数值解互验」,偏差小说明两者都对——这也是论文严谨性的展示。

</details>

## 🏆 竞赛实战链接

- **出镜频率**:灵敏度分析(对参数求偏导)、稳定性分析(求特征值、判断平衡点)、模型推导验算,几乎每篇用微分方程/优化模型的论文都用得上
- **论文加分点**:①「解析解与数值解的最大偏差 < 1e-10」这类互验结论,是模型可信度的硬证据;②用 SymPy 生成雅可比矩阵、特征多项式,附录放推导代码;③SIR/Logistic 等经典 ODE 的解析解推导让论文的模型部分更有深度
- **工具**:Jupyter 里 SymPy 表达式有漂亮的 LaTeX 渲染(`sp.init_printing()`),截图进论文附录非常直观

## 💻 代码实现

本单元核心链路的汇总(推导 → 验证 → 桥接):

```python
import sympy as sp
import numpy as np

# 1. 符号推导
x, y = sp.symbols("x y", real=True)
f = x**3 - 3*x + 2
crit = sp.solve(sp.Eq(sp.diff(f, x), 0), x)
print("驻点:", crit, "函数值:", [f.subs(x, c) for c in crit])

# 2. 符号定积分
print("∫x²dx [0,1] =", sp.integrate(x**2, (x, 0, 1)))

# 3. ODE 求解
t = sp.symbols("t"); r = sp.symbols("r", positive=True)
P = sp.Function("P")
print("dP/dt=rP 的解:", sp.dsolve(sp.Eq(sp.diff(P(t), t), r * P(t)), P(t)))

# 4. lambdify 桥接到 NumPy
g = sp.lambdify(x, sp.diff(f, x), "numpy")
print("f' 在 [0,1,2] 的值:", g(np.array([0.0, 1.0, 2.0])))
```

## 📚 延伸阅读

- **官方文档**:SymPy 教程(https://docs.sympy.org/latest/tutorials/intro-tutorial/index.html)— 前四章覆盖本单元全部内容
- **在线工具**:SymPy Live(https://live.sympy.org/)不用安装即可试验
- **姊妹单元**:符号推导结果交给《scipy.optimize求解优化问题》与《Python科学计算入门》做数值验证;《Matplotlib数据可视化》单元负责把 lambdify 出的函数画出来

## 🧠 小结

1. SymPy 是「推导工具」不是「计算工具」:求导、积分、解方程、ODE 解析解,精度是无限的
2. 三件套 `diff` / `integrate` / `limit` 加上 `solve`/`nsolve` 分工,覆盖建模推导的 90% 需求
3. `dsolve` 求通解后必须用初值定出积分常数——「定常数」是符号解 ODE 的标准动作
4. `lambdify(..., "numpy")` 是符号与数值世界的桥:公式推导与代码执行从此零抄写误差
5. 纪律:「解析解与数值解互验」——偏差 $10^{-10}$ 量级的对照结论,是论文可信度最硬的证据之一
