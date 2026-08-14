# NumPy数组操作实战

> **难度**:入门 · **预计学习时长**:30 分钟 · **主讲智能体**:🧩 求解器 · **方法类别**:编程工具

## 🎯 学习目标

本单元是练习型单元。学完后,你应该能够:

- 熟练用 `reshape` / `stack` / `concatenate` 变换数组形状
- 掌握切片、布尔索引、花式索引三种索引方式,并知道何时用哪种
- 理解广播的三条规则,能预测 `(3,1) + (4,)` 这类运算的结果形状
- 正确使用 `axis` 参数沿行/列做聚合统计
- 用 `numpy.linalg` 解线性方程组、求特征值与奇异值分解

## 📖 核心概念

### 1. 形状:数组的「世界观」

每个 ndarray 有三个基本属性:`shape`(各维长度)、`ndim`(维数)、`dtype`(元素类型)。

```python
import numpy as np

a = np.arange(24).reshape(4, 6)  # 4×6 矩阵,元素 0~23
print(a.shape, a.ndim, a.dtype)  # (4, 6) 2 int64(或 int32,依平台)

b = a.reshape(-1, 3)  # -1 表示「自动推算」:24/3 = 8 行
c = a.T  # 转置:6×4
d = a[:, :, np.newaxis]  # 末尾加一轴:4×6×1
print(b.shape, c.shape, d.shape)
```

**小练习 1**:写出把形状 (2, 3, 4) 的数组变成 (6, 4) 的一行代码。

<details><summary>查看答案</summary>

`arr.reshape(6, 4)` 或 `arr.reshape(-1, 4)`。注意 reshape 的「行主序」展开顺序:(2,3,4) 按最内层维度最快变化展开为 24 个元素,再按 (6,4) 重新打包。

</details>

### 2. 三种索引方式

```python
import numpy as np

rng = np.random.default_rng(1)
a = rng.integers(-5, 6, size=(5, 5))  # 5×5 的 -5~5 随机整数

# (1) 基础切片:视图!与原数组共享内存
sub = a[1:3, 2:4]
sub[:] = 999  # 修改切片会同步修改原数组
print("切片赋值后 a[1:3,2:4] 全为 999:", (a[1:3, 2:4] == 999).all())

# (2) 布尔索引:返回一维数组
pos = a[a > 0]
print("正元素个数:", pos.size)

# (3) 花式索引:按下标列表取行/列
rows = a[[0, 2, 4]]  # 取第 0、2、4 行
print("花式索引取行后形状:", rows.shape)
```

**小练习 2**:`a[a > 0] = -1` 与 `pos = a[a > 0]; pos[:] = -1` 效果相同吗?

<details><summary>查看答案</summary>

不同。`a[a > 0] = -1` 是直接对原数组的布尔掩码赋值,会修改 `a`;而 `pos = a[a > 0]` 得到的是一份**拷贝**,修改 `pos` 不影响 `a`。布尔索引取元素总是拷贝,基础切片才是视图——这是两者最关键的差异。

</details>

### 3. 广播:三条规则

NumPy 从**尾部**开始逐维比较两个数组的形状:

1. 两维长度相等 → 兼容
2. 一方长度为 1 → 拉伸复制到与另一方相同
3. 一方缺失(维数少)→ 视作长度为 1 参与比较;都不满足 → 报错

```python
import numpy as np

A = np.arange(12).reshape(3, 4)  # (3,4)
v = np.array([10, 20, 30, 40])  # (4,) → 视作 (1,4) → 广播为 (3,4)
print(A + v)  # 每一行都加上 v

col = np.array([[1], [2], [3]])  # (3,1) → 广播为 (3,4)
print((col + A).shape)  # (3,4),每一列加对应数
```

**小练习 3**:不运行代码,预测 `np.ones((3, 1)) + np.arange(4)` 的结果形状,再验证。

<details><summary>查看答案</summary>

`(3,1)` 与 `(4,)`(视作 (1,4)):尾部对齐后 1 对 4 → 拉伸为 4;3 对 1 → 拉伸为 3。结果是 **$(3,4)$** 的矩阵,第 $i$ 行第 $j$ 列元素为 $1 + j$。这是广播最容易让人意外的情形:两个向量相加得到的是矩阵而不是向量。

</details>

### 4. 沿轴聚合:axis 的含义

`axis` 指定的是**被压缩掉的那根轴**:

```python
import numpy as np

X = np.arange(1, 13).reshape(3, 4)
print("原矩阵:\n", X)
print("axis=0 求和(压掉行,得每列之和):", X.sum(axis=0))  # [15 18 21 24]
print("axis=1 求和(压掉列,得每行之和):", X.sum(axis=1))  # [10 26 42]
print("全局最大值位置(展平后下标):", X.argmax())  # 11
```

