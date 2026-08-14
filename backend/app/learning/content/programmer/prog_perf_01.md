# 代码性能优化

> **难度**:实战 · **预计学习时长**:50 分钟 · **主讲智能体**:🧩 求解器 · **方法类别**:编程工具

## 🎯 学习目标

学完本单元,你应该能够:

- 用 `timeit` / `perf_counter` 精确测量代码耗时,做到「先测量,后优化」
- 识别性能瓶颈的层级:算法复杂度 > 向量化 > 常数级技巧
- 把纯 Python 循环改写为 NumPy 广播向量化,并理解 `np.vectorize` 为什么不是加速
- 用 Numba 的 `@njit` 把「必须写循环」的代码编译提速几十倍
- 掌握内存侧的优化:视图/拷贝、dtype 降精度、in-place 运算

## 📖 核心概念

### 1. 优化第一定律:先测量

优化前必须知道**时间花在哪**——凭直觉优化通常会改错地方:

```python
import timeit
import time

# 一次性计时:timeit 自动多次运行取最优,避免系统抖动干扰
t = timeit.timeit("sum(range(1000))", number=10000)
print(f"单次耗时: {t / 10000 * 1e6:.2f} 微秒")

# 代码块内计时:perf_counter 精度最高
start = time.perf_counter()
result = sum(i * i for i in range(10**6))
elapsed = time.perf_counter() - start
print(f"耗时 {elapsed:.3f} 秒")
```

Jupyter 里用 `%timeit` 魔术命令一行搞定。**没有测量数据的优化都是玄学**。

### 2. 性能层级:复杂度为王

| 层级 | 手段 | 典型加速 |
|------|------|---------|
| 算法级 | $O(n^2)$ 改 $O(n\log n)$:排序、哈希、动态规划 | 数十到数万倍 |
| 向量化 | 循环改 NumPy 广播/ufunc | 10~100 倍 |
| 编译级 | Numba JIT / Cython | 10~100 倍 |
| 常数级 | 缓存、局部变量、in-place | 1~3 倍 |

**口诀**:先问「复杂度能不能降」,再问「循环能不能向量化/编译」,最后才是常数级微调。把一个 $O(n^2)$ 的双重循环用 Numba 加速 50 倍,不如改成 $O(n\log n)$ 算法快。

### 3. 向量化:让运算发生在 NumPy 内部

```python
import numpy as np

rng = np.random.default_rng(0)
x = rng.normal(size=1_000_000)

# 慢:Python 层循环,每次迭代都有解释器开销
s = 0.0
for v in x:
    s += v**2

# 快:整个运算下沉到 C 层
s = np.dot(x, x)  # 或 (x**2).sum() 或 x @ x
```

> ⚠️ **`np.vectorize` 不是加速**。它只是把函数调用「循环」包了一层语法糖,内部仍是 Python 循环,甚至可能更慢。真正的向量化必须让计算发生在 NumPy 内部。

### 4. 循环内的高价习惯

- 循环内 `list.append` 不如预分配数组;字符串 `+=` 拼接是 $O(n^2)$ 灾难,用 `"".join`
- 循环内反复调用小粒度 NumPy 函数(如对 2 元素数组调 `np.sqrt`)开销巨大——碎片化调用比计算本身还贵
- 能整块算的绝不逐元素算:能用广播就用广播(见《NumPy数组操作实战》单元)

### 5. Numba:必须写循环时的救星

Numba 是 JIT 编译器:给函数加 `@njit` 装饰器,把纯 Python 循环编译成机器码:

```python
import numpy as np
from numba import njit


@njit
def sum_of_squares(x):
    s = 0.0
    for v in x:
        s += v * v
    return s


x = np.random.default_rng(0).normal(size=1_000_000)
sum_of_squares(x)  # 第一次调用含编译时间
sum_of_squares(x)  # 之后都是机器码速度
```

- **适用**:数值循环(仿真、动态规划、网格计算),代码越「循环密集」收益越大
- **限制**:只支持 Python 与 NumPy 的**子集**(列表、字典、字符串等特性受限),报错时把复杂逻辑拆到 `@njit` 函数之外
- **代价**:首次调用有编译开销(约 0.1~1 秒),小数据量、单次调用反而更慢;加 `cache=True` 可把编译结果缓存到磁盘
- **并行**:`from numba import prange`,循环无迭代依赖时 `prange` + `parallel=True` 吃满多核

