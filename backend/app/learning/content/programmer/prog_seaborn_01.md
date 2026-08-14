# Seaborn高级可视化

> **难度**:进阶 · **预计学习时长**:35 分钟 · **主讲智能体**:🧩 求解器 · **方法类别**:编程工具

## 🎯 学习目标

学完本单元,你应该能够:

- 理解 Seaborn 与 Matplotlib 的关系:统计图层 vs 底层绘图
- 用 `heatmap` 画相关系数矩阵,用 `pairplot` 快速探索多维特征关系
- 用箱线图/小提琴图对比多组数据的分布
- 区分 figure-level(`relplot`/`catplot`/`pairplot`)与 axes-level 函数的使用差异
- 把 Seaborn 图形无缝嵌入 Matplotlib 的 OO 工作流,产出论文级统计图

## 📖 核心概念

### 1. Seaborn 是什么

Seaborn 构建在 Matplotlib 之上:**统计图层的快捷方式**。Matplotlib 提供「像素级」控制,Seaborn 提供「统计语义」——把 DataFrame 的列直接映射为图形元素,一行代码出带置信区间的回归线、分组分布图。两者不是替代关系,而是配合:

```python
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

sns.set_theme(style="whitegrid", context="paper")  # 全局风格
data = np.random.default_rng(0).normal(size=1000)
fig, ax = plt.subplots(figsize=(7, 4.5))
sns.histplot(x=data, ax=ax)  # seaborn 画,ax 仍是 matplotlib 对象
ax.set_xlabel("数值")
ax.set_title("分布直方图")
fig.savefig("hist.png", dpi=200)
```

所有 axes-level 函数都接受 `ax=` 参数——Seaborn 画内容,Matplotlib 管排版,这就是正确的心智模型。

### 2. 两类函数:figure-level vs axes-level

| | axes-level | figure-level |
|------|------|------|
| 例子 | `scatterplot` / `boxplot` / `histplot` | `relplot` / `catplot` / `pairplot` |
| 返回 | `ax`(Matplotlib 坐标轴) | `FacetGrid` / `PairGrid` 对象 |
| 特点 | 传 `ax=` 嵌入现有画布 | 自带分面(按类别分多个子图) |
| 修改细节 | `ax.set_xxx` | `g.set_axis_labels(...)`、`g.tight_layout()` |

### 3. 数据要求:整洁长表(Tidy Data)

Seaborn 的威力来自**列名映射**:每列一个变量,每行一条观测,「按某列分组着色/分面」都是参数级操作,不需要手动拆数据。这正是 Pandas 清洗后数据的天然形态(参见《Pandas数据处理》单元)。

### 4. 统计图四件套

- **分布**:`histplot`(直方图)、`kdeplot`(核密度估计,平滑版的直方图)
- **关系**:`scatterplot`、`regplot`(散点 + 回归线 + 置信带)、`pairplot`(全特征两两关系矩阵)
- **分组对比**:`boxplot`(箱线图:中位数 + 四分位 + 异常点)、`violinplot`(小提琴图:分布形状 + 箱线)、`swarmplot`(蜂群散点)
- **矩阵**:`heatmap`(相关系数矩阵、混淆矩阵的可视化)

## 🧮 核心 API 速查

| 任务 | API | 关键参数 |
|------|-----|------|
| 全局风格 | `sns.set_theme(style=, context=)` | `style`: darkgrid/whitegrid/ticks;`context`: paper/notebook/talk |
| 热力图 | `sns.heatmap(df, annot=, fmt=, cmap=, center=, ax=)` | `center=0` 适合相关系数矩阵 |
| 散点矩阵 | `sns.pairplot(df, hue=, diag_kind=, corner=)` | `diag_kind="kde"` 对角放密度 |
| 散点 | `sns.scatterplot(data=df, x=, y=, hue=)` | `hue` 分组着色 |
| 回归线 | `sns.regplot(data=df, x=, y=)` | 自动加置信带 |
| 箱线图 | `sns.boxplot(data=df, x=, y=, ax=)` | 分组分布对比 |
| 小提琴图 | `sns.violinplot(data=df, x=, y=, ax=)` | 保留分布形状的箱线图 |
| 直方图 | `sns.histplot(x=, bins=, kde=True)` | 旧版 `distplot` 已废弃 |
| 核密度 | `sns.kdeplot(x=, fill=True)` | 平滑密度曲线 |
| 计数图 | `sns.countplot(data=df, x=)` | 类别频数条形图 |
| 分面 | `sns.catplot / relplot(kind=, col=)` | figure-level,按 `col`/`row` 分面 |

