# 建模数据处理流水线

> **难度**:实战 · **预计学习时长**:50 分钟 · **主讲智能体**:🧩 求解器 · **方法类别**:编程工具

## 🎯 学习目标

学完本单元,你应该能够:

- 用 `Pipeline` 把「预处理 → 特征工程 → 模型」串成一条流水线,彻底消除数据泄露
- 用 `ColumnTransformer` 对数值列与类别列分别定制处理
- 用 `FunctionTransformer` 封装自定义特征工程,并接入流水线与网格搜索
- 用 `GridSearchCV` 在流水线内部调参(掌握 `step__param` 双下划线语法)
- 用 `joblib` 保存整条流水线,保证训练与预测环境完全一致

## 📖 核心概念

### 1. 为什么需要流水线

回想《sklearn机器学习实战》单元的铁律:缩放器只能在训练集上 `fit`,测试集只 `transform`。当预处理步骤多起来(填充缺失 → 缩放 → 独热编码 → 降维 → 模型),手写这套「训练/测试两套动作」极易出错——**数据泄露是建模竞赛中最隐蔽、后果最严重的错误**。Pipeline 的解法:把每一步都装进一个对象,`fit`/`predict`/`transform` 由 sklearn 统一调度,交叉验证的每一折都在流水线内部完成正确的「训练时拟合、验证时只变换」。

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split

X, y = make_classification(n_samples=300, n_features=6, random_state=0)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42)

pipe = Pipeline([
    ("scaler", StandardScaler()),                    # 变换器:有 fit/transform
    ("model", LogisticRegression(max_iter=2000)),    # 估计器:有 fit/predict
])
pipe.fit(X_train, y_train)        # 内部:scaler 在训练集 fit_transform,再训模型
print("测试准确率:", f"{pipe.score(X_test, y_test):.3f}")
pipe.predict(X_test)              # 与训练时完全相同的预处理路径
```

### 2. ColumnTransformer:分列定制

真实赛题数据几乎都是「数值 + 类别」混合。`ColumnTransformer` 把列分成几组,每组挂一条处理链:

```python
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

rng = np.random.default_rng(0)
df = pd.DataFrame({
    "年龄": rng.normal(35, 10, 100).round(1),
    "收入": rng.normal(8, 3, 100).round(2),
    "学历": rng.choice(["高中", "本科", "硕士"], 100),
    "城市": rng.choice(["北京", "上海", "广州"], 100),
})
df.loc[:4, "年龄"] = np.nan                     # 注入少量缺失

preprocessor = ColumnTransformer([
    ("num", Pipeline([
        ("impute", SimpleImputer(strategy="median")),   # 数值:中位数填充
        ("scale", StandardScaler()),                    #       再标准化
    ]), ["年龄", "收入"]),
    ("cat", Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),  # 类别:众数填充
        ("onehot", OneHotEncoder(handle_unknown="ignore",
                                 sparse_output=False)),        #       再独热
    ]), ["学历", "城市"]),
])
X_processed = preprocessor.fit_transform(df)
print("新列名:", preprocessor.get_feature_names_out())
```

### 3. 自定义特征工程:FunctionTransformer

不是所有特征工程都有现成类。`FunctionTransformer` 把任意函数包装成变换器,接入流水线:

```python
from sklearn.preprocessing import FunctionTransformer
import numpy as np

log_shift = FunctionTransformer(
    lambda X: np.log1p(np.abs(X)),          # log(1+|x|),偏态数据取对数
    feature_names_out="one-to-one")