### 5. 常用线性代数:np.linalg

```python
import numpy as np

A = np.array([[2.0, 1.0], [1.0, 3.0]])
b = np.array([5.0, 10.0])

x = np.linalg.solve(A, b)  # 解 Ax = b
print("方程组的解:", x)  # [1. 3.]
print("验证 A@x - b:", A @ x - b)  # [0. 0.]

vals, vecs = np.linalg.eig(A)  # 特征值分解
print("特征值:", vals.round(3))
print("行列式:", np.linalg.det(A))  # 5.0
```

## 🧮 核心 API 速查

| 操作 | API | 说明 |
|------|-----|------|
| 形状变换 | `reshape` / `ravel` / `T` / `np.newaxis` | 重塑 / 展平 / 转置 / 加轴 |
| 拼接 | `np.concatenate` / `np.stack` / `np.vstack` / `np.hstack` | 沿轴拼接 / 新轴堆叠 |
| 重复与平铺 | `np.tile` / `np.repeat` | 整块复制 / 逐元素重复 |
| 索引 | `arr[i:j]` / `arr[mask]` / `arr[[i,j,k]]` | 切片(视图)/ 布尔 / 花式(拷贝) |
| 聚合 | `sum(axis=)` / `cumsum` / `np.percentile` | 求和 / 累加 / 分位数 |
| 查找 | `np.where` / `np.argmax` / `np.unique` | 条件定位 / 最值下标 / 去重 |
| 比较 | `np.isclose` / `np.allclose` | 浮点近似相等 |
| 线性代数 | `np.linalg.solve` / `inv` / `eig` / `svd` | 解方程 / 求逆 / 特征值 / 奇异值 |

## 💡 经典例题

### 例题 1:图像矩阵操作(切片实战)

> 用随机矩阵模拟一张 8×12 的灰度图(取值 0~255),完成:上下翻转、左右翻转、隔行隔列降采样到 4×6,并验证翻转的对称性。

**代码**:

```python
import numpy as np

rng = np.random.default_rng(7)
img = rng.integers(0, 256, size=(8, 12))  # 8×12 灰度图

flip_ud = img[::-1, :]  # 行序反转 = 上下翻转
flip_lr = img[:, ::-1]  # 列序反转 = 左右翻转
down = img[::2, ::2]  # 隔行隔列降采样

print("原图形状:", img.shape, "→ 降采样后:", down.shape)
print("上下翻转 (0,0) 是否等于原图 (7,0):", flip_ud[0, 0] == img[7, 0])
print("左右翻转 (0,0) 是否等于原图 (0,11):", flip_lr[0, 0] == img[0, 11])
print("再翻转一次回到原图:", (flip_ud[::-1, :] == img).all())
```

**输出解读**:

```
原图形状: (8, 12) → 降采样后: (4, 6)
上下翻转 (0,0) 是否等于原图 (7,0): True
左右翻转 (0,0) 是否等于原图 (0,11): True
再翻转一次回到原图: True
```

负步长切片 `[::-1]` 是 NumPy 处理翻转、倒序的最高效方式——不移动任何数据,只改变读取方向。美赛 C 题经常给网格化/图像化数据(地形高程、卫星影像),「切片 + 降采样」就是处理它们的第一步。

### 例题 2:广播按列标准化(数据预处理)

> 某赛事给出 40 个城市 4 项指标的数据矩阵 $X$(40×4),指标量纲差异巨大(见代码)。请做 Z-score 标准化:每列减去列均值、除以列标准差,并验证标准化后各列均值约为 0、标准差约为 1。

**代码**:

```python
import numpy as np

rng = np.random.default_rng(3)
# 4 列指标:量纲分别为 十、百、个位、三百(显式按列生成)
locs = np.array([50, 200, 8, 300])
scales = np.array([10, 40, 2, 60])
X = rng.normal(size=(40, 4)) * scales + locs  # (40,4) * (4,) 广播

mu = X.mean(axis=0)  # 各列均值,形状 (4,)
sigma = X.std(axis=0)  # 各列标准差,形状 (4,)
Z = (X - mu) / sigma  # 广播:(40,4) - (4,) → (40,4)

print("列均值:", mu.round(2))
print("列标准差:", sigma.round(2))
print("标准化后各列均值:", Z.mean(axis=0).round(12))  # 全 0
print("标准化后各列标准差:", Z.std(axis=0).round(12))  # 全 1
```

**输出解读**:

```
列均值: [ 49.13 201.67   8.27 290.43]
列标准差: [11.88  46.12   1.93  48.69]
标准化后各列均值: [0. 0. 0. 0.]
标准化后各列标准差: [1. 1. 1. 1.]
```

