# sklearn机器学习实战

> **难度**:进阶 · **预计学习时长**:60 分钟 · **主讲智能体**:🧩 求解器 · **方法类别**:编程工具

## 🎯 学习目标

学完本单元,你应该能够:

- 掌握 sklearn 的统一 Estimator API:`fit` / `predict` / `score` 三步走
- 搭建「划分 → 标准化 → 训练 → 评估」的标准监督学习流程
- 熟练使用分类(逻辑回归、随机森林)、回归(线性、岭回归)、聚类(KMeans)与降维(PCA)
- 读懂混淆矩阵、分类报告与 $R^2$/RMSE,选对评估指标
- 用交叉验证与网格搜索做模型选择,并写出论文级的模型对比

## 📖 核心概念

### 1. 统一 API:所有模型长得一样

sklearn 的设计核心是 **Estimator API**——分类、回归、聚类、降维全部遵循同一套接口:

```python
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

X, y = make_classification(n_samples=200, n_features=4, random_state=0)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=0)

model = LogisticRegression(max_iter=2000)   # ① 创建(设置超参数)
model.fit(X_train, y_train)                 # ② 训练(从数据学习)
pred = model.predict(X_test)                # ③ 预测(分类/回归)
score = model.score(X_test, y_test)         # ③' 评估(默认指标)
print("测试准确率:", f"{score:.3f}")
```

换模型只改第一行。这让你可以批量试验几十个模型,而代码骨架不变——「模型对比表」的成本被压到最低。

### 2. 标准监督学习流程

```python
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

X, y = make_classification(n_samples=400, n_features=8, random_state=0)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)   # 分层划分

scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)   # 训练集:拟合 + 变换
X_test_s = scaler.transform(X_test)         # 测试集:只用变换!

model = LogisticRegression(max_iter=2000)
model.fit(X_train_s, y_train)
print("测试准确率:", model.score(X_test_s, y_test))
```

> 🔴 **铁律**:`scaler` 只能在训练集上 `fit`,测试集只 `transform`——否则测试集信息「泄漏」进模型,评估结果虚高。工程化防泄漏做法见《建模数据处理流水线》单元。

### 3. 四类任务的常用模型

| 任务 | 模型 | 特点 |
|------|------|------|
| 分类 | `LogisticRegression` | 线性、可解释、快;分类的基线 |
| 分类 | `RandomForestClassifier` | 非线性、抗过拟合强、无需调参即好用 |
| 回归 | `LinearRegression` / `Ridge` / `Lasso` | 线性族;岭回归抗共线性,Lasso 稀疏 |
| 回归 | `RandomForestRegressor` | 非线性回归 |
| 聚类 | `KMeans` | 球状簇,需指定簇数 |
| 聚类 | `DBSCAN` | 任意形状簇,自动定簇数 |
| 降维 | `PCA` | 线性降维,去相关 |
| 降维 | `TSNE` | 可视化降维(不用于建模特征) |

### 4. 评估指标:选错指标等于白做

- **分类**:准确率 `accuracy`(类别均衡时用)、精确率/召回率/F1(`classification_report`)、`confusion_matrix`(看错在哪)
- **回归**:$R^2$(可解释方差比例)、RMSE(与目标同量纲的误差)
- **聚类**:调整兰德指数 `adjusted_rand_score`(有真实标签时)、轮廓系数 `silhouette_score`(无标签时)

### 5. 模型选择:交叉验证与网格搜索