```

更复杂、需要学习数据统计量的变换(如「填充用训练集均值」),就写一个带 `fit`/`transform` 的类——这正是 sklearn 变换器的接口约定。

### 4. 流水线内的模型选择

`GridSearchCV` 的参数名用**双下划线**连接步骤名与参数名:

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.datasets import make_regression
from sklearn.model_selection import train_test_split, GridSearchCV

X, y = make_regression(n_samples=300, n_features=6, noise=10, random_state=0)
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)

pipe = Pipeline([("scaler", StandardScaler()), ("model", Ridge())])
grid = GridSearchCV(pipe,
                    {"model__alpha": [0.1, 1.0, 10.0],       # 模型参数
                     "scaler__with_mean": [True, False]},    # 预处理参数也可调
                    cv=5, scoring="r2")
grid.fit(X_train, y_train)
print(grid.best_params_, round(grid.best_score_, 3))
```

嵌套流水线(ColumnTransformer 里套 Pipeline)的参数名会很长,如 `preprocessor__num__impute__strategy`——用 `grid.estimator.get_params().keys()` 打印全部合法参数名,照着写。

### 5. 持久化:存整条流水线

```python
import joblib
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split

X, y = make_classification(n_samples=300, n_features=6, random_state=0)
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)
pipe = Pipeline([("scaler", StandardScaler()),
                 ("model", LogisticRegression(max_iter=2000))])
pipe.fit(X_train, y_train)

joblib.dump(pipe, "model_pipeline.pkl")      # 保存整条流水线
loaded = joblib.load("model_pipeline.pkl")
print("复现得分:", f"{loaded.score(X_test, y_test):.3f}")   # 与训练现场一致
```

只保存模型而丢掉预处理,预测时新数据会走「另一套」缩放/编码——经典翻车点。**流水线整体序列化**,训练与预测环境才真正一致。

## 🧮 核心 API 速查

| 任务 | API | 说明 |
|------|-----|------|
| 流水线 | `Pipeline([(name, step), ...])` | 最后一步必须是估计器 |
| 快速建线 | `make_pipeline(step1, step2, ...)` | 自动命名 |
| 分列处理 | `ColumnTransformer(transformers)` | `remainder="drop"` 丢弃其余列 |
| 缺失填充 | `SimpleImputer(strategy=)` | median / mean / most_frequent |
| 标准化 | `StandardScaler()` | 训练时 fit,预测时 transform |
| 独热编码 | `OneHotEncoder(handle_unknown="ignore", sparse_output=False)` | 新版本参数名 |
| 多项式特征 | `PolynomialFeatures(degree=, include_bias=False)` | 交互项与高次项 |
| 自定义变换 | `FunctionTransformer(func, feature_names_out=)` | 任意函数包装 |
| 并行分支 | `FeatureUnion([...])` | 多条特征链并联 |
| 流水线调参 | `GridSearchCV(pipe, {"step__param": [...]})` | 双下划线语法 |
| 序列化 | `joblib.dump / load` | 存整条流水线 |
| 缓存 | `Pipeline(steps, memory="./cache")` | 缓存中间变换,加速重复运行 |

## 💡 经典例题

### 例题 1:混合类型数据的完整预处理流水线

> 一份含 2 个数值列(有缺失)与 2 个类别列(有缺失)的调查数据。请构建 ColumnTransformer 完成「数值中位数填充 + 标准化」「类别众数填充 + 独热编码」,并输出处理后的形状与新列名。

**代码**:

```python
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

rng = np.random.default_rng(0)
n = 200
df = pd.DataFrame({
    "年龄": rng.normal(35, 10, n).round(1),
    "收入": rng.normal(8, 3, n).round(2),
    "学历": rng.choice(["高中", "本科", "硕士"], n),
    "城市": rng.choice(["北京", "上海", "广州"], n),
})
df.loc[rng.integers(0, n, 20), "年龄"] = np.nan    # 注入缺失
df.loc[rng.integers(0, n, 15), "学历"] = np.nan

num_cols = ["年龄", "收入"]
cat_cols = ["学历", "城市"]
preprocessor = ColumnTransformer([
    ("num", Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ]), num_cols),
    ("cat", Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore",
                                 sparse_output=False)),
    ]), cat_cols),
])

X_processed = preprocessor.fit_transform(df)
print("处理后形状:", X_processed.shape)
print("新列名:", preprocessor.get_feature_names_out().tolist())
print("数值部分均值(应≈0):", X_processed[:, :2].mean(axis=0).round(6))
```