标准化公式即 $z_{ij} = \dfrac{x_{ij} - \mu_j}{\sigma_j}$。若没有广播,你需要双重循环逐列计算;有了广播,一行 `(X - mu) / sigma` 完成——这正是「向量化思维」的体现。Z-score 标准化是聚类、主成分分析等一切距离型方法的前置步骤(参见《sklearn机器学习实战》单元)。

### 例题 3:布尔索引与异常值修复(传感器数据清洗)

> 某气象站温度传感器每分钟记录一次,共 1440 条(一天)。数据含 12 个人为注入的异常尖峰(幅度 +40)。请用 $3\sigma$ 准则检出异常,并用「前向填充」(用最近的上一个正常值替代)修复,最后对比修复前后的最大值与标准差。

**代码**:

```python
import numpy as np

rng = np.random.default_rng(11)
t = np.linspace(0, 24, 1440, endpoint=False)
temp = 20 + 8 * np.sin(2 * np.pi * t / 24) + rng.normal(0, 0.8, 1440)
temp[rng.integers(0, 1440, 12)] += 40  # 注入 12 个异常尖峰

mu, sd = temp.mean(), temp.std()
mask = np.abs(temp - mu) > 3 * sd  # 布尔掩码:True = 异常
print(f"检出异常 {mask.sum()} 个")

# 向量化前向填充:记录每个位置「最近的上一个有效下标」
temp2 = np.concatenate([[mu], temp])  # 头部垫一个均值,处理开头即异常
valid = np.concatenate([[True], ~mask])  # 垫子视为有效
pos = np.where(valid, np.arange(1441), 0)
fixed = temp2[np.maximum.accumulate(pos)][1:]  # 去掉垫子

print(f"修复前: 最大值 {temp.max():.1f}, 标准差 {temp.std():.3f}")
print(f"修复后: 最大值 {fixed.max():.1f}, 标准差 {fixed.std():.3f}")
print("非异常位置未被改动:", (fixed[~mask] == temp[~mask]).all())
```

**输出解读**:

```
检出异常 12 个
修复前: 最大值 51.2, 标准差 6.147
修复后: 最大值 28.6, 标准差 5.730
非异常位置未被改动: True
```

三个要点:①`np.abs(temp - mu) > 3 * sd` 是典型的掩码构造;②`np.maximum.accumulate(pos)` 把「最近有效下标」一路传播下去,实现了**无循环**的前向填充;③最后一行验证修复只动了异常点——数据清洗必须保证「不误伤正常数据」,这行断言写进论文非常加分。

## ⚠️ 常见易错点

1. **切片是视图,布尔索引是拷贝**。`sub = a[1:3]; sub[:] = 0` 会改原数组;`pos = a[a > 0]` 修改 `pos` 不影响 `a`。需要独立副本时显式 `.copy()`
2. **布尔条件组合忘记括号**。必须写 `(a > 0) & (a < 5)`,`a > 0 and a < 5` 会直接报错(`and` 不能作用于数组),`a > 0 & a < 5` 则因优先级先算 `0 & a` 而语义全错
3. **广播形状预测错**。`(3,) + (3,1)` 的结果是 (3,3) 而不是 (3,);「维数少的一侧补 1」这条规则最容易被忽略。拿不准时先 `np.broadcast_shapes((3,), (3,1))` 查一下
4. **axis 方向搞反**。`X.sum(axis=0)` 是「压掉第 0 轴」得到**每列**之和,不是每行;口诀:axis 指向被消掉的那根轴
5. **reshape 总元素数不对**。reshape 前先 `arr.size` 核对;`-1` 占位虽然方便,但会掩盖「元素数对不上」的真实 bug
6. **浮点数用 `==` 判等**。`0.1 + 0.2 == 0.3` 是 False;数组比较用 `np.isclose(a, b, atol=1e-8)` 或 `np.allclose`
7. **布尔索引返回一维数组**。`a[mask]` 丢掉形状信息,后续做矩阵运算前先想清楚是否需要 `a[mask].reshape(...)` 或改用 `np.where`

## ✏️ 自测练习(选择题)

**第 1 题**

```python
import numpy as np

a = np.arange(10)
b = a[3:7]
b[0] = 99
print(a)
```

输出是:

A. [ 0  1  2 99  4  5  6  7  8  9]
B. [ 0  1  2  3  4  5  6  7  8  9]
C. [ 0  1  2  3 99  5  6  7  8  9]
D. 报错:视图对象不可赋值

<details><summary>查看答案与解析</summary>
**答案:A**。基础切片返回的是**视图**,与原数组共享内存:`b[0]` 就是 `a[3]`,改成 99 后原数组同步变化。[0 1 2 3 4 5 6 7 8 9] 是以为切片返回拷贝(布尔/花式索引才是拷贝);[0 1 2 3 99 ...] 是把 `b[0]` 误当成了 `a[4]`;视图当然可以赋值——这正是「视图陷阱」危险的地方。需要独立副本时显式 `b = a[3:7].copy()`。
</details>

