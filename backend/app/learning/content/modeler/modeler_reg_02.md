# 多元回归与变量选择

> **难度**:入门 · **预计学习时长**:45 分钟 · **主讲智能体**:🧩 建模手 · **方法类别**:预测

> 📌 **前置单元**:建议先学《线性回归与最小二乘法》(modeler_reg_01)。本单元假设你已熟悉一元最小二乘、$R^2$ 与残差分析。

## 🎯 学习目标

学完本单元,你应该能够:

- 用矩阵语言写出多元回归模型,并从「残差平方和最小」推导正规方程 $X^TX\hat\beta = X^Ty$
- 解释 $R^2$ 与调整 $R^2$ 的区别,用 AIC/BIC 比较不同变量数的模型
- 识别多重共线性(VIF),说清它为什么使系数「乱跳」
- 掌握逐步回归三种策略的流程与陷阱,理解岭回归/LASSO 的正则化思想
- 用 statsmodels/sklearn 完成一次完整的多元回归建模与变量选择

## 📖 核心概念

### 1. 从一元到多元:矩阵形式

$$y = \beta_0 + \beta_1 x_1 + \dots + \beta_p x_p + \varepsilon \quad\Longleftrightarrow\quad y = X\beta + \varepsilon$$

$X$ 是 $n \times (p+1)$ 设计矩阵(第一列全 1)。$\beta_j$ 的含义是「**其他变量不变时**,$x_j$ 增加 1 单位,$y$ 的平均变化」——「其他变量不变」是多元系数的灵魂,论文里解释系数时必须带上这句限定。

### 2. 最小二乘的几何意义

最小化 $SSE = \|y - X\beta\|^2$,几何上等价于找 $y$ 在 $X$ 列空间上的**正交投影**:

- 残差 $e = y - X\hat\beta$ 与 $X$ 的每一列正交 → 正规方程 $X^Te = 0$
- $y$ 被分解为「列空间中的拟合值」与「正交的残差」,勾股定理给出 $SST = SSR + SSE$
- 拟合值 $\hat y = Hy$,其中帽子矩阵 $H = X(X^TX)^{-1}X^T$ 是幂等对称的投影矩阵

### 3. 多重共线性:当自变量「互相抄袭」

若 $x_1$ 与 $x_2$ 高度相关,则 $X^TX$ 接近奇异,求逆极不稳定,系数估计的方差爆炸。典型症状:

- 整体 $F$ 检验显著,但单个系数的 $t$ 检验几乎都不显著
- 系数符号与业务常识相反,或数值大得离谱
- 增删一个样本,系数大幅改变

**检测**:方差膨胀因子 $\mathrm{VIF}_j = 1/(1 - R_j^2)$,其中 $R_j^2$ 是把 $x_j$ 对其余所有自变量回归得到的 $R^2$。经验规则:VIF > 10 表示严重共线性(部分教材取 5)。**处理**:删除或合并业务变量、岭回归、主成分回归(参见《主成分分析PCA》单元)。

### 4. 变量选择:为什么不能「全塞进去」

变量越多,SSE 必然越小、$R^2$ 必然越大,但方差增大、过拟合随之而来。模型比较要用**带惩罚的准则**:

- **调整 $R^2$**:$\bar R^2 = 1 - \dfrac{SSE/(n-p-1)}{SST/(n-1)} = 1 - (1-R^2)\dfrac{n-1}{n-p-1}$。新增变量必须让 SSE 减少得「划算」,$\bar R^2$ 才会上升
- **AIC/BIC**:从信息论角度权衡拟合与复杂度,数值小者优。BIC 对变量数惩罚更重,倾向更小的模型

### 5. 逐步回归与正则化:两代变量选择方法

- **前向选择**:从空模型开始,逐个加入最显著的变量,直到没有显著者可加
- **后向剔除**:从全模型开始,逐个删除最不显著的变量,直到剩下的都显著
- **逐步回归**:每步「加一个再看能否删一个」,双向搜索