**输出解读**:

```
处理后形状: (200, 8)
新列名: ['num__年龄', 'num__收入', 'cat__学历_本科', 'cat__学历_硕士',
       'cat__学历_高中', 'cat__城市_上海', 'cat__城市_北京', 'cat__城市_广州']
数值部分均值(应≈0): [-0. 0.]
```

解读:①2 个数值列保持 2 列,两个类别列(3 类 + 3 类)独热展开为 6 列,共 8 列——`get_feature_names_out` 直接给出论文附录可引用的新列名;②数值部分经标准化后均值恰为 0,说明 `StandardScaler` 正常工作;③`handle_unknown="ignore"` 保证预测时若出现训练集没见过的类别(如新城市「深圳」),编码器输出全 0 行而不是报错——这是部署场景的头号保险。这条流水线对任意「新数据」调用 `transform`,处理逻辑与训练时严格一致。

### 例题 2:数据泄露实证(两种预处理的对照)

> 用同一份数据做两个对照实验:(A) 在全量数据上先**标准化**再交叉验证 vs Pipeline 内标准化;(B) 在全量数据上先做**特征选择**(随机森林重要性)再交叉验证 vs Pipeline 内选择。量化两种预处理各自的泄漏虚高,回答:什么决定了泄漏的严重程度?

**代码**:

```python
import numpy as np
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import SelectFromModel
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

rng = np.random.default_rng(0)
n = 120
X = np.column_stack([rng.normal(0, 1, (n, 40)),   # 40 个噪声特征
                     rng.normal(0, 1, (n, 2))])   # 2 个信息特征
y = (X[:, 40] + X[:, 41] > 0).astype(int)

# 实验 A:标准化泄漏(均值/方差是稳定统计量,泄漏影响很小)
Xs = StandardScaler().fit_transform(X)
a_wrong = cross_val_score(LogisticRegression(max_iter=2000), Xs, y,
                          cv=5, scoring="accuracy")
a_right = cross_val_score(
    Pipeline([("scaler", StandardScaler()),
              ("model", LogisticRegression(max_iter=2000))]),
    X, y, cv=5, scoring="accuracy")
print(f"实验A 标准化: 错误 {a_wrong.mean():.3f} vs "
      f"正确 {a_right.mean():.3f}, "
      f"虚高 {(a_wrong.mean() - a_right.mean()) * 100:.2f} 个百分点")

# 实验 B:特征选择泄漏(选择器在噪声特征上过拟合,泄漏影响大)
def make_selector():
    return SelectFromModel(
        RandomForestClassifier(n_estimators=200, random_state=0),
        max_features=10, threshold=-np.inf)

X_sel = make_selector().fit(X, y).transform(X)
b_wrong = cross_val_score(LogisticRegression(max_iter=2000), X_sel, y,
                          cv=5, scoring="accuracy")
b_right = cross_val_score(
    Pipeline([("sel", make_selector()),
              ("model", LogisticRegression(max_iter=2000))]),
    X, y, cv=5, scoring="accuracy")
print(f"实验B 特征选择: 错误 {b_wrong.mean():.3f} vs "
      f"正确 {b_right.mean():.3f}, "
      f"虚高 {(b_wrong.mean() - b_right.mean()) * 100:.2f} 个百分点")
```

**输出解读**:

```
实验A 标准化: 错误 0.858 vs 正确 0.858, 虚高 0.00 个百分点
实验B 特征选择: 错误 0.950 vs 正确 0.933, 虚高 1.67 个百分点
```