### 6. 内存优化:减少搬砖

```python
import numpy as np

a = np.ones((1000, 1000))
b = a + 1  # 新数组
b = a[::2, ::2]  # 视图:不复制数据(但修改会联动原数组!)
a += 1  # in-place:原地修改,不产生新数组
a32 = a.astype(np.float32)  # 降精度:内存减半,缓存命中率提升
```

- 链式矩阵运算 `A @ B @ C` 会先算 `A @ B` 产生临时矩阵;`np.linalg.multi_dot([A, B, C])` 自动选最优结合顺序
- 大数组反复切片产生拷贝是内存杀手,能用视图用视图(注意视图的共享语义)

## 🧮 核心 API 速查

| 任务 | API | 说明 |
|------|-----|------|
| 计时 | `timeit.timeit(stmt, number=)` | 多次取最优,适合微基准 |
| 计时 | `time.perf_counter()` | 高精度墙钟,适合代码块 |
| 向量点积 | `x @ x` / `np.dot` | 求和平方的最快写法 |
| 矩阵链乘 | `np.linalg.multi_dot([A, B, C])` | 自动优化结合顺序 |
| 广义求和 | `np.einsum("ij,jk->ik", A, B)` | 无临时数组的灵活张量运算 |
| JIT 编译 | `from numba import njit; @njit(cache=True)` | 缓存编译结果 |
| 并行循环 | `from numba import prange; @njit(parallel=True)` | 无依赖循环并行化 |
| in-place | `a += b` / `np.add(a, b, out=a)` | 不产生新数组 |
| 视图 | `a[::2]` / `a.T` | 零拷贝,注意共享 |
| 内存占用 | `a.nbytes` / `a.dtype` | 评估内存成本 |

## 💡 经典例题

### 例题 1:蒙特卡洛估算 π 的三版对比(循环 → NumPy → Numba)

> 用投点法估算 $\pi$:向单位正方形随机投 $n$ 个点,落入四分之一圆的比例 $\times 4$ 即 $\pi$。请用纯循环、NumPy 向量化、Numba 三种实现,实测耗时并互验结果。

**代码**:

```python
import numpy as np
import timeit
from numba import njit


def mc_pi_loop(n, rng):
    inside = 0
    for _ in range(n):
        x, y = rng.random(), rng.random()
        if x * x + y * y <= 1.0:
            inside += 1
    return 4.0 * inside / n


def mc_pi_numpy(n, rng):
    x = rng.random(n)
    y = rng.random(n)
    return 4.0 * np.mean(x * x + y * y <= 1.0)


@njit
def mc_pi_numba(n, rng):
    inside = 0
    for _ in range(n):
        x, y = rng.random(), rng.random()
        if x * x + y * y <= 1.0:
            inside += 1
    return 4.0 * inside / n


rng = np.random.default_rng(0)
n = 300_000
print("纯循环:", mc_pi_loop(n, rng))
print("NumPy :", mc_pi_numpy(n, rng))
print("Numba :", mc_pi_numba(n, rng))  # 首次调用含编译

for name, f in [("纯循环", mc_pi_loop), ("NumPy", mc_pi_numpy), ("Numba", mc_pi_numba)]:
    t = timeit.timeit(lambda: f(n, rng), number=3) / 3
    print(f"{name}: 单次 {t * 1000:.2f} ms")
```

**输出解读**(数值依机器而异,比例是重点):

```
纯循环: 3.141...
NumPy : 3.139...
Numba : 3.142...
纯循环: 单次 152.7 ms
NumPy : 单次 2.2 ms
Numba : 单次 0.9 ms
```

三个结论:①**同一算法、同一结果**,三种实现估算值一致(蒙特卡洛误差 $O(1/\sqrt{n})$,每次运行的随机结果略有不同);②NumPy 比纯循环快约 70 倍,原因在《Python科学计算入门》单元讲过:循环开销 + C 层批量运算;③Numba 把**同样的循环代码**编译成机器码,比 NumPy 还快 2~3 倍,而且不用想广播——**当你必须写循环时,Numba 就是答案**。注意第一次调用 `mc_pi_numba` 含编译时间,基准测试要预热后再测。

### 例题 2:距离矩阵:双重循环 → 广播 → Numba