逐步回归优点是可解释、论文好写;缺点是:①多重检验问题(反复用同一批数据检验,$p$ 值被「数据窥探」污染);②路径依赖,三种策略可能给出三个模型;③结果不稳定。现代替代是**正则化**:岭回归(L2 惩罚,收缩系数)、LASSO(L1 惩罚,可直接把系数压成 0,自动完成变量选择),用交叉验证选惩罚参数 $\lambda$。竞赛稳妥套路:**LASSO 选变量 + 普通最小二乘重拟合做解释**。

## 🧮 公式与结论

### 正规方程与 OLS 解

$$SSE(\beta) = (y - X\beta)^T(y - X\beta), \qquad \nabla_\beta\, SSE = -2X^T(y - X\beta) = 0$$

$$\Rightarrow \quad X^TX\hat\beta = X^Ty \quad\Rightarrow\quad \hat\beta = (X^TX)^{-1}X^Ty$$

- 拟合值 $\hat y = X\hat\beta = Hy$,残差 $e = (I - H)y$,且 $\hat y \perp e$
- 若 $X$ 列不满秩($X^TX$ 不可逆),正规方程有无穷多解——完全共线性的标志

### 参数估计的分布

Gauss–Markov 条件下:

$$\hat\beta \sim N\big(\beta,\ \sigma^2 (X^TX)^{-1}\big), \qquad s^2 = \frac{SSE}{n-p-1}$$

第 $j$ 个系数的标准误 $\mathrm{SE}(\hat\beta_j) = s\sqrt{(X^TX)^{-1}_{jj}}$,$t_j = \hat\beta_j / \mathrm{SE}(\hat\beta_j) \sim t(n-p-1)$。

### 模型比较准则

$$\bar R^2 = 1 - (1-R^2)\frac{n-1}{n-p-1}, \qquad AIC = n\ln\frac{SSE}{n} + 2(p+1), \qquad BIC = n\ln\frac{SSE}{n} + (p+1)\ln n$$

整体显著性检验(所有系数是否同时为零):

$$F = \frac{SSR/p}{SSE/(n-p-1)} \sim F(p,\ n-p-1)$$

### 岭回归与 LASSO

$$\hat\beta_{\text{ridge}} = \arg\min_{\beta}\Big\{\|y - X\beta\|^2 + \lambda\sum_{j=1}^p \beta_j^2\Big\} = (X^TX + \lambda I)^{-1}X^Ty$$

$$\hat\beta_{\text{lasso}} = \arg\min_{\beta}\Big\{\|y - X\beta\|^2 + \lambda\sum_{j=1}^p |\beta_j|\Big\}$$

- 岭回归给 $X^TX$ 加上对角「脊」,永远可逆 → 直接解决共线性;系数向 0 收缩,但通常**不恰好**为 0
- LASSO 的 L1 惩罚在原点有尖角,使部分系数**恰好为 0** → 同时完成变量选择;$\lambda$ 越大,模型越小
- **必须先标准化自变量**,否则量纲大的特征会「替别人挨罚」;LASSO 系数是收缩后的,不宜直接解读大小

## 💡 经典例题

### 例题 1:正交设计下的多元回归手算

> 四个观测:$x_1 = (-1, 1, -1, 1)$,$x_2 = (-1, -1, 1, 1)$,$y = (1, 4, 2, 7)$。求最小二乘估计与 $R^2$。

设计矩阵 $X = [\mathbf{1}, x_1, x_2]$。列两两正交($\sum x_1 = 0$,$\sum x_2 = 0$,$\sum x_1x_2 = 0$),于是:

$$X^TX = \begin{bmatrix} 4 & 0 & 0 \\ 0 & 4 & 0 \\ 0 & 0 & 4 \end{bmatrix} = 4I, \qquad X^Ty = \begin{bmatrix} \sum y \\ \sum x_1 y \\ \sum x_2 y \end{bmatrix} = \begin{bmatrix} 14 \\ 8 \\ 4 \end{bmatrix}$$