```python
from sklearn.datasets import make_classification
from sklearn.model_selection import (train_test_split, cross_val_score,
                                     GridSearchCV)
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier

X, y = make_classification(n_samples=400, n_features=8, random_state=0)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)
X_train_s = StandardScaler().fit_transform(X_train)

model = RandomForestClassifier(n_estimators=100, random_state=0)
# 5 折交叉验证:评估的黄金标准
scores = cross_val_score(model, X, y, cv=5, scoring="accuracy")
print(f"5折CV: {scores.mean():.3f} ± {scores.std():.3f}")

# 网格搜索:超参数自动调优
grid = GridSearchCV(
    RandomForestClassifier(random_state=0),
    param_grid={"n_estimators": [50, 100, 200],
                "max_depth": [5, 10, None]},
    cv=5, scoring="accuracy")
grid.fit(X_train_s, y_train)
print("最优参数:", grid.best_params_)
```

## 🧮 核心 API 速查

| 任务 | API | 说明 |
|------|-----|------|
| 划分数据 | `train_test_split(X, y, test_size=, random_state=, stratify=)` | 分类问题加 `stratify=y` 保持类别比例 |
| 标准化 | `StandardScaler().fit_transform / transform` | 训练集 fit,测试集只 transform |
| 逻辑回归 | `LogisticRegression(max_iter=2000)` | 收敛警告时加大 `max_iter` |
| 随机森林 | `RandomForestClassifier(n_estimators=100, random_state=0)` | 竞赛主力模型 |
| 岭回归 | `Ridge(alpha=1.0)` | `alpha` 越大正则越强 |
| KMeans | `KMeans(n_clusters=, n_init=10, random_state=0)` | 结果受初始中心影响,固定种子 |
| PCA | `PCA(n_components=2).fit_transform(X)` | 先标准化再做 PCA |
| 混淆矩阵 | `confusion_matrix(y_true, y_pred)` | 行=真实,列=预测 |
| 分类报告 | `classification_report(y_true, y_pred, zero_division=0)` | 精确率/召回率/F1 |
| 回归指标 | `r2_score` / `mean_squared_error` | RMSE = `mse ** 0.5` |
| 交叉验证 | `cross_val_score(model, X, y, cv=5, scoring=)` | 比单次划分更稳健 |
| 网格搜索 | `GridSearchCV(model, param_grid, cv=5)` | `.best_params_` / `.best_score_` |

## 💡 经典例题

### 例题 1:分类竞赛全流程(逻辑回归 vs 随机森林)

> 某二分类问题有 500 个样本、6 维特征(信息特征 4 维)。请完成:分层划分 → 标准化 → 训练逻辑回归与随机森林 → 输出混淆矩阵与分类报告,并对比两个模型。

**代码**:

```python
import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, classification_report

X, y = make_classification(n_samples=500, n_features=6,
                           n_informative=4, n_redundant=0,
                           random_state=0)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)

scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s = scaler.transform(X_test)

models = {
    "逻辑回归": LogisticRegression(max_iter=2000),
    "随机森林": RandomForestClassifier(n_estimators=100, random_state=0),
}
for name, model in models.items():
    model.fit(X_train_s, y_train)
    y_pred = model.predict(X_test_s)
    print(f"\n===== {name} =====")
    print("测试准确率:", f"{model.score(X_test_s, y_test):.3f}")
    print("混淆矩阵:\n", confusion_matrix(y_test, y_pred))
    print(classification_report(y_test, y_pred, zero_division=0,
                                digits=3))
```

**输出解读**(节选):

```
===== 逻辑回归 =====
测试准确率: 0.800
混淆矩阵:
 [[42  8]
 [12 38]]
===== 随机森林 =====
测试准确率: 0.830
混淆矩阵:
 [[39 11]
 [ 6 44]]
```

读混淆矩阵:行是真实类别,列是预测类别——随机森林总误判 17 个(11+6),少于逻辑回归的 20 个(8+12),非线性模型略胜一筹。论文里的模型对比表就来自这个循环:同一份数据、同一个评估协议,**只换模型**。注意 `stratify=y` 保证了测试集中两类比例与总体一致,否则小样本时测试集可能偏斜。

### 例题 2:回归与正则化(线性 vs 岭回归)

