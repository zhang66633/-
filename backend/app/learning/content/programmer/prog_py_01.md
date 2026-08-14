# Python科学计算入门

> **难度**:入门 · **预计学习时长**:45 分钟 · **主讲智能体**:🧩 求解器 · **方法类别**:编程工具

## 🎯 学习目标

学完本单元,你应该能够:

- 说出 NumPy、SciPy、Pandas、Matplotlib 四件套各自的职责,遇到问题知道该调用哪个库
- 创建 NumPy 数组,并用向量化运算替代 for 循环
- 使用 SciPy 完成数值积分、方程求根、最小二乘拟合三类高频数值任务
- 把「建好的数学模型」翻译成一段可运行的 Python 代码,并读懂输出结果

## 📖 核心概念

### 1. 为什么建模竞赛选 Python

数学建模竞赛(国赛/美赛)的赛程只有三天,你需要完成建模、编程求解、画图、写论文的全流程。Python 的胜出原因:

- **一个语言打通全流程**:建模推导可用 SymPy 符号验算,数值求解用 NumPy/SciPy,数据处理用 Pandas,绘图用 Matplotlib/Seaborn
- **代码短、调试快**:同样的最小二乘拟合,C/C++ 要几十行,NumPy 一行搞定
- **生态成熟**:优化、统计、机器学习、图论都有现成库,不用从零造轮子

### 2. 四件套的分工

| 库 | 职责 | 典型场景 |
|------|------|------|
| **NumPy** | 多维数组 + 向量化运算 + 线性代数 | 一切数值计算的地基 |
| **SciPy** | 数值算法:积分、优化、插值、求根 | 模型求解的核心工具 |
| **Pandas** | 表格数据的读取、清洗、聚合 | 处理题目附件的 .csv/.xlsx |
| **Matplotlib** | 数据可视化 | 论文插图 |

> 💡 **心法**:建模题的数据处理链路通常是「Pandas 读入并清洗 → NumPy 数值计算 → SciPy 求解 → Matplotlib 出图」,四个库按这个顺序上场。

### 3. NumPy 的 ndarray:一切的基础

`ndarray` 是 NumPy 的核心数据结构——**同质、定长、多维**的数组。它与 Python 原生 list 的区别:

- **同质**:数组内所有元素类型相同,内存连续排布,存取极快
- **向量化**:`a + b`、`np.sin(a)` 这类运算自动作用到每个元素,底层用 C 实现
- **广播**:形状不同的数组在一定规则下自动扩展对齐(详见《NumPy数组操作实战》单元)

```python
import numpy as np

a = np.array([1.0, 2.0, 3.0])            # 从 list 创建
b = np.linspace(0, 1, 5)                 # 均匀采样 5 个点
c = np.zeros((2, 3))                     # 2×3 全零矩阵
rng = np.random.default_rng(42)          # 现代随机数生成器
d = rng.normal(0, 1, 1000)               # 1000 个标准正态样本

print(a + 10)        # 向量化:每个元素 +10
print(a * a)         # 逐元素相乘(不是矩阵乘法!)
print(f"样本均值 {d.mean():.3f}, 标准差 {d.std():.3f}")
```

### 4. SciPy:数值算法工具箱

SciPy 建立在 NumPy 之上,按子模块组织:

- `scipy.integrate`:数值积分与常微分方程
- `scipy.optimize`:优化与求根(详见《scipy.optimize求解优化问题》单元)
- `scipy.interpolate`:插值
- `scipy.stats`:概率分布与统计检验
- `scipy.linalg`:线性代数
- `scipy.fft`:傅里叶变换

## 🧮 核心 API 速查

| 任务 | API | 说明 |
|------|-----|------|
| 创建数组 | `np.array` / `np.linspace` / `np.arange` | 从 list 创建 / 均匀点 / 等差序列 |
| 特殊数组 | `np.zeros` / `np.ones` / `np.eye` | 全零 / 全一 / 单位阵 |
| 随机数 | `np.random.default_rng(seed)` | 现代随机数生成器,取代旧式 `np.random.seed` |
| 形状变换 | `arr.reshape(m, n)` / `arr.T` | 重塑 / 转置 |
| 聚合统计 | `arr.sum / mean / max / argmax` | 支持 `axis=` 参数按轴计算 |
| 矩阵运算 | `A @ B` / `np.linalg.inv` / `np.linalg.eig` | 矩阵乘 / 求逆 / 特征值分解 |
| 数值积分 | `scipy.integrate.quad(f, a, b)` | 定积分 |
| 方程求根 | `scipy.optimize.root_scalar(f, bracket=[a, b])` | 一元方程数值解 |
| 曲线拟合 | `scipy.optimize.curve_fit(f, x, y)` | 最小二乘拟合 |
| 概率分布 | `scipy.stats.norm.pdf / .cdf / .rvs` | 密度 / 分布函数 / 抽样 |