结论很诚实:**泄漏的严重程度取决于预处理对数据的「记忆」程度**。标准化只用均值/方差这类稳定统计量,全量拟合与折内拟合几乎无差(虚高 0.00 个百分点);而特征选择会在 40 个噪声特征上「精挑细选」出恰好与测试折标签相关的特征(虚高 1.67 个百分点)。数据量越小、噪声特征越多、选择器越灵活,虚高越大。这个对照实验本身就是论文素材:「为保证评估无偏,所有预处理均在交叉验证折内完成」,并附上本实验的对比数字,评审会立刻明白你理解了模型评估的本质。既然 Pipeline 的防泄漏成本是**零**,就没有任何理由不用它。

### 例题 3:自定义特征工程 + 流水线调参(完整建模)

> 回归问题:特征偏态需取对数,再生成二次交互项,最后岭回归。请把「对数变换(FunctionTransformer)→ 多项式特征 → 标准化 → 岭回归」装进 Pipeline,用 GridSearchCV 同时调多项式阶数与正则系数,保存并复现最优流水线。

**代码**:

```python
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (FunctionTransformer, StandardScaler,
                                   PolynomialFeatures)
from sklearn.linear_model import Ridge
import joblib

rng = np.random.default_rng(0)
X = rng.lognormal(0, 0.8, size=(400, 5))        # 偏态特征(对数正态)
coef = np.array([3.0, -2.0, 1.5, 0.5, -1.0])
y = np.log1p(X) @ coef + rng.normal(0, 0.2, 400)  # 真实关系:对数变换后线性
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42)

pipe = Pipeline([
    ("log", FunctionTransformer(np.log1p, feature_names_out="one-to-one")),
    ("poly", PolynomialFeatures(degree=2, include_bias=False)),
    ("scale", StandardScaler()),
    ("model", Ridge()),
])

grid = GridSearchCV(pipe,
                    {"poly__degree": [1, 2],
                     "model__alpha": [0.1, 1.0, 10.0]},
                    cv=5, scoring="r2")
grid.fit(X_train, y_train)
print("最优参数:", grid.best_params_)
print("测试集 R²:", f"{grid.score(X_test, y_test):.3f}")

joblib.dump(grid.best_estimator_, "model_pipeline.pkl")   # 保存整条流水线
loaded = joblib.load("model_pipeline.pkl")
print("加载后复现 R²:", f"{loaded.score(X_test, y_test):.3f}")
print("流水线步骤:", [name for name, _ in loaded.steps])
```

**输出解读**:

```
最优参数: {'model__alpha': 0.1, 'poly__degree': 1}
测试集 R²: 0.986
加载后复现 R²: 0.986
流水线步骤: ['log', 'poly', 'scale', 'model']
```

四个工程要点:①`FunctionTransformer` 让自定义函数享受与 sklearn 组件完全相同的接口——对数变换被「固定」在流水线里,预测新数据时自动执行,**不会出现「训练时取了对数、预测时忘了取」**;②网格搜索「用数据说话」:真实关系在对数变换后本来就是线性的,所以 `degree=1` 胜出——不需要你预设多项式阶数;③`poly__degree` 与 `model__alpha` 一起在网格里搜索,6 组参数 × 5 折 = 30 次完整「预处理 + 训练」,每一次都在折内防泄漏地执行;④`joblib` 保存的是**整条流水线**(4 个步骤全在),加载后对测试集的得分与训练现场完全一致——这就是「可复现」的工程级实现。

## ⚠️ 常见易错点

1. **在流水线外 fit 任何变换器**。`scaler.fit(X)` 之后再进 CV,等于重演例题 2 的泄露;所有 `fit` 必须发生在流水线内部,由 `cross_val_score`/`GridSearchCV` 的折划分控制
2. **OneHotEncoder 用旧参数**。旧版参数 `sparse` 已废弃,新版是 `sparse_output`;接在 `StandardScaler` 后若忘记 `sparse_output=False`,会因稀疏矩阵与稠密矩阵混用报错
3. **测试集出现新类别**。不加 `handle_unknown="ignore"`,预测时未见过的类别直接报 ValueError;加了则编码为全 0 行(模型会保守处理)
4. **GridSearchCV 参数名写错**。必须 `步骤名__参数名`(双下划线);不确定时 `print(grid.estimator.get_params().keys())` 照抄,嵌套结构(ColumnTransformer 内套 Pipeline)的名字尤其长
5. **对测试集调用 `fit_transform`**。测试集上任何 `fit*` 都是在用测试数据「学习」预处理参数——测试集永远只 `transform`(或直接 `pipe.predict`,内部自动正确)
6. **只存模型不存流水线**。`joblib.dump(model)` 而预处理另存/不存,预测时预处理不一致,结果静默漂移;存就存 `pipe` 整体