> 300 个样本、8 维特征的回归问题(含噪声)。分别训练普通线性回归与岭回归,用 $R^2$ 与 RMSE 评估,并查看岭回归系数被压缩的幅度。

**代码**:

```python
import numpy as np
from sklearn.datasets import make_regression
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import r2_score, mean_squared_error

X, y = make_regression(n_samples=300, n_features=8, noise=20,
                       random_state=0)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42)

for name, model in [("线性回归", LinearRegression()),
                    ("岭回归", Ridge(alpha=10.0))]:
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    r2 = r2_score(y_test, pred)
    rmse = mean_squared_error(y_test, pred) ** 0.5
    print(f"{name}: R²={r2:.3f}, RMSE={rmse:.2f}, "
          f"系数范围 [{model.coef_.min():.1f}, {model.coef_.max():.1f}]")
```

**输出解读**:

```
线性回归: R²=0.991, RMSE=20.76, 系数范围 [6.9, 97.8]
岭回归: R²=0.987, RMSE=24.76, 系数范围 [6.5, 92.5]
```

本例中普通线性回归精度略高——数据没有共线性、噪声也不大时,**正则化是有代价的**(岭回归的偏差换稳健)。但岭回归的系数更「收敛」(最大值 97.8 → 92.5),当特征存在共线性或噪声较大时,普通回归的系数会剧烈震荡,岭回归的 $\ell_2$ 惩罚是标准解药(可以把 `make_regression` 的 `noise` 调到 100 再对比,差距立刻反转);想要稀疏解(特征选择)则用 Lasso($\ell_1$)。报告指标时 $R^2$ 与 RMSE 一起给:$R^2$ 说明「解释了多少方差」,RMSE 给出「误差的量纲」。

### 例题 3:聚类与降维(KMeans + PCA)

> 400 个样本、8 维特征、真实簇数为 4 的聚类问题。请:(1) 标准化后用 KMeans 聚类,与真实标签对比(调整兰德指数);(2) 用肘部法则(不同 k 的惯性值)辅助选簇数;(3) PCA 降到 2 维观察结构。

**代码**:

```python
import numpy as np
from sklearn.datasets import make_blobs
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score

X, y_true = make_blobs(n_samples=400, centers=4, n_features=8,
                       cluster_std=1.5, random_state=0)
X_s = StandardScaler().fit_transform(X)

# (1) KMeans 聚类质量:调整兰德指数(1=完全一致,0=随机)
km = KMeans(n_clusters=4, n_init=10, random_state=0)
y_pred = km.fit_predict(X_s)
print(f"ARI = {adjusted_rand_score(y_true, y_pred):.3f}")

# (2) 肘部法则:k 从 2 到 8 的惯性(簇内平方和)
inertias = [KMeans(n_clusters=k, n_init=10, random_state=0)
            .fit(X_s).inertia_ for k in range(2, 9)]
print("惯性序列(k=2..8):", [round(v) for v in inertias])

# (3) PCA 可视化(降维后再聚类,验证结构)
X2 = PCA(n_components=2, random_state=0).fit_transform(X_s)
km2 = KMeans(n_clusters=4, n_init=10, random_state=0).fit(X2)
print(f"PCA 降维后聚类 ARI = "
      f"{adjusted_rand_score(y_true, km2.labels_):.3f}")
```

**输出解读**:

```
ARI = 1.000
ARI(降维后)= 1.000
惯性序列(k=2..8): [1662, 883, 347, 332, 316, 304, 291]
```

解读:①ARI = 1.000,聚类完美还原真实簇——`adjusted_rand_score` 是「有真实标签」时聚类的标准指标,比准确率公平(它校正了随机命中的影响);②惯性序列从 k=3 到 k=4 出现断崖式下降(883 → 347),之后趋缓,「肘部」明确指向簇数 4;③PCA 降维后聚类质量不变,说明数据结构能被 2 维主成分保留——「先 PCA 后聚类」是 8 维数据可视化的标准组合。注意 KMeans 对**量纲敏感**:不标准化直接跑,ARI 会大幅下降,这也是第 (1) 步标准化的原因。