> 计算 $n$ 个二维点两两之间的欧氏距离矩阵 $D_{ij} = \|x_i - x_j\|_2$。先用双重循环实现,再用广播向量化与 Numba 重写,验证三种实现结果一致并对比耗时。

**代码**:

```python
import numpy as np
import timeit
from numba import njit

rng = np.random.default_rng(0)
X = rng.normal(size=(300, 2))


def dist_loop(X):
    n = X.shape[0]
    D = np.empty((n, n))
    for i in range(n):
        for j in range(n):
            D[i, j] = np.sqrt(((X[i] - X[j]) ** 2).sum())
    return D


def dist_vec(X):
    diff = X[:, None, :] - X[None, :, :]  # 广播成 (n, n, 2)
    return np.sqrt((diff**2).sum(axis=2))


@njit
def dist_numba(X):
    n = X.shape[0]
    D = np.empty((n, n))
    for i in range(n):
        for j in range(n):
            dx = X[i, 0] - X[j, 0]
            dy = X[i, 1] - X[j, 1]
            D[i, j] = (dx * dx + dy * dy) ** 0.5
    return D


print(
    "三种实现一致:",
    np.allclose(dist_loop(X), dist_vec(X)) and np.allclose(dist_loop(X), dist_numba(X)),
)

for name, f in [("双重循环", dist_loop), ("广播向量化", dist_vec), ("Numba", dist_numba)]:
    t = timeit.timeit(lambda: f(X), number=3) / 3
    print(f"{name}: {t * 1000:.2f} ms")
```

**输出解读**(数值依机器而异):

```
三种实现一致: True
双重循环: 172 ms
广播向量化: 1.4 ms
Numba: 0.1 ms
```

三重教训:①双重循环慢的原因不是循环本身,而是**循环内每次迭代都调用小粒度 NumPy 函数**(90 000 次碎片化调用);②广播一行 `X[:, None, :] - X[None, :, :]` 生成 (300, 300, 2) 的差矩阵,把整个计算下沉到 C 层——但注意它是 $O(n^2 d)$ **内存**,$n$ 很大时(如 5000 点 → 5000×5000×2×8 字节 ≈ 400 MB)会爆内存,此时换分块计算或 Numba 循环;③Numba 版本保留了循环结构、内存 $O(n^2)$,速度还最快——**内存与速度的取舍要按数据规模决策**。

### 例题 3:Numba 加速参数扫描(SIR 传染病模拟)

> 传染病模型 SIR 的离散模拟:每天新增感染 $\Delta I = \beta S I / N$,恢复 $\Delta R = \gamma I$。请在 2000 组 $(\beta, \gamma)$ 参数下各模拟 5000 天,对比纯 Python 与 Numba 的总耗时,并找出最终感染规模最大的参数组合。

**代码**:

```python
import numpy as np
import timeit
from numba import njit


def sir_final(beta, gamma, days, S0=9999.0, I0=1.0):
    S, I, R = S0, I0, 0.0
    N = S0 + I0
    for _ in range(days):
        new_inf = beta * S * I / N
        new_rec = gamma * I
        S, I, R = S - new_inf, I + new_inf - new_rec, R + new_rec
    return R


@njit
def sir_final_nb(beta, gamma, days, S0=9999.0, I0=1.0):
    S, I, R = S0, I0, 0.0
    N = S0 + I0
    for _ in range(days):
        new_inf = beta * S * I / N
        new_rec = gamma * I
        S -= new_inf
        I += new_inf - new_rec
        R += new_rec
    return R


rng = np.random.default_rng(1)
params = rng.uniform([0.05, 0.02], [0.8, 0.3], size=(2000, 2))  # (β, γ)


def scan(f):
    return np.array([f(b, g, 5000) for b, g in params])


print("纯 Python 结果前 3:", scan(sir_final)[:3].round(1))
print("Numba 结果前 3:  ", scan(sir_final_nb)[:3].round(1))

scan(sir_final_nb)  # 预热:触发 JIT 编译,别把编译时间算进基准
t_py = timeit.timeit(lambda: scan(sir_final), number=1)
t_nb = timeit.timeit(lambda: scan(sir_final_nb), number=1)
print(f"纯 Python: {t_py:.2f} s | Numba: {t_nb:.2f} s | 加速 {t_py / t_nb:.0f} 倍")

R_all = scan(sir_final_nb)
i = int(np.argmax(R_all))
print(f"最终感染规模最大的参数: β={params[i, 0]:.2f}, γ={params[i, 1]:.2f}, R={R_all[i]:.0f}")
```