## 💡 经典例题

### 例题 1:向量化统计(成绩分析)

> 某校 500 名学生参加数学建模选拔赛,成绩服从均值 75、标准差 12 的正态分布(分数取整并截断在 [0, 100])。请用 NumPy 计算平均分、标准差、及格率与最高分,并输出标准化成绩(Z 分数)最高的前三名学号。

**代码**:

```python
import numpy as np

rng = np.random.default_rng(2024)          # 固定种子,结果可复现
scores = rng.normal(75, 12, 500)           # 500 个正态样本
scores = np.clip(np.round(scores), 0, 100) # 取整并截断到 [0,100]

mean = scores.mean()
std = scores.std()
pass_rate = (scores >= 60).mean()          # 布尔数组求均值 = 及格比例
best = scores.max()

z = (scores - mean) / std                  # 标准化:Z 分数
top3 = np.argsort(-z)[:3]                  # 降序排列取前三的下标

print(f"平均分: {mean:.2f}, 标准差: {std:.2f}")
print(f"及格率: {pass_rate:.1%}, 最高分: {best:.0f}")
print(f"Z 分数前三名: 学号 {top3}, Z = {z[top3].round(2)}")
```

**输出解读**:

```
平均分: 74.95, 标准差: 11.72
及格率: 89.8%, 最高分: 100
Z 分数前三名: 学号 [388 412 406], Z = [2.14 2.14 2.14]
```

整个统计过程**没有一个显式 for 循环**。`(scores >= 60).mean()` 是 NumPy 的经典技巧:布尔比较返回布尔数组,`True` 按 1 参与求均值,得到的恰好是及格比例。这一套「生成 → 清洗 → 统计」的流程几乎原样出现在每道建模题的数据处理阶段。

### 例题 2:数值积分与求根(排队系统阈值分析)

> 某服务系统的顾客到达间隔服从均值为 2 分钟的指数分布,密度函数为 $f(t) = \lambda e^{-\lambda t}$($\lambda = 0.5$)。求:(1) 间隔超过 5 分钟的概率;(2) 使「间隔超过 $T$ 分钟的概率恰为 5%」的阈值 $T$。

**建模**:问题 (1) 是定积分 $P = \int_5^\infty \lambda e^{-\lambda t}\,dt = e^{-2.5}$;问题 (2) 是求根:解方程 $e^{-\lambda T} = 0.05$。

**代码**:

```python
import numpy as np
from scipy import integrate, optimize, stats

lam = 0.5
f = lambda t: lam * np.exp(-lam * t)

# (1) 定积分 + 解析验证
p1, err = integrate.quad(f, 5, np.inf)
print(f"数值积分 P(T>5) = {p1:.4f} (误差估计 {err:.1e})")
print(f"解析值 e^(-2.5)  = {np.exp(-2.5):.4f}")

# (2) 求根:解 e^(-λT) = 0.05,即 g(T) = 0
g = lambda T: np.exp(-lam * T) - 0.05
T = optimize.root_scalar(g, bracket=[0, 50], method="brentq").root
print(f"阈值 T = {T:.3f} 分钟")
print(f"验证: stats.expon.cdf({T:.3f}, scale=2) = {stats.expon.cdf(T, scale=2):.4f}")
```

**输出解读**:

```
数值积分 P(T>5) = 0.0821 (误差估计 9.2e-09)
解析值 e^(-2.5)  = 0.0821
阈值 T = 5.991 分钟
验证: stats.expon.cdf(5.991, scale=2) = 0.9500
```

`integrate.quad` 直接支持无穷上限;`root_scalar` 用布伦特法在区间内找根,比手写二分法稳得多。最后一行的验证是竞赛论文的好习惯——**用第二种方法交叉验证第一种方法的结果**。数值解与解析值吻合到 4 位小数,这正是「代码可信」的直接证据。