## 💡 经典例题

### 例题 1:相关系数矩阵热力图(数据探索第一步)

> 某经济研究给出 4 项指标的 200 组观测(已知其相关结构)。请计算相关系数矩阵并绘制带标注的热力图,指出最强正相关与最强负相关的指标对。

**代码**:

```python
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

rng = np.random.default_rng(42)
cov = [[1.0, 0.8, -0.6, 0.1], [0.8, 1.0, -0.5, 0.0], [-0.6, -0.5, 1.0, 0.3], [0.1, 0.0, 0.3, 1.0]]
df = pd.DataFrame(
    rng.multivariate_normal([0, 0, 0, 0], cov, size=200),
    columns=["GDP增速", "投资", "失业率", "出口"],
)
corr = df.corr()

fig, ax = plt.subplots(figsize=(7, 5.5))
sns.heatmap(
    corr,
    annot=True,
    fmt=".2f",
    cmap="RdBu_r",
    vmin=-1,
    vmax=1,
    center=0,
    square=True,
    cbar_kws={"shrink": 0.8},
    ax=ax,
)
ax.set_title("指标相关系数矩阵")
fig.savefig("corr.png", dpi=200)
print(corr.round(2))
```

**输出解读**:

```
         GDP增速   投资  失业率   出口
GDP增速    1.00  0.87 -0.55  0.05
投资       0.87  1.00 -0.52 -0.02
失业率     -0.55 -0.52  1.00  0.29
出口       0.05 -0.02  0.29  1.00
```

设置要点:①`cmap="RdBu_r"` + `center=0` + `vmin=-1, vmax=1`——相关系数矩阵的**标准配色**,红正蓝负、0 为白色,正负一眼可辨;②`annot=True, fmt=".2f"` 把数值直接标在格子里,论文里无需再读色标;③`square=True` 使格子方正,观感更专业。结论:GDP 增速与投资强正相关(0.87),与失业率负相关(-0.55)——这张图是国赛数据分析题「指标相关性分析」小节的标配开场图。

### 例题 2:pairplot 多维特征探索(分类问题)

> 四维特征的二分类数据集。请用 pairplot 观察:哪些特征在两类间有区分度?类别间是否线性可分?

**代码**:

```python
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.datasets import make_classification

X, y = make_classification(
    n_samples=300, n_features=4, n_informative=3, n_redundant=0, random_state=0
)
df = pd.DataFrame(X, columns=[f"x{i + 1}" for i in range(4)])
df["类别"] = y.astype(str)

g = sns.pairplot(df, hue="类别", diag_kind="kde", palette=["#4C78A8", "#F58518"])
g.savefig("pair.png", dpi=200)
print("各类别样本数:", df["类别"].value_counts().to_dict())
```

**输出解读**:

```
各类别样本数: {'0': 152, '1': 148}
```

读图方法:对角线是各特征按类别的密度曲线,非对角是两两散点图。若某散点图中两类**颜色明显分区**(如 x1-x2 平面几乎不重叠),说明这两个特征组合有强区分度;若全部平面都混成一团,说明线性分类器希望渺茫。`diag_kind="kde"` 把对角线的直方图换成平滑密度曲线,重叠程度看得更清。这张图可以直接放进论文的「数据探索」小节,并为后续建模选择提供依据(选区分度高的特征、判断是否需要非线性模型,参见《sklearn机器学习实战》单元)。

### 例题 3:箱线图与小提琴图对比(方法性能评估)

> 四种预测方法各 80 次实验的得分数据(模拟)。请用箱线图与小提琴图并排展示四种方法的得分分布,回答:哪种方法中位数最高?哪种最不稳定?

**代码**:

```python
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

rng = np.random.default_rng(0)
n = 80
df = pd.DataFrame(
    {
        "方法": np.repeat(["方法A", "方法B", "方法C", "方法D"], n),
        "得分": np.concatenate(
            [
                rng.normal(72, 6, n),
                rng.normal(78, 8, n),
                rng.normal(65, 10, n),
                rng.normal(80, 5, n),
            ]
        ),
    }
)

fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
sns.boxplot(data=df, x="方法", y="得分", hue="方法", palette="pastel", legend=False, ax=axes[0])
sns.violinplot(data=df, x="方法", y="得分", hue="方法", palette="muted", legend=False, ax=axes[1])
axes[0].set_title("箱线图")
axes[1].set_title("小提琴图")
fig.tight_layout()
fig.savefig("box_violin.png", dpi=200)

summary = df.groupby("方法")["得分"].agg(["median", "std"]).round(2)
print(summary)
```

**输出解读**:

```
         median    std
方法
方法A     72.60   5.82
方法B     78.26   7.69
方法C     62.98  10.95
方法D     78.98   5.31
```

图形结论:方法 D 中位数最高(78.98)且小提琴最「瘦」(std 最小,5.31)——**既准又稳**;方法 C 中位数最低且分布最「胖」(std 10.95)——既差又不稳。箱线图适合快速比较中位数与离群点(箱外的散点就是离群值),小提琴图额外展示了分布形状(双峰、偏态都能看出来)。论文写法:「箱线图展示中位数与四分位距,小提琴图进一步刻画分布形态」——两种图互补,并排放是性能评估小节的标准构图。

## ⚠️ 常见易错点

1. **还在用 `distplot`**。seaborn 0.11 起 `distplot` 已废弃,报 DeprecationWarning;改用 `histplot`(直方图)或 `kdeplot`(密度曲线),两者可叠加
2. **figure-level 函数当 ax 用**。`pairplot`/`catplot` 返回的是 FacetGrid,`ax.set_xlabel` 会报错;改标题用 `g.fig.suptitle`,改轴标签用 `g.set_axis_labels`,保存用 `g.savefig`
3. **热力图配色不设 `center=0`**。相关系数矩阵直接默认配色,色标从数据最小值到最大值,0 不在中间——正负关系被配色误导;`center=0, vmin=-1, vmax=1` 是标配
4. **数据不是长表格式**。把宽表(每列一个组)直接传给 `boxplot`,画不出分组图;先 `melt` 成长表(一列「组名」一列「数值」),或像例题 3 那样构造
5. **中文乱码沿用旧习惯**。Seaborn 的中文支持与 Matplotlib 相同,`rcParams` 照设(见《Matplotlib数据可视化》单元);或干脆论文图用英文标签
6. **`palette` 与 `hue` 数量不匹配**。手动指定颜色数量必须 ≥ 类别数,否则报错;拿不准就用 `palette="Set2"` 之类的定性色板,交给 Seaborn 自动分配

## ✏️ 自测练习(选择题)

**第 1 题** `sns.pairplot` 返回的是 PairGrid 对象。想修改坐标轴标签,正确做法是:

A. g.set_axis_labels("x", "y")
B. g.set_xlabel("x")
C. pairplot 返回的是 ax,直接 ax.set_xlabel("x")
D. plt.xlabel("x")

<details><summary>查看答案与解析</summary>
**答案:A**。figure-level 函数(pairplot/catplot/relplot)返回 Grid 对象,**不是 ax**,改轴标签用 `g.set_axis_labels(...)`,改总标题用 `g.fig.suptitle(...)`,保存用 `g.savefig(...)`。Grid 对象没有 set_xlabel 方法,直接调用会报 AttributeError;plt.xlabel 是 pyplot 状态机写法,多子图时作用到错误对象。axes-level 函数(scatterplot/boxplot/histplot)才返回 ax,那时才用 ax.set_xlabel——两类函数先分清。
</details>

**第 2 题** 画相关系数矩阵热力图时,推荐的配色参数组合是:

A. cmap="viridis",不设 center(默认配色即可)
B. cmap="RdBu_r",center=0.5,vmin=0,vmax=1
C. 默认参数即可,相关系数自带正负
D. cmap="RdBu_r",center=0,vmin=-1,vmax=1