**输出解读**(数值依机器而异):

```
纯 Python 结果前 3: [6028.4 2.2 8178.9]
Numba 结果前 3:   [6028.4 2.2 8178.9]
纯 Python: 2.7 s | Numba: 0.15 s | 加速 18 倍
最终感染规模最大的参数: β=0.73, γ=0.03, R=10000
```

这个例子是竞赛的**真实场景**:参数敏感性分析 = 同样的模拟在参数网格上重复成千上万次(2000 组 × 5000 天 = $10^7$ 次迭代)。要点:①`scan` 函数把「循环调用」与「单次模拟」解耦,`f` 换成 `@njit` 版本就完成加速,**业务逻辑零改动**——这是 Numba 最大的工程价值;②计时前必须预热(`scan(sir_final_nb)` 先跑一次触发编译),否则编译时间混进基准,得出「Numba 反而慢」的假象——这正是本单元易错点第 3 条的实战演示;③模拟结果两者逐位一致(确定性计算),换算法不换答案;④结果解读:$\beta$ 大、$\gamma$ 小(传染力强、康复慢)时疫情饱和,最终感染规模最大($R = 10000$,全员感染)——这种「全参数扫描 + 取最优」的模式,在美赛传染病题、国赛评价类题目中反复出现。

## ⚠️ 常见易错点

1. **不测量就优化**。花两小时把一个占 1% 运行时间的函数提速 10 倍,总收益 0.9%;先用计时(或 cProfile)定位真正的热点,再动手
2. **把 `np.vectorize` 当加速器**。它只是循环的语法糖,甚至因类型转换更慢;要么真向量化(广播/ufunc),要么上 Numba
3. **忽略 Numba 的首次编译**。小任务、单次调用时 `@njit` 反而更慢;基准测试必须先预热一次再计时,生产用法加 `cache=True`
4. **Numba 里写它不支持的 Python**。类方法、字符串处理、混合类型 list 会编译失败或回退 object 模式(极慢);报错就把这部分逻辑移出 `@njit` 函数,保持函数「纯数值」
5. **微优化掩盖算法问题**。双重循环里抠常数(局部变量、位运算)不如把 $O(n^2)$ 换成 $O(n\log n)$;复杂度层级的收益是数量级的
6. **内存泄漏式切片拷贝**。大数组上反复 `a[1:]`、`a.T.copy()` 产生海量临时数组;能用视图用视图、能 in-place 就 in-place、注意 `multi_dot`/`einsum` 减少临时矩阵

## ✏️ 自测练习(选择题)

**第 1 题** 关于 `np.vectorize(f)`,下列说法正确的是:

A. 是语法糖:内部仍是 Python 层循环,不加速甚至更慢
B. 与 Numba 的 @njit 等价,都是 JIT 编译
C. 会自动利用多核并行加速
D. 只能作用于 numpy 的 ufunc

<details><summary>查看答案与解析</summary>
**答案:A**。`np.vectorize` 只是把函数调用「循环」包了一层语法糖:内部仍是 Python 层的逐元素调用,加上类型转换开销,往往比直接循环还慢——它**不是**加速器。它的价值是语义糖:让标量函数接受数组输入、支持广播,方便书写。要性能只有两条路:真向量化(把计算写进 NumPy 的广播/ufunc,让运算发生在 C 层),或必须写循环时用 Numba 的 @njit 编译。它也不是并行工具,不限于 ufunc。
</details>

**第 2 题** 给函数加 `@njit` 后,第一次调用明显比后续调用慢,原因是:

A. 首次调用要初始化 GPU
B. 是 Numba 的 bug,第二次才会正常
C. 首次调用含 JIT 编译时间;基准测试应先预热一次再计时
D. 首次调用包含 Python 解释器启动开销

<details><summary>查看答案与解析</summary>
**答案:C**。第一次调用时 Numba 把 Python 函数**编译**成机器码(约 0.1~1 秒),之后直接执行机器码。不同参数**类型**(如 float64 数组 vs int64 数组)还会触发不同的编译版本。因此基准测试必须「先预热一次再计时」,否则编译时间混进基准,得出「Numba 反而慢」的假象;生产代码加 `@njit(cache=True)` 把编译结果缓存到磁盘。小数据量、单次调用时 @njit 也可能因编译开销反而更慢。
</details>