### 例题 3:最小二乘拟合(疫情数据建模)

> 给出某地区疫情早期连续 10 天的累计病例数(见代码),试用逻辑斯蒂模型 $P(t) = \dfrac{K}{1 + e^{-r(t - t_0)}}$ 拟合,并预测第 11、12 天的病例数。

**代码**:

```python
import numpy as np
from scipy.optimize import curve_fit

t = np.arange(10)
cases = np.array([2, 5, 9, 18, 35, 62, 98, 145, 189, 223])

def logistic(t, K, r, t0):
    return K / (1 + np.exp(-r * (t - t0)))

popt, pcov = curve_fit(logistic, t, cases, p0=[400, 0.6, 5])
K, r, t0 = popt
print(f"拟合参数: K={K:.1f}, r={r:.3f}, t0={t0:.2f}")
print(f"参数标准差: {np.sqrt(np.diag(pcov)).round(3)}")

pred = logistic(np.array([10, 11]), K, r, t0)
print(f"第 11、12 天预测: {pred.round(0)}")
```

**输出解读**:

```
拟合参数: K=273.3, r=0.685, t0=6.82
参数标准差: [2.494 0.008 0.034]
第 11、12 天预测: [245. 259.]
```

`curve_fit` 内部做的是非线性最小二乘(Levenberg-Marquardt 算法):`p0` 给初值,`pcov` 返回参数协方差矩阵,对角线开方即参数标准差。把「参数 ± 标准差」的表写进论文,模型可靠性就有了量化支撑。注意:初值给得太离谱会导致拟合发散,一般先画散点图目测参数量级再设初值。

## ⚠️ 常见易错点

1. **`a * b` 是逐元素乘,不是矩阵乘法**。两个 NumPy 数组之间的 `*` 是 Hadamard 积,矩阵乘要用 `@` 或 `np.dot`;形状不匹配时 `*` 会触发广播,得到「悄悄错了形状」的结果
2. **`np.random.seed` 已过时**。旧式全局种子在多线程/多进程下不可复现,请用 `rng = np.random.default_rng(seed)`,所有抽样都从 `rng` 调用
3. **list 和 ndarray 混用**。`[1,2,3] + [1,2,3]` 是拼接得到 `[1,2,3,1,2,3]`,而 `np.array([1,2,3]) + np.array([1,2,3])` 是逐元素加得到 `[2,4,6]`;读取数据后先 `np.asarray()` 转数组再计算
4. **误以为 `quad` 万能**。被积函数有尖峰、振荡或间断点时 `quad` 可能静默给出错误结果,注意检查返回的误差估计,必要时分段积分或换 `quad_vec`
5. **非线性拟合初值乱给**。初值离真值太远会发散或收敛到局部极值;先画图目测量级,再给 `p0`
6. **输出不设精度**。默认 `print` 浮点数可能吐出一长串小数,论文表格和截图里用 f-string 的 `:.3f` 控制位数,避免「伪精度」

## ✏️ 自测练习

**第 1 题(判断)**:`np.array([1,2,3]) ** 2` 的结果是什么?它与 `np.dot` 语义有何区别?

<details><summary>查看答案</summary>

结果是 `[1, 4, 9]`,即逐元素平方。`**`、`*`、`/` 都是逐元素运算;只有 `@`、`np.dot`、`np.matmul` 才是矩阵乘法语义。对向量而言 `a @ a` 是内积(标量 14),`a * a` 是逐元素积(向量 `[1,4,9]`)。

</details>

**第 2 题(补全)**:用一行代码生成从 0 到 10 的 101 个等间隔点。

<details><summary>查看答案</summary>

```python
import numpy as np
np.linspace(0, 10, 101)
```

`np.linspace(start, stop, num)` 包含两端点共 101 个点,步长 0.1。注意与 `np.arange(0, 10.1, 0.1)` 的区别:`arange` 用浮点步长累加会产生累积误差,等间隔采样一律优先 `linspace`。

</details>

**第 3 题(计算)**:用 `scipy.integrate.quad` 验证正态分布密度在全实轴上的积分等于 1(取 $\mu=1,\ \sigma=2$)。

<details><summary>查看答案</summary>

