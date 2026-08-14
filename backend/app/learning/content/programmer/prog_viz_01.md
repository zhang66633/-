# Matplotlib数据可视化

> **难度**:入门 · **预计学习时长**:40 分钟 · **主讲智能体**:🧩 求解器 · **方法类别**:编程工具

## 🎯 学习目标

学完本单元,你应该能够:

- 用**面向对象 API**(`fig, ax = plt.subplots()`)规范地组织绘图代码
- 绘制折线图、散点图、柱状图、热力图与误差棒图
- 用 `subplots` 排布多子图,做参数敏感性对比
- 掌握论文级出图细节:字体、字号、网格、图例、dpi 与保存格式
- 解决中文乱码这一国赛论文最常见的问题

## 📖 核心概念

### 1. 为什么用面向对象 API

Matplotlib 有两套接口:隐式的 pyplot 状态机(`plt.plot`)和显式的面向对象 API(`ax.plot`)。竞赛代码请**一律用 OO API**:

- `fig` 是整张画布,`ax` 是坐标系(一张 fig 可含多个 ax)
- 所有绘图元素(线、标签、网格)都挂在明确的 `ax` 上,多子图时不会「画串了」

```python
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 2 * np.pi, 100)
fig, ax = plt.subplots(figsize=(7, 4.5))   # 1 个坐标系,画布 7×4.5 英寸
ax.plot(x, np.sin(x), label="sin(x)")
ax.plot(x, np.cos(x), label="cos(x)")
ax.set_xlabel("x")
ax.set_ylabel("y")
ax.set_title("三角函数")
ax.legend()
ax.grid(alpha=0.3)
fig.savefig("trig.png", dpi=200)           # 保存而不是 plt.show()
```

### 2. 四种基础图型

```python
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(0)
x = np.linspace(0, 1, 30)
y = x + rng.normal(0, 0.1, x.size)

fig, axes = plt.subplots(2, 2, figsize=(8, 6))
# 折线图:连续量随自变量的变化
axes[0, 0].plot(x, y, "o-", ms=4)
# 散点图:两变量的关系
axes[0, 1].scatter(x, y, s=20, c=y, cmap="viridis")
# 柱状图:分类对比
axes[1, 0].bar(["A", "B", "C"], [3, 7, 5], color="steelblue")
# 误差棒图:均值 ± 标准差
axes[1, 1].errorbar(["A", "B", "C"], [3, 7, 5],
                    yerr=[0.5, 1.0, 0.8], fmt="o", capsize=4)
fig.tight_layout()
fig.savefig("four_basic.png", dpi=200)
```

### 3. 热力图与等值线

二维标量场(地形高程、热分布、概率密度)用 `imshow`(热力图)或 `contour/contourf`(等值线/填充):

```python
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(-3, 3, 200)
X, Y = np.meshgrid(x, x)
Z = np.exp(-(X**2 + Y**2) / 2) + 0.3 * np.sin(2 * X) * np.cos(2 * Y)

fig, ax = plt.subplots(figsize=(7, 5))
im = ax.imshow(Z, extent=[-3, 3, -3, 3], origin="lower",
               cmap="viridis", aspect="auto")
ax.contour(X, Y, Z, levels=6, colors="white", linewidths=0.6)
fig.colorbar(im, ax=ax, label="z")
ax.set_xlabel("x"); ax.set_ylabel("y")
fig.savefig("field.png", dpi=200)
```

> 注意 `imshow` 默认 `origin="upper"`(第 0 行在顶部),画「数学意义」的场必须 `origin="lower"`,否则图像上下颠倒。

### 4. 中文显示与论文级美化

```python
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]  # 中文字体
plt.rcParams["axes.unicode_minus"] = False   # 解决负号显示为方块
plt.rcParams["font.size"] = 11               # 全局字号
plt.rcParams["axes.grid"] = True             # 默认开网格
```

- **中文字体**:Windows 用 `SimHei`/`Microsoft YaHei`;若论文模板要求英文图,直接不加中文
- **保存格式**:论文插图存 **PDF/SVG**(矢量,放大不糊);汇报 PPT 存 PNG `dpi=300`;论文定稿再统一导出,不要用截图
- **`tight_layout()`**:多子图标签重叠时调用,或 `savefig(..., bbox_inches="tight")`

## 🧮 核心 API 速查