$$\hat\beta = (X^TX)^{-1}X^Ty = \left(\frac{14}{4}, \frac{8}{4}, \frac{4}{4}\right) = (3.5,\ 2,\ 1)$$

即 $\hat y = 3.5 + 2x_1 + x_2$。拟合值 $(0.5, 4.5, 2.5, 6.5)$,残差 $(0.5, -0.5, -0.5, 0.5)$,$SSE = 1$;$\bar y = 3.5$,$SST = 21$,故 $R^2 = 1 - 1/21 = 0.9524$。

**解析**:列正交时 $(X^TX)^{-1}$ 也是对角阵,每个系数退化成「一元公式」独立给出——**正交试验设计**追求的就是这个效果(参见正交设计类单元)。同时可以检验共线性:把 $x_1$ 对 $x_2$ 回归,$R^2 = 0$(两列正交),故两个变量的 VIF 都等于 1,无共线性。残差 $+0.5, -0.5, -0.5, +0.5$ 恰好与 $x_1x_2$ 的符号一致,提示可能遗漏了交互项 $x_1x_2$——残差分析在多元回归中同样重要。

### 例题 2:完全共线性与近似共线性

**完全共线性**:若题目中同时给了「摄氏温度 $x_1$」和「华氏温度 $x_2 = 1.8x_1 + 32$」,则 $X$ 的第 2、3 列线性相关,$\det(X^TX) = 0$,正规方程有无穷多解,软件通常报错或自动丢弃一列。模型「无法识别」——数据里没有信息能区分两者的贡献。

**近似共线性**(实战更常见):$x_2 \approx 2x_1 + $ 小噪声。$X^TX$ 可逆但条件数巨大。后果:$\hat\beta_1, \hat\beta_2$ 的方差爆炸,符号甚至相反——出现「$x_1$ 正作用、$x_2$ 强负作用」的怪象,但两者的线性组合 $2\hat\beta_1 + \hat\beta_2$ 反而估计得较准。

**诊断**:若把 $x_1$ 对 $x_2$ 回归得 $R^2 = 0.99$,则 $\mathrm{VIF} = 1/(1-0.99) = 100 \gg 10$,严重共线;$R^2 = 0.9$ 对应 VIF = 10,正好到警戒线。

**解析**:以**预测**为目的时,共线性其实「无害」(整体预测仍然良好);只有做**解释/归因**时才必须处理。先想清楚题目要什么,再决定是否动手处理共线性。

### 例题 3:AIC/BIC 选模型

> $n = 20$ 的样本,同一组数据($SST = 150$)上拟合两个候选:模型 A($p = 2$,SSE = 30)与模型 B($p = 5$,SSE = 25)。该选谁?

**只看 $R^2$**:$R_A^2 = 1 - 30/150 = 0.8$,$R_B^2 = 1 - 25/150 = 0.833$ → 永远选 B。

**调整 $R^2$**:

$$\bar R_A^2 = 1 - 0.2 \times \frac{19}{17} = 0.776, \qquad \bar R_B^2 = 1 - 0.167 \times \frac{19}{14} = 0.774$$

**AIC/BIC**:

$$AIC_A = 20\ln(1.5) + 2 \times 3 = 8.11 + 6 = 14.11, \qquad AIC_B = 20\ln(1.25) + 2 \times 6 = 4.46 + 12 = 16.46$$

$$BIC_A = 8.11 + 3\ln 20 = 17.10, \qquad BIC_B = 4.46 + 6\ln 20 = 22.44$$

**解析**:B 多出的 3 个变量只把 SSE 从 30 降到 25,「性价比」不足——调整 $R^2$、AIC、BIC 三个准则全部选 A。这就是「模型比较必须用带惩罚的准则」的数值演示:看 $R^2$ 你永远会选最大模型,直到过拟合。