```python
import numpy as np
from scipy import integrate, stats

mu, sigma = 1.0, 2.0
val, err = integrate.quad(lambda x: stats.norm.pdf(x, mu, sigma), -np.inf, np.inf)
print(val, err)   # 0.9999999999999999 与约 4e-9 的误差
```

`quad` 支持无穷上下限,内部会做变量替换。这个恒等式也是检验自己推导的密度函数是否写错的快捷手段。

</details>

**第 4 题(概念)**:为什么 NumPy 的向量化运算比 Python 的 for 循环快?

<details><summary>查看答案</summary>

两个原因:①NumPy 底层用编译型 C/Fortran 代码执行运算,而 Python 循环的每次迭代都要经过解释器开销(类型检查、边界检查、动态分派);②ndarray 内存连续,CPU 缓存命中率高,还能利用 SIMD 指令同时处理多个数据。数据量越大差距越明显(可达几十到几百倍)。注意 `np.vectorize` 只是语法糖,并不带来真正的速度提升——真正的向量化是让运算本身发生在 NumPy 内部(详见《代码性能优化》单元)。

</details>

## 🏆 竞赛实战链接

- **出镜频率**:Python 是近年国赛/美赛获奖论文中最主流的编程语言,几乎所有赛题的官方附件(csv/xlsx)都用 Pandas + NumPy 处理
- **论文加分点**:①代码附在附录,注明 Python 与主要库的版本号,体现可复现性;②关键数值结果保留 3~4 位小数并在正文制表;③随机模拟类结果必须固定随机种子,评审复现时才能得到相同结果
- **工具**:Jupyter Notebook 边写边看中间结果;除了 `print`,学会用 `arr.shape`、`arr.dtype` 快速自查

## 💻 代码实现

本单元三个例题的完整代码已在上文给出。下面给出一个把「四件套」串起来的最小完整流程——从带噪声数据到直线拟合再到出图(绘图细节见《Matplotlib数据可视化》单元):

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]  # 中文字体
plt.rcParams["axes.unicode_minus"] = False

# 1. 生成带噪声的数据(真实关系 y = 2.5 x + 1.2)
rng = np.random.default_rng(0)
x = np.linspace(0, 10, 30)
y = 2.5 * x + 1.2 + rng.normal(0, 1.5, x.size)

# 2. 最小二乘直线拟合
def line(x, k, b):
    return k * x + b

(k, b), cov = curve_fit(line, x, y)
print(f"y = {k:.3f} x + {b:.3f}")

# 3. 画图(面向对象 API)
fig, ax = plt.subplots(figsize=(7, 4.5))
ax.scatter(x, y, s=25, label="观测数据", zorder=3)
ax.plot(x, k * x + b, "r-", lw=2, label=f"拟合直线 (k={k:.2f})")
ax.set_xlabel("x"); ax.set_ylabel("y")
ax.legend(); ax.grid(alpha=0.3)
fig.savefig("fit_demo.png", dpi=200)
print("图片已保存到 fit_demo.png")
```

## 📚 延伸阅读

- **官方教程**:NumPy Quickstart(https://numpy.org/doc/stable/user/quickstart.html)— 读一遍覆盖本单元 90% 内容
- **SciPy 文档**:https://docs.scipy.org/doc/scipy/tutorial/index.html,重点看 integrate 与 optimize 两个模块
- **书籍**:Wes McKinney《利用 Python 进行数据分析》— 数据部分圣经
- **进阶关联**:学完本单元 → 《NumPy数组操作实战》(广播与索引进阶)→ 《Pandas数据处理》(结构化数据)→ 《scipy.optimize求解优化问题》(模型求解)

## 🧠 小结

1. Python 四件套分工明确:NumPy 算、SciPy 解、Pandas 洗、Matplotlib 画;建模题按「读 → 洗 → 算 → 解 → 画」的链路走
2. ndarray 是同质定长多维数组,向量化运算取代 for 循环,是 Python 数值计算速度的根本来源
3. `quad`(积分)、`root_scalar`(求根)、`curve_fit`(拟合)是 SciPy 三件高频工具,覆盖了建模题中大半的「求解」需求
4. 现代写法:随机数用 `default_rng`,矩阵乘用 `@`,输出用 f-string 控制精度——这些细节决定你的代码是「能跑」还是「能写进论文附录」
5. 任何数值结果都要想办法**二次验证**(解析值、另一个库、极端情形),这是建模论文可信度的底线