| 任务 | API | 说明 |
|------|-----|------|
| 创建画布 | `fig, ax = plt.subplots(nrows, ncols, figsize=)` | OO API 入口 |
| 折线 | `ax.plot(x, y, fmt, lw=, label=)` | `fmt` 如 `"r--"`、`"o-"` |
| 散点 | `ax.scatter(x, y, s=, c=, cmap=)` | `c` 可传数值实现按值着色 |
| 柱状 | `ax.bar / ax.barh` | 分类对比 |
| 误差棒 | `ax.errorbar(x, y, yerr=, capsize=)` | 均值 ± 标准差 |
| 热力图 | `ax.imshow(Z, extent=, origin=, cmap=)` | 二维标量场 |
| 等值线 | `ax.contour(X, Y, Z)` / `ax.contourf` | 线 / 填充 |
| 色标 | `fig.colorbar(im, ax=ax, label=)` | 必须绑定到 `ax` |
| 直方图 | `ax.hist(x, bins=)` | 分布形状 |
| 双 y 轴 | `ax2 = ax.twinx()` | 两条不同量纲的曲线 |
| 标注 | `ax.text / ax.annotate` | 局部说明 |
| 排版 | `fig.tight_layout()` / `fig.suptitle()` | 防重叠 / 总标题 |
| 保存 | `fig.savefig(name, dpi=, bbox_inches="tight")` | 论文用 PDF,汇报用 PNG |

## 💡 经典例题

### 例题 1:拟合效果图(数据 + 模型 + 残差)

> 给定 25 组带噪声的观测数据(真实关系 $y = 2.5x + 1.2$),用最小二乘拟合直线,并画「数据散点 + 拟合直线」与「残差分布」上下两图——这是建模论文里展示模型优度的标准构图。

**代码**:

```python
import numpy as np
import matplotlib.pyplot as plt

rng = np.random.default_rng(0)
x = np.linspace(0, 10, 25)
y = 2.5 * x + 1.2 + rng.normal(0, 1.5, x.size)
k, b = np.polyfit(x, y, 1)                 # 最小二乘直线
resid = y - (k * x + b)                    # 残差

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 6), sharex=True,
                               gridspec_kw={"height_ratios": [3, 1]})
ax1.scatter(x, y, s=30, label="观测数据", zorder=3)
ax1.plot(x, k * x + b, "r-", lw=2,
         label=f"拟合直线: $y={k:.2f}x+{b:.2f}$")
ax1.set_ylabel("y")
ax1.legend()
ax1.grid(alpha=0.3)

ax2.scatter(x, resid, s=30, color="gray", label="残差")
ax2.axhline(0, color="r", ls="--", lw=1)
ax2.set_xlabel("x")
ax2.set_ylabel("残差")
ax2.grid(alpha=0.3)

fig.tight_layout()
fig.savefig("fit_resid.png", dpi=200)
print(f"k={k:.3f}, b={b:.3f}, 残差标准差={resid.std():.3f}")
```

**输出解读**:

```
k=2.528, b=0.951, 残差标准差=1.280
```

`gridspec_kw={"height_ratios": [3, 1]}` 让上图占 3/4 高度、残差图占 1/4,是「主图 + 诊断图」的标准比例。残差图是最被低估的模型诊断工具:残差若呈现**随机散布**(无趋势),说明模型形式正确;若呈弧形或漏斗形,说明需要换模型或做变换。拟合参数 $k=2.528, b=0.951$ 与真值 $(2.5, 1.2)$ 的偏差在残差标准差量级内,拟合可信。

### 例题 2:二维标量场热力图与等值线

> 某优化问题需要可视化目标函数 $z = e^{-(x^2+y^2)/2} + 0.3\sin(2x)\cos(2y)$ 在 $[-3,3]^2$ 上的形态,标注等高线,用于论文中说明「多峰、需全局寻优」。

**代码**:

```python
import numpy as np
import matplotlib.pyplot as plt

x = np.linspace(-3, 3, 200)
X, Y = np.meshgrid(x, x)
Z = np.exp(-(X**2 + Y**2) / 2) + 0.3 * np.sin(2 * X) * np.cos(2 * Y)

fig, ax = plt.subplots(figsize=(7, 5))
im = ax.imshow(Z, extent=[-3, 3, -3, 3], origin="lower",
               cmap="viridis", aspect="auto")
cs = ax.contour(X, Y, Z, levels=6, colors="white", linewidths=0.6)
ax.clabel(cs, fontsize=8, fmt="%.1f")
fig.colorbar(im, ax=ax, label="z")
ax.set_xlabel("x"); ax.set_ylabel("y")
ax.set_title("目标函数形态:中心主峰 + 周边多个局部极值")
fig.savefig("field.png", dpi=200)
print(f"全局最大值位置: ({X.ravel()[Z.argmax()]:.2f}, "
      f"{Y.ravel()[Z.argmax()]:.2f}), 值 {Z.max():.3f}")
```