## ⚠️ 常见易错点

1. **用 $R^2$ 比较不同变量数的模型**。变量越多 $R^2$ 必然越大;必须用调整 $R^2$/AIC/BIC,否则永远选全模型
2. **共线性时只盯单个系数的 $p$ 值**。整体显著而个体都不显著、系数符号怪异——先查 VIF 表,而不是硬解释「不显著」
3. **把逐步回归的结果当「真模型」**。$p$ 值已被反复检验污染,且路径依赖;结果应在独立验证集(或交叉验证)上确认后再写进论文
4. **岭/LASSO 前不标准化**。惩罚对量纲大的特征不公平,结果没有意义;且 LASSO 的系数被收缩过,不宜直接解读大小
5. **认为 VIF 大就必须删变量**。预测任务可以保留共线变量;只有解释任务才必须处理,处理方式也不止删变量(岭回归、主成分)
6. **在同一批数据上「先选变量后做检验」**。选择过程已经「看过」数据,再用同一批数据报 $p$ 值,显著性是被夸大的

## ✏️ 自测练习

**第 1 题(推导)**:从 $SSE(\beta) = (y - X\beta)^T(y - X\beta)$ 出发,用矩阵求导推出正规方程 $X^TX\hat\beta = X^Ty$。

<details><summary>查看答案</summary>

展开:$(y - X\beta)^T(y - X\beta) = y^Ty - 2\beta^TX^Ty + \beta^TX^TX\beta$。对 $\beta$ 求梯度(利用 $\frac{\partial}{\partial\beta}\beta^TA\beta = 2A\beta$ 对对称矩阵 $A$):

$$\nabla_\beta SSE = -2X^Ty + 2X^TX\beta = 0 \quad\Rightarrow\quad X^TX\hat\beta = X^Ty$$

若 $X$ 列满秩,左乘 $(X^TX)^{-1}$ 得 $\hat\beta = (X^TX)^{-1}X^Ty$。

</details>

**第 2 题(计算)**:某回归问题中 $X^TX = 4I_3$($p = 2$,含截距),$X^Ty = (16, 8, -4)^T$。求 $\hat\beta$ 与拟合方程。

<details><summary>查看答案</summary>

$(X^TX)^{-1} = \frac14 I$,故 $\hat\beta = \frac14(16, 8, -4) = (4, 2, -1)$,拟合方程 $\hat y = 4 + 2x_1 - x_2$。列正交时每个系数互不干扰,这正是例题 1 的模式。

</details>

**第 3 题(计算)**:把 $x_3$ 对其余自变量回归得 $R^2 = 0.9$,求 $x_3$ 的 VIF;若 $R^2 = 0.95$ 呢?各属于什么水平?

<details><summary>查看答案</summary>

$R^2 = 0.9$:$\mathrm{VIF} = 1/(1-0.9) = 10$,恰好到「严重共线性」的常用警戒线;$R^2 = 0.95$:$\mathrm{VIF} = 20$,严重共线。注意 VIF 是相对经验的软指标,要结合 $F/t$ 检验的矛盾现象与业务理解综合判断。

</details>

**第 4 题(判断)**:逐步回归选出的模型,能否直接用同一批数据的 $p$ 值证明各变量显著?

<details><summary>查看答案</summary>

**不能**。逐步回归在反复使用同一批数据做检验,「显著」本身成了入选标准——$p$ 值被数据窥探(data snooping)污染,系统性偏小。正确做法:在独立验证集或交叉验证中评估所选模型的预测表现,再报告各变量的置信区间,而不是原始 $p$ 值。

</details>

## 🏆 竞赛实战链接