<details><summary>查看答案与解析</summary>
**答案:D**。相关系数矩阵的标准配色:`cmap="RdBu_r"`(红正蓝负)+ `center=0`(0 恰好落在色标中点为白色)+ `vmin=-1, vmax=1`(色标固定全量程,不同热力图之间颜色深浅可直接比较)。viridis 没有正负语义;`RdBu` 方向反了(蓝正红负),center=0.5 让 0 偏离中点;默认配色下色标从数据最小值到最大值浮动,0 不在中点,正负关系被配色误导。
</details>

**第 3 题** seaborn 0.11 之后,画直方图应该使用:

A. sns.distplot
B. sns.histplot
C. sns.kdeplot
D. sns.countplot

<details><summary>查看答案与解析</summary>
**答案:B**。`distplot` 自 seaborn 0.11 起已废弃(调用报 DeprecationWarning/错误),由 `histplot`(直方图)、`kdeplot`(核密度曲线)、`rugplot` 拆分替代。`kdeplot` 是平滑密度曲线,不是直方图(要叠加可 `histplot(..., kde=True)`);`countplot` 是类别频数条形图,用于分类型变量,画数值分布的直方图会得到每值一柱的错误图。
</details>

## 🏆 竞赛实战链接

- **出镜频率**:国赛 A/C 题的「数据分析」小节,相关性热力图几乎是必出图;美赛论文的统计图用 Seaborn 会显著提升观感评分
- **论文加分点**:①相关系数热力图 + 文字解读「最强相关对」;②多方法性能对比用箱线图/小提琴图并排;③`pairplot` 放在数据探索小节,说明特征选择依据
- **工具**:`sns.set_theme(style="whitegrid", context="paper", font_scale=1.1)` 一行统一全文风格;出图前确认中文/英文标签方案与《Matplotlib数据可视化》单元一致

## 💻 代码实现

数据探索三件套(热力图 + 散点矩阵 + 分组分布)的汇总模板:

```python
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

sns.set_theme(style="whitegrid", context="paper")
rng = np.random.default_rng(0)
df = pd.DataFrame(rng.normal(size=(150, 4)), columns=list("abcd"))
df["组别"] = rng.choice(["G1", "G2", "G3"], 150)

# ① 相关系数热力图
fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(
    df[list("abcd")].corr(), annot=True, fmt=".2f", cmap="RdBu_r", vmin=-1, vmax=1, center=0, ax=ax
)
ax.set_title("相关系数矩阵")
fig.savefig("corr.png", dpi=200)

# ② 散点矩阵(按组着色)
g = sns.pairplot(df, vars=list("abcd"), hue="组别", diag_kind="kde")
g.savefig("pair.png", dpi=200)

# ③ 分组分布对比
fig, axes = plt.subplots(2, 2, figsize=(10, 8))
for ax, col in zip(axes.flat, list("abcd")):
    sns.violinplot(data=df, x="组别", y=col, ax=ax)
fig.tight_layout()
fig.savefig("groups.png", dpi=200)
```

## 📚 延伸阅读

- **官方文档**:Seaborn 教程(https://seaborn.pydata.org/tutorial.html)—「Data structures accepted」一节讲透长表要求
- **图库**:Seaborn 示例画廊(https://seaborn.pydata.org/examples/index.html)— 找图型先翻这里
- **姊妹单元**:《Matplotlib数据可视化》(底层控制)→《Pandas数据处理》(长表数据的来源)→《sklearn机器学习实战》(热力图/pairplot 服务于建模)

## 🧠 小结

1. Seaborn 是 Matplotlib 的统计图层:axes-level 函数传 `ax=` 嵌入 OO 工作流,figure-level 函数自带分面
2. 数据必须整洁长表:一列一变量、一行一观测,`hue`/`col` 参数自动分组
3. 四件套:热力图(相关性)、pairplot(多维探索)、箱线/小提琴(分组分布)、hist/kde(分布形状)
4. 三个标配参数:相关系数热力图 `center=0, vmin=-1, vmax=1`;废弃的 `distplot` 换成 `histplot`/`kdeplot`
5. 统计图的价值在解读:每张图配一句「图中可见……」的结论,图才算完成