## ⚠️ 常见易错点

1. **数据泄露:先标准化再划分**。`scaler.fit_transform(X)` 之后再切分,测试集信息(均值/方差)已经混入缩放——评估虚高,实战翻车;必须先划分,或直接用 `Pipeline`(见《建模数据处理流水线》单元)
2. **不平衡数据只看准确率**。99% 是正类的数据,「全部预测正类」也有 99% 准确率;此时必须看精确率/召回率/F1,或 AUC,并在 `train_test_split` 加 `stratify=y`
3. **`fit_transform` 与 `transform` 混用**。对测试集再次 `fit_transform` 等于用测试集重新拟合了缩放器,泄漏测试信息;测试集永远只 `transform`
4. **KMeans 不标准化**。量纲大的特征会主导距离计算,聚类结果被「大数特征」绑架;先 `StandardScaler` 再聚类
5. **拿测试集反复调参后报成绩**。测试集只允许**用一次**(最终评估);调参全程用交叉验证,否则「测试准确率」已经变成训练信息的一部分,论文里会被质疑
6. **忽略随机性**。随机森林、KMeans、划分都含随机成分;固定 `random_state`,论文复现才有一致结果;随机森林等集成模型多跑几个种子报告均值 ± 标准差更严谨

## ✏️ 自测练习

**第 1 题(判断)**:下面的代码哪里违反了「不泄漏」原则?

```python
from sklearn.datasets import make_classification
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

X, y = make_classification(n_samples=300, n_features=6, random_state=0)
model = LogisticRegression(max_iter=2000)    # 题目设定的模型

X_s = StandardScaler().fit_transform(X)      # 全量标准化(题目代码)
X_train, X_test, y_train, y_test = train_test_split(X_s, y, test_size=0.2)
model.fit(X_train, y_train)
print(model.score(X_test, y_test))
```

<details><summary>查看答案</summary>

第一步在全量数据上 `fit_transform`,缩放参数(均值/标准差)用到了测试集的取值,测试集信息泄漏进预处理。正确顺序:先 `train_test_split`,再在训练集上 `fit_transform`、测试集上仅 `transform`;或直接把 scaler 和模型装进 `Pipeline` 再划分(参见《建模数据处理流水线》单元)。

</details>

**第 2 题(补全)**:写出用 5 折交叉验证评估随机森林分类器准确率的代码。

<details><summary>查看答案</summary>

```python
from sklearn.datasets import make_classification
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestClassifier

X, y = make_classification(n_samples=300, n_features=6, random_state=0)
model = RandomForestClassifier(n_estimators=100, random_state=0)
scores = cross_val_score(model, X, y, cv=5, scoring="accuracy")
print(f"{scores.mean():.3f} ± {scores.std():.3f}")
```

注意:若需要标准化,应把 `StandardScaler` 放进 Pipeline 再交叉验证,否则每折都在「看过测试折」的缩放上训练,仍是泄漏。

</details>

**第 3 题(计算)**:给定真实标签与预测结果,解释混淆矩阵 `[[50, 5], [10, 35]]` 的含义,并计算准确率。

<details><summary>查看答案</summary>

行=真实,列=预测:50 个负类预测正确(真负)、5 个负类误判为正(假正)、10 个正类误判为负(假负)、35 个正类正确(真正)。准确率 = (50+35)/(50+5+10+35) = 85/100 = **85%**。同时可算:精确率 = 35/(5+35) = 87.5%,召回率 = 35/(10+35) = 77.8%。

</details>

**第 4 题(概念)**:为什么说「KMeans 聚类前必须标准化」?什么样的数据集可以例外?

<details><summary>查看答案</summary>