**第 2 题**

```python
import numpy as np

X = np.arange(1, 13).reshape(3, 4)
print(X.sum(axis=0))
```

输出是:

A. [10 26 42]
B. 78
C. [15 18 21 24]
D. [6 15 24 33]

<details><summary>查看答案与解析</summary>
**答案:C**。axis 指向**被压缩掉的那根轴**:axis=0 压掉行轴,得到每一列之和 1+5+9=15、2+6+10=18、3+7+11=21、4+8+12=24。[10 26 42] 是 axis=1(每行之和),axis 方向搞反是最常见错误;78 是全局总和(不指定 axis);[6 15 24 33] 是把矩阵误想成 4×3 布局的列和。口诀:axis=0 沿行方向压缩(得列统计),axis=1 沿列方向压缩(得行统计)。
</details>

**第 3 题**

```python
import numpy as np

r = np.ones((3, 1)) + np.arange(4)
print(r.shape)
```

输出是:

A. 报错:形状不兼容
B. (1, 4)
C. (3,)
D. (3, 4)

<details><summary>查看答案与解析</summary>
**答案:D**。广播从尾部对齐:(3,1) 与 (4,)——维数少的 (4,) 先补成 (1,4),再逐维比较:3 对 1 → 拉伸为 3;1 对 4 → 拉伸为 4。结果是 (3,4) 的矩阵,第 i 行第 j 列元素为 1 + j。这是广播最容易让人意外的情形:两个向量相加得到的是**矩阵**。(3,)/(1,4) 都是只拉伸一边的错误预期;报错是把规则记成了「维度必须完全相等」。拿不准时用 `np.broadcast_shapes((3,1), (4,))` 直接查。
</details>

## 🏆 竞赛实战链接

- **出镜频率**:国赛数据处理题(A/C 题)里,附件数据的读入后第一步永远是 NumPy 数组化与形状核对;美赛 C 题的网格数据、B 题的图像数据都依赖切片与广播
- **论文加分点**:①数据预处理步骤用「处理前后统计量对比表」展示(如例题 3 的修复前后对比);②涉及矩阵计算的模型(层次分析法、灰色预测、PCA)在附录附矩阵运算代码
- **工具**:数组调试三连——`print(arr.shape)`、`print(arr.dtype)`、`print(arr[:3])`,解决一半以上的形状错误

## 💻 代码实现

本单元全部技巧的汇总示例(建议逐行运行观察输出):

```python
import numpy as np

rng = np.random.default_rng(42)
A = rng.normal(size=(4, 5))  # 4×5 随机矩阵

# 形状变换
print("形状:", A.shape, "→", A.reshape(5, 4).shape, "→", A.T.shape)

# 拼接:行方向与列方向
B = np.concatenate([A, A[:, :2]], axis=1)  # (4,7)
C = np.stack([A[0], A[1]], axis=0)  # (2,5)
print("拼接后:", B.shape, C.shape)

# 索引三件套
print("子矩阵:", A[1:3, 0:2])  # 基础切片(视图)
print("布尔:", A[A > 1.5])  # 布尔索引(拷贝,一维)
print("花式:", A[[3, 0], :].shape)  # 花式索引(拷贝)

# 广播与聚合
print("按列标准化:\n", (A - A.mean(axis=0)) / A.std(axis=0))
print("每行最大值:", A.max(axis=1))

# 线性代数
ATA = A.T @ A
print("A^T A 的特征值(全非负,半正定):", np.linalg.eigvalsh(ATA).round(3))
```

## 📚 延伸阅读

- **官方文档**:NumPy Broadcasting 规则(https://numpy.org/doc/stable/user/basics.broadcasting.html)— 广播讲得最权威
- **练习库**:numpy-100(https://github.com/rougier/numpy-100)— 100 道由浅入深的练习题,建议做完前 60 题
- **进阶关联**:学完本单元 → 《Pandas数据处理》(表格化数据)→ 《代码性能优化》(把循环改写成广播/Numba)

## 🧠 小结

1. 形状是 NumPy 的第一公民:写任何运算前先问「两边 shape 是多少,广播后是多少」
2. 索引三件套各有语义:切片是视图、布尔/花式是拷贝;赋值时「视图陷阱」最隐蔽
3. 广播三规则从尾部对齐:相等兼容、1 可拉伸、缺失补 1;拿不准就用 `np.broadcast_shapes` 验证
4. `axis` 指向被压缩的轴:`axis=0` 压掉行得列统计,`axis=1` 压掉列得行统计;`keepdims=True` 保留维度以利广播
5. 本单元的每一个小练习都值得亲手敲一遍——NumPy 操作是肌肉记忆,练得越多,赛场上留给建模思考的时间就越多