- **出镜场景**:国赛 2021 B(乙醇偶合制备 C4 烯烃)是多元回归的教科书式场景——温度、催化剂组合、投料比等多个工艺变量影响产物收率,变量之间存在共线性(温度与催化剂活性耦合),「回归建模 + 共线性诊断 + 变量选择」是标准解法;2023 C(蔬菜定价补货)的销量受多个特征影响,同样适用
- **论文加分点**:①给出 **VIF 表**证明共线性检查做过;②用 **AIC/BIC 表格**展示变量选择过程,而不是「我们选了这些变量」一句话;③**LASSO 系数路径图**(系数随 $\lambda$ 增大逐个收缩为 0)是很漂亮的插图;④解释系数时写上「其他变量不变」的限定
- **美赛**:C 题大数据场景特征动辄几十上百,变量选择是必写环节;LASSO + 交叉验证是评委熟悉且认可的做法

## 💻 代码实现

```python
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.linear_model import LassoCV
from sklearn.preprocessing import StandardScaler

# 模拟数据:y = 3 + 2x1 - x2 + 噪声,其中 x2 与 x1 高度相关(人为共线性)
rng = np.random.default_rng(42)
n = 100
x1 = rng.normal(0, 1, n)
x2 = 0.9 * x1 + rng.normal(0, 0.2, n)      # x2 ≈ 0.9 x1
y = 3 + 2 * x1 - 1 * x2 + rng.normal(0, 0.5, n)
X = pd.DataFrame({"x1": x1, "x2": x2})

# 1) VIF 诊断
vif = pd.DataFrame(
    {"VIF": [variance_inflation_factor(X.values, j) for j in range(X.shape[1])]},
    index=X.columns,
)
print(vif)   # x1、x2 的 VIF 都会很大 → 共线性实锤

# 2) 全模型 OLS
m = sm.OLS(y, sm.add_constant(X)).fit()
print(m.summary())   # 可能出现系数符号异常、单个 p 值不显著

# 3) LASSO 自动选变量(必须先标准化)
X_s = StandardScaler().fit_transform(X)
lasso = LassoCV(cv=5, random_state=0).fit(X_s, y)
print("LASSO 系数:", np.round(lasso.coef_, 4))
print("最优 lambda:", round(lasso.alpha_, 4))
```

> 竞赛中「LASSO 选变量 → 对入选变量重新做 OLS 得到可解释系数」是稳妥的两段式套路。

## 📚 延伸阅读

- **教材**:何晓群《应用回归分析》多元回归与共线性章节;ISLR 第 3、6 章(变量选择与正则化,免费电子版)
- **经典书**:Belsley, Kuh & Welsch, *Regression Diagnostics*(共线性与诊断的经典);Hastie, *The Elements of Statistical Learning* 第 3 章(线性方法与正则化)
- **在线**:sklearn 用户指南的 [Lasso 与交叉验证](https://scikit-learn.org/stable/modules/linear_model.html#lasso)部分;statsmodels 的 [VIF 文档](https://www.statsmodels.org/stable/generated/statsmodels.stats.outliers_influence.variance_inflation_factor.html)
- **进阶关联**:前置《线性回归与最小二乘法》(modeler_reg_01)→ 本单元 → [主成分分析](modeler_pca_01)(共线性的降维解法)→ [神经网络预测入门](modeler_nn_01)(非线性推广)

## 🧠 小结

1. 多元 OLS 的解析解 $\hat\beta = (X^TX)^{-1}X^Ty$ 来自投影几何:拟合值落在列空间,残差与之正交
2. 「其他变量不变」是多元系数解释的前提;共线性使 $X^TX$ 近奇异、系数方差爆炸——VIF > 10 要警惕
3. 模型比较永远用带惩罚的准则:调整 $R^2$、AIC、BIC,绝不用原始 $R^2$
4. 逐步回归直观但脆弱;LASSO + 交叉验证是现代默认选择,论文里两者对照写最稳
5. 预测与解释的目标不同:共线性对预测影响小,对归因影响大——先想清楚题目要什么