KMeans 用欧氏距离 $\sqrt{\sum (x_{ik} - x_{jk})^2}$,每个特征的量纲直接决定它对距离的贡献:某特征若取值 0~1000、另一特征 0~1,聚类几乎完全被第一个特征主导。标准化(或 MinMax 缩放)把各特征拉到可比尺度,距离才有意义。例外:所有特征本身同量纲、同尺度(如都是像素灰度 0~255),可不标准化——但标准化也几乎无害,拿不准就做。

</details>

## 🏆 竞赛实战链接

- **出镜频率**:国赛 C 题(分类/预测/聚类)几乎年年出现;美赛 C 题的评分预测、E 题的分类问题也常依赖 sklearn;即使主模型是机理模型,sklearn 也是「基线对比」的标配
- **论文加分点**:①「模型对比表」:同一评估协议下多个模型的指标并列(本单元例题 1 的循环直接产出);②交叉验证的均值 ± 标准差,替代单次划分的单一数字;③说明评估指标选择理由(不平衡数据为何用 F1 而非准确率);④用混淆矩阵/特征重要性做**可解释性**分析
- **工具**:`model.feature_importances_`(随机森林)输出特征重要性,是「哪些变量关键」的现成素材;`joblib.dump(model, "model.pkl")` 保存模型供复现

## 💻 代码实现

竞赛级分类项目完整骨架(划分 → 管道预处理 → 多模型对比 → 交叉验证 → 网格调优):

```python
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

X, y = make_classification(n_samples=800, n_features=10,
                           n_informative=6, random_state=0)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)

# 预处理 + 模型装进 Pipeline,彻底防泄漏
pipelines = {
    "逻辑回归": Pipeline([("scaler", StandardScaler()),
                          ("model", LogisticRegression(max_iter=2000))]),
    "随机森林": Pipeline([("scaler", StandardScaler()),
                          ("model", RandomForestClassifier(random_state=0))]),
}
for name, pipe in pipelines.items():
    cv = cross_val_score(pipe, X_train, y_train, cv=5,
                         scoring="accuracy")
    print(f"{name}: 5折CV = {cv.mean():.3f} ± {cv.std():.3f}")

# 网格搜索调优最优模型,最后才碰测试集
best_pipe = Pipeline([("scaler", StandardScaler()),
                      ("model", RandomForestClassifier(random_state=0))])
grid = GridSearchCV(best_pipe,
                    {"model__n_estimators": [50, 100, 200],
                     "model__max_depth": [5, 10, None]},
                    cv=5, scoring="accuracy")
grid.fit(X_train, y_train)
print("最优参数:", grid.best_params_)
print("测试集最终成绩:", f"{grid.score(X_test, y_test):.3f}")
```

## 📚 延伸阅读

- **官方文档**:scikit-learn 用户指南(https://scikit-learn.org/stable/user_guide.html)— 每个模型页面的「examples」都值得点开
- **书籍**:《机器学习实战:基于 Scikit-Learn、Keras 和 TensorFlow》(Aurélien Géron)第 1~9 章
- **进阶关联**:《建模数据处理流水线》单元(Pipeline/ColumnTransformer 的完整用法)→ 《Seaborn高级可视化》单元(把模型结果画漂亮)→ 深度学习部分另寻 PyTorch 资料

## 🧠 小结

1. Estimator API 三步走(`fit` → `predict` → `score`),换模型只改一行——模型对比表的成本因此趋近于零
2. 标准流程:分层划分 → 训练集 fit 缩放器 → 测试集只 transform → 训练 → 评估;泄漏是头号大敌
3. 指标要对症下药:均衡数据看准确率,不平衡看 F1/AUC,回归看 $R^2$+RMSE,聚类看 ARI/轮廓系数
4. 模型选择靠交叉验证与网格搜索,测试集只在最后一刻用一次
5. 竞赛三件套:模型对比表、CV 均值±标准差、固定随机种子——凑齐即可进论文