## ✏️ 自测练习

**第 1 题(判断)**:下面代码哪里泄漏了?怎么改?

```python
from sklearn.datasets import make_classification
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from sklearn.linear_model import LogisticRegression

X, y = make_classification(n_samples=300, n_features=6, random_state=0)

scaler = StandardScaler().fit(X)        # 全量 fit(题目代码)
X_scaled = scaler.transform(X)
scores = cross_val_score(LogisticRegression(max_iter=2000), X_scaled, y, cv=5)
```

<details><summary>查看答案</summary>

`scaler.fit(X)` 用到了**全部数据**(包括每一折的验证部分),缩放参数泄漏了验证折的信息,CV 评估不再严格无偏。泄漏的虚高幅度取决于预处理对数据的敏感程度——标准化这类稳定统计量通常影响很小,特征选择这类「会记住数据」的操作影响明显(实测对照见例题 2)。改法:把 scaler 装进 Pipeline,`cross_val_score(Pipeline([("scaler", StandardScaler()), ("model", LogisticRegression())]), X, y, cv=5)`——每折的训练部分 fit 缩放器、验证部分只 transform,评估无偏。防泄漏的成本为零,没有理由不用 Pipeline。

</details>

**第 2 题(补全)**:写出「数值列(均值填充 + 标准化)与类别列(众数填充 + 独热)」的 ColumnTransformer。

<details><summary>查看答案</summary>

```python
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

num_cols = ["年龄", "收入"]
cat_cols = ["学历", "城市"]
pre = ColumnTransformer([
    ("num", Pipeline([("imp", SimpleImputer(strategy="mean")),
                      ("sc", StandardScaler())]), num_cols),
    ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                      ("ohe", OneHotEncoder(handle_unknown="ignore",
                                            sparse_output=False))]), cat_cols),
])
```

要点:每类列挂一条**完整子流水线**(先填充再变换,顺序不可反);`num_cols`/`cat_cols` 是列名列表,可用 `df.select_dtypes(include=np.number).columns` 自动生成数值列名。

</details>

**第 3 题(计算)**:流水线 `Pipeline([("scaler", StandardScaler()), ("model", Ridge())])`,用 GridSearchCV 调 `Ridge` 的 `alpha ∈ {0.1, 1}` 和 `StandardScaler` 的 `with_mean`,参数网格怎么写?

<details><summary>查看答案</summary>

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge

pipe = Pipeline([("scaler", StandardScaler()), ("model", Ridge())])
param_grid = {
    "model__alpha": [0.1, 1.0],
    "scaler__with_mean": [True, False],
}
```

双下划线把「步骤名」与「参数名」连起来;`scaler__with_mean=False` 适合稀疏矩阵场景。嵌套流水线(如 ColumnTransformer 内)写法更长,如 `pre__num__sc__with_mean`,用 `get_params().keys()` 核对。

</details>

**第 4 题(概念)**:为什么建议 `joblib.dump` 保存整条 Pipeline 而不是只保存模型?

<details><summary>查看答案</summary>

预测时的新数据必须经过**与训练完全相同的预处理**(同样的填充值、缩放均值/标准差、独热类别表)。只存模型意味着这些状态丢失或手写重建,一旦有出入(如训练时众数填充、预测时均值填充),特征分布漂移,预测静默变差。存整条 Pipeline,预处理状态与模型一起序列化,`load` 后直接 `predict`,训练/预测环境零漂移——这也是竞赛论文「可复现性」的工程保证。

</details>

## 🏆 竞赛实战链接

- **出镜频率**:国赛 C 题、美赛 C 题的数据建模流程,获奖论文几乎都有「数据处理流水线」小节;泄露错误的隐蔽性使它成为「模型分数高、盲测翻车」的头号原因
- **论文加分点**:①用流程图/列表展示流水线结构(数据 → 填充 → 缩放 → 编码 → 特征工程 → 模型);②附「有无流水线防泄漏」的 CV 对比实验(例题 2 的格式);③提交附录时给出 `joblib` 保存的流水线与复现脚本,注明 sklearn 版本
- **工具**:`pipe.named_steps` 检查每一步;`pipe.set_params(**grid.best_params_)` 直接更新;大型数据用 `Pipeline(memory="./cache")` 缓存中间变换,网格搜索提速明显

## 💻 代码实现

数据类赛题的完整工程模板(读取 → 分列处理 → 流水线 → 调参 → 保存):

```python
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.model_selection import GridSearchCV, cross_val_score
from sklearn.ensemble import RandomForestRegressor
import joblib

# ① 读数据(真实竞赛中: df = pd.read_csv("附件数据.csv"))
rng = np.random.default_rng(0)
df = pd.DataFrame({
    "数值1": rng.normal(0, 1, 300),
    "数值2": rng.normal(5, 2, 300),
    "类别": rng.choice(["A", "B", "C"], 300),
})
df["目标列"] = df["数值1"] * 2 + df["数值2"] * 0.5 + rng.normal(0, 0.5, 300)
target = df.pop("目标列")                              # ② 拆出目标
num_cols = df.select_dtypes(include=np.number).columns.tolist()
cat_cols = df.select_dtypes(include="object").columns.tolist()

pre = ColumnTransformer([                             # ③ 分列预处理
    ("num", Pipeline([("imp", SimpleImputer(strategy="median")),
                      ("sc", StandardScaler())]), num_cols),
    ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                      ("ohe", OneHotEncoder(handle_unknown="ignore",
                                            sparse_output=False))]), cat_cols),
])
pipe = Pipeline([("pre", pre),
                 ("model", RandomForestRegressor(random_state=0))])

grid = GridSearchCV(pipe,                             # ④ 流水线内调参
                    {"model__n_estimators": [100, 200],
                     "model__max_depth": [5, 10, None]},
                    cv=5, scoring="r2")
grid.fit(df, target)
print("最优参数:", grid.best_params_)
print("CV 得分:", f"{grid.best_score_:.3f}")

joblib.dump(grid.best_estimator_, "final_pipeline.pkl")   # ⑤ 整线保存
```

## 📚 延伸阅读

- **官方文档**:sklearn「Pipelines and composite estimators」(https://scikit-learn.org/stable/modules/compose.html)— ColumnTransformer 一节必读
- **泄漏专题**:sklearn 官方「Common pitfalls and recommended practices」——数据泄露的完整案例清单
- **姊妹单元**:《Pandas数据处理》(流水线上游的清洗)→《sklearn机器学习实战》(流水线下游的模型)→《Seaborn高级可视化》(流水线输出的呈现)

## 🧠 小结

1. Pipeline 把「预处理 → 特征工程 → 模型」封装成单一对象,`fit`/`predict` 自动走完一致路径——防泄漏不是靠自觉,而是靠结构
2. ColumnTransformer 按列分组处理:数值走「填充 + 缩放」,类别走「填充 + 独热」,`handle_unknown="ignore"` 保平安
3. FunctionTransformer 把任意函数变成流水线组件,自定义特征工程从此不游离在体系之外
4. 流水线内调参用 `step__param` 双下划线语法;嵌套名字用 `get_params().keys()` 核对
5. 序列化整条流水线(joblib),训练与预测环境零漂移——这是竞赛论文「可复现性」的工程底线