**输出解读**:

```
全局最大值位置: (0.44, -0.02), 值 1.139
```

`imshow` + `contour` 叠加是二维场可视化的标准组合:底色表达数值大小,等值线表达「山脊走向」,`clabel` 直接把等高线数值标在线上。最后的 `argmax` 输出说明:全局最大(≈1.14)并不在原点,而被正弦扰动项推到了 $(0.44, -0.02)$——这样的图放在论文里,比文字描述「函数多峰」有说服力得多。

### 例题 3:多子图参数敏感性对比

> 模型 $f(x; a) = a\sin x + x/5$ 含参数 $a$。请在同一张图中用 2×2 子图对比 $a = 0.5, 1, 2, 4$ 时曲线形态的变化(敏感性分析的经典呈现方式)。

**代码**:

```python
import numpy as np
import matplotlib.pyplot as plt

x = np.linspace(0, 2 * np.pi, 100)
params = [0.5, 1.0, 2.0, 4.0]

fig, axes = plt.subplots(2, 2, figsize=(8, 6), sharex=True, sharey=True)
for ax, a in zip(axes.flat, params):
    ax.plot(x, a * np.sin(x) + x / 5, lw=2, color="steelblue")
    ax.plot(x, x / 5, "r--", lw=1, label="线性趋势项" if a == 0.5 else None)
    ax.set_title(f"$a = {a}$")
    ax.grid(alpha=0.3)
    if a == 0.5:
        ax.legend()

for ax in axes[:, 0]:
    ax.set_ylabel("$f(x)$")
for ax in axes[1, :]:
    ax.set_xlabel("$x$")
fig.suptitle("参数 a 的敏感性:振荡幅值随 a 增大")
fig.tight_layout()
fig.savefig("sensitivity.png", dpi=200)
print("子图数量:", axes.size, "张")
```

**输出解读**:

```
子图数量: 4 张
```

要点:①`sharex=True, sharey=True` 让四张图坐标轴对齐,**可直接目测差异**;②`zip(axes.flat, params)` 是循环绘制多子图的标准写法;③`fig.suptitle` 放总标题、各子图 `set_title` 标参数值,读者一眼看到「参数如何影响曲线」。敏感性分析在国赛论文中是高频加分项,这种「同参数不同取值并列」的构图可以直接复用。

## ⚠️ 常见易错点

1. **两套 API 混用**。前脚 `ax.plot`,后脚 `plt.xlabel`,在单图时碰巧没事,多子图时立刻「画串/标错」;全程 OO API,不碰 `plt` 的绘图函数
2. **中文乱码**。未设置 `font.sans-serif` 时中文显示为方框;同时别忘了 `axes.unicode_minus=False`,否则负号变方块
3. **`imshow` 图像上下颠倒**。默认 `origin="upper"`,数学场(地形、概率密度)要 `origin="lower"`;另外 `imshow` 的 `extent` 决定坐标范围,别拿像素下标当坐标
4. **`colorbar` 不绑定 `ax`**。`fig.colorbar(im)` 在多子图时不知道缩放哪张图,必须 `fig.colorbar(im, ax=ax)`
5. **保存用截图**。论文插图必须是程序 `savefig` 出的矢量图(PDF/SVG),截图进论文会糊且被评委一眼看穿;PNG 至少 `dpi=300`
6. **图缺「三要素」**。无坐标轴标签、无图例、无单位——评委看不懂的图等于没画;每张图问自己:横轴是什么、纵轴是什么、不同曲线分别是什么

## ✏️ 自测练习(选择题)

**第 1 题** 用面向对象 API 画图时,设置横轴标签的正确方式是:

```python
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.plot(x, y)
```

A. plt.xlabel("x")
B. ax.set_xlabel("x")
C. fig.set_xlabel("x")
D. ax.xlabel("x")

<details><summary>查看答案与解析</summary>
**答案:B**。面向对象 API 下所有绘图元素都挂在明确的 `ax` 上,标签用 `ax.set_xlabel`。`plt.xlabel` 是 pyplot 状态机写法,作用于「当前坐标系」——单图时碰巧没事,多子图/封装成函数时就会标错地方;`fig` 是整张画布,没有 set_xlabel 方法;`ax.xlabel` 方法名不存在。竞赛代码一律 `fig, ax = plt.subplots()`,只用 `ax.*`,不碰 `plt` 的绘图函数。
</details>