**第 3 题** 某段双重循环代码复杂度为 $O(n^2)$,用 Numba 可加速约 50 倍;同时存在 $O(n\log n)$ 的替代算法。
$n = 10^5$ 时,最优策略是:

A. 直接用 Numba 加速现有代码即可,50 倍已足够
B. 优先换 O(n log n) 算法:复杂度收益是数量级的(n²/(n log n) ≈ 6000 倍,远超 50 倍)
C. 两者收益相当,任选其一
D. 先做常数级微调(局部变量、缓存属性),不够再改算法

<details><summary>查看答案与解析</summary>
**答案:B**。复杂度差异是数量级的:$n^2 = 10^{10}$ 对 $n\log_2 n \approx 1.7\times 10^6$,差距约 6000 倍,远超 Numba 的 50 倍常数级收益——把一个 O(n²) 双重循环用 Numba 加速,不如改成 O(n log n) 算法快。常数级微调(局部变量、in-place)只有 1~3 倍,且往往牺牲可读性。优化顺序:先测量定位热点 → 降复杂度(算法/数据结构)→ 向量化或 JIT → 最后才常数级微调。
</details>

## 🏆 竞赛实战链接

- **出镜频率**:三天赛程里「跑一次要 3 小时」的仿真/扫描是常见事故;蒙特卡洛模拟、参数网格扫描、大规模数据处理是三大提速刚需
- **论文加分点**:论文或附录中给出「优化前后耗时对比表」(如本单元例题的格式),并说明采用了向量化/Numba 技术——既展示工程能力,也回应「结果是否可复现」
- **实战组合**:先 NumPy 向量化(零依赖),不够再 Numba(一行装饰器),仍不够再考虑并行(`prange`)或 Cython;竞赛环境通常禁止超算,单机多核要榨干
- **参考线**:复杂仿真单次运行控制在 10 分钟以内,才能在赛程内完成灵敏度分析所需的上百次运行

## 💻 代码实现

性能优化的标准流程模板(测量 → 向量化 → JIT → 验证):

```python
import numpy as np
import timeit
from numba import njit

rng = np.random.default_rng(0)
data = rng.normal(size=1_000_000)


# 0. 基线:纯循环
def baseline(x):
    s = 0.0
    for v in x:
        s += v * v
    return s


# 1. 向量化
def vectorized(x):
    return x @ x


# 2. JIT 编译
@njit
def jitted(x):
    s = 0.0
    for v in x:
        s += v * v
    return s


print(
    "结果一致:",
    np.allclose(baseline(data), vectorized(data)) and np.allclose(baseline(data), jitted(data)),
)
for name, f in [("纯循环", baseline), ("向量化", vectorized), ("Numba", jitted)]:
    t = timeit.timeit(lambda: f(data), number=10) / 10
    print(f"{name}: {t * 1000:.2f} ms")
```

## 📚 延伸阅读

- **官方文档**:Numba 5 分钟指南(https://numba.readthedocs.io/en/stable/user/5minguide.html)— 支持/不支持特性的速查表
- **测速工具**:Python 标准库 cProfile(`python -m cProfile script.py`)做函数级剖析;line_profiler 看行级热点
- **进阶**:Cython 基础教程(https://cython.readthedocs.io/)——静态编译的最终手段;`np.einsum` 与 `numba` 的 `prange` 并行文档
- **姊妹单元**:《NumPy数组操作实战》(广播是向量化的基本功)→ 本单元 → 《建模数据处理流水线》(工程化)

## 🧠 小结

1. 优化第一定律:**先测量**(timeit/perf_counter/cProfile),再动手;没有数据的优化是玄学
2. 层级顺序:算法复杂度($O(n^2)\to O(n\log n)$,数量级收益)> 向量化(下沉到 C 层,10~100 倍)> Numba(循环编译,10~100 倍)> 常数级微调(1~3 倍)
3. `np.vectorize` 是语法糖不是加速器;真向量化 = 广播 + ufunc + 整块运算
4. Numba 的工程价值:循环代码原样加速、业务逻辑零改动;注意预热、`cache=True`、只写纯数值子集
5. 内存也是性能:视图不拷贝但共享、in-place 省临时数组、`multi_dot`/`einsum` 减中转——别让内存带宽拖后腿