**第 2 题** 用 `imshow` 显示数学意义的二维场(地形高程、概率密度)时,必须设置 `origin="lower"`,原因是:

A. 默认 origin="lower" 会把图像左右颠倒
B. 不设置时颜色映射会失效
C. 默认 origin="upper" 会把图像上下颠倒
D. 不设置时无法指定坐标轴范围

<details><summary>查看答案与解析</summary>
**答案:C**。`imshow` 默认 `origin="upper"`,第 0 行显示在顶部;而数学场的 y 轴向上增长,不设置时显示的其实是「上下翻转后的矩阵」——图像上下颠倒。左右颠倒混淆了 extent 参数的职责;颜色映射失效混淆了 cmap;坐标范围由 `extent` 参数负责,与 origin 无关。画数学意义的矩阵/场一律加 `origin="lower"`(或改用 `ax.matshow`,它会自动设置正确的 origin 与坐标)。
</details>

**第 3 题** 论文插图应该用什么格式保存,为什么?

A. 用 plt.show() 展示后截图进论文
B. 保存 JPG,压缩率高最适合论文
C. 保存 PNG 默认 dpi 即可,位图打印不糊
D. 保存 PDF/SVG 矢量格式,放大不糊;汇报 PPT 用 PNG(dpi=300)

<details><summary>查看答案与解析</summary>
**答案:D**。论文插图必须是程序 `savefig` 出的**矢量图**(PDF/SVG),放大任意倍数不糊;PNG 是位图,打印前至少 `dpi=300`,默认 dpi(100)会糊。截图进论文既糊又会被评委一眼看穿;JPG 是有损压缩,会产生压缩伪影,不适合线条与文字密集的学术图。论文定稿再统一导出矢量图,不要截图。
</details>

## 🏆 竞赛实战链接

- **出镜频率**:每篇论文 8~15 张图,图的质量直接影响「论文写作」评分项;国赛 A 题的三维建模图、C 题的统计图、美赛的可视化题都靠 Matplotlib 出图
- **论文加分点**:①统一全文字体、字号与配色(同一变量在所有图中用同一种颜色);②每张图配图题编号与图注(图 1:xxx);③敏感性分析用多子图并列,对比直接可读
- **进阶关联**:需要统计风格、更美观的图时用《Seaborn高级可视化》单元;三维曲面用 `ax.plot_surface`(Matplotlib 的 3D 子模块)

## 💻 代码实现

论文级绘图函数模板(封装成函数,全篇复用):

```python
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.size"] = 11

def paper_line(x, y_list, labels, xlabel, ylabel, fname, title=None):
    """多条曲线的论文级折线图:y_list 为曲线列表,labels 为图例。"""
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for y, lb in zip(y_list, labels):
        ax.plot(x, y, lw=2, label=lb)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(fname, dpi=300, bbox_inches="tight")
    plt.close(fig)          # 防止循环绘图时内存堆积

x = np.linspace(0, 4, 100)
paper_line(x, [np.exp(-x), np.exp(-2 * x)],
           ["λ=1", "λ=2"], "t", "衰减曲线", "decay.png")
print("已保存 decay.png")
```

## 📚 延伸阅读

- **官方文档**:Matplotlib 教程(https://matplotlib.org/stable/tutorials/index.html),重点「Usage Guide」与「Artist tutorial」
- **配色参考**:https://matplotlib.org/stable/users/explain/colors/colormaps.html — 选择适合论文印刷的 colormap
- **进阶关联**:学完本单元 → 《Seaborn高级可视化》(统计图一步到位)→ 三维绘图可自行查阅 `mpl_toolkits.mplot3d`

## 🧠 小结

1. 全程面向对象 API:`fig, ax = plt.subplots()`,所有元素挂在 `ax` 上,多图不串线
2. 四大基础图型(折线/散点/柱状/误差棒)+ 场可视化(`imshow` + `contour` + `colorbar`)覆盖竞赛 90% 出图需求
3. 论文级出图三件套:中文字体设置、`tight_layout` 防重叠、PDF/SVG 矢量保存
4. 残差图与多子图敏感性对比是「模型诊断」的两张王牌图,建议每道建模题都画
5. 图的三要素(轴标签、图例、单位)缺一不可——评委看不懂的图等于没画
