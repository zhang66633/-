# Pandas数据处理

> **难度**:入门 · **预计学习时长**:45 分钟 · **主讲智能体**:🧩 求解器 · **方法类别**:编程工具

## 🎯 学习目标

学完本单元,你应该能够:

- 用 `read_csv` / `read_excel` 读取竞赛附件数据,并用 `info` / `describe` 快速摸清数据
- 完成缺失值处理、去重、类型转换、异常值修复四类数据清洗任务
- 用 `loc` / 布尔条件 / `query` 灵活筛选数据
- 用 `groupby` + `agg` 做分组聚合,用 `pivot_table` 做透视
- 处理日期型数据:`to_datetime`、`resample` 重采样、`rolling` 滑动窗口

## 📖 核心概念

### 1. Series 与 DataFrame

- **Series**:带索引的一维数组,类似「带标签的列」
- **DataFrame**:由多个 Series 拼成的二维表,行有索引(index)、列有列名(columns)

```python
import pandas as pd

df = pd.DataFrame({
    "城市": ["北京", "上海", "广州"],
    "GDP": [4.4, 4.7, 3.0],
    "人口": [2186, 2487, 1882],
})
print(df.info())          # 列类型与非空计数
print(df.describe())      # 数值列的统计量
print(df.head(2))         # 前两行
```

### 2. 读入数据的第一件事:摸清底细

拿到附件 .csv/.xlsx 后,先用三连摸清数据:`.head()` 看长相、`.info()` 看类型与缺失、`.describe()` 看数值分布。**读取阶段就要养成好习惯**:

```python
import io
import pandas as pd

# 真实竞赛中直接读附件文件:
# df = pd.read_csv("data.csv", encoding="utf-8")          # 中文文件常需指定编码
# df = pd.read_excel("data.xlsx", sheet_name="Sheet1")    # 多表时指定 sheet
# 常用参数: parse_dates=["日期"](日期列直接解析)、usecols(只读部分列)、index_col(指定索引)
raw = "日期,城市,温度\n2024-06-01,北京,25.3\n2024-06-02,上海,27.1\n"
df = pd.read_csv(io.StringIO(raw), parse_dates=["日期"])
print(df.dtypes)          # 确认「日期」已解析为 datetime64 类型
```

### 3. 数据清洗四件套

```python
import pandas as pd
import numpy as np

df = pd.DataFrame({
    "x": [1.0, np.nan, 3.0, 3.0, 5.0],
    "y": ["a", "b", "c", "c", "d"],
})

# (1) 缺失值
miss = df.isna().sum()                # 统计缺失
df2 = df.dropna(subset=["x"])         # 删除 x 缺失的行
df3 = df.fillna({"x": df["x"].mean()})  # 均值填充(按列指定)

# (2) 重复值
df4 = df.drop_duplicates(subset=["y"], keep="first")

# (3) 类型转换
df["x"] = df["x"].astype("float64")
df["y"] = df["y"].astype("category")

# (4) 异常值:超过 3σ 的替换为 NaN 再填充
mu, sd = df["x"].mean(), df["x"].std()
df.loc[(df["x"] - mu).abs() > 3 * sd, "x"] = np.nan
```

### 4. 筛选与排序

```python
import pandas as pd

df = pd.DataFrame({
    "地区": ["华东", "华南", "华北", "华东"],
    "销量": [120, 80, 60, 200],
    "利润": [12, 8, 5, 25],
})

# 列筛选
df[["地区", "销量"]]
# 行筛选:loc(标签)/ iloc(位置)/ 布尔条件 / query
df.loc[0, "销量"]              # 第 0 行「销量」列
df.iloc[1:3, 0:2]              # 位置切片
df[df["销量"] > 100]           # 布尔筛选
df.query("销量 > 100 and 地区 == '华东'")   # SQL 风格
# 排序
df.sort_values("利润", ascending=False)
```

### 5. GroupBy:分组-聚合

「**split → apply → combine**」三步:按键拆组、组内计算、结果合并。

```python
import pandas as pd

df = pd.DataFrame({
    "地区": ["华东", "华南", "华东", "华南"],
    "产品": ["A", "A", "B", "B"],
    "销量": [10, 20, 30, 40],
    "利润": [1, 2, 6, 8],
})

g = df.groupby("地区")                 # 分组对象
print(g["销量"].sum())                 # 各地区销量和
print(g.agg({"销量": ["mean", "max"], "利润": "sum"}))   # 多指标聚合
print(df.pivot_table(index="地区", columns="产品", values="销量", aggfunc="sum"))
```

### 6. 时间序列

```python
import pandas as pd
import numpy as np

idx = pd.date_range("2023-01-01", periods=365, freq="D")
s = pd.Series(np.arange(365) % 20 + 10, index=idx)

weekly = s.resample("W").mean()        # 按周重采样(降采样)
smooth = s.rolling(7, center=True).mean()   # 7 日滑动平均(平滑)
```

## 🧮 核心 API 速查

| 任务 | API | 说明 |
|------|-----|------|
| 读取 | `pd.read_csv / read_excel` | `encoding`、`parse_dates`、`usecols` 常用 |
| 摸底 | `df.info / describe / head` | 类型缺失 / 数值统计 / 预览 |
| 缺失值 | `df.isna / dropna / fillna` | 统计 / 删除 / 填充(method 按列字典) |
| 去重 | `df.drop_duplicates(subset=, keep="first")` | 按指定列去重 |
| 类型 | `df.astype` / `pd.to_numeric(errors="coerce")` | 转换;非法值转 NaN |
| 筛选 | `df.loc / iloc / query / isin` | 标签 / 位置 / SQL 风格 / 成员判断 |
| 排序 | `df.sort_values(by=, ascending=)` | 多列排序传列表 |
| 分组 | `df.groupby(cols).agg(dict)` | 支持多键分组、多指标聚合 |
| 透视 | `df.pivot_table(index, columns, values, aggfunc)` | 交叉表 |
| 合并 | `pd.merge(left, right, on=, how=)` / `pd.concat` | 按键连接 / 纵向堆叠 |
| 日期 | `pd.to_datetime / resample / rolling` | 解析 / 重采样 / 滑动窗口 |
| 导出 | `df.to_csv / to_excel(index=False)` | 结果回写附件 |

## 💡 经典例题

### 例题 1:气象数据清洗全流程

> 附件数据(模拟)存在四类问题:重复记录、缺失值、日期列为字符串、混入异常温度(99.9)。请完成清洗,并给出清洗前后的行数、缺失数与温度均值。

**代码**:

```python
import io
import pandas as pd
import numpy as np

raw = """日期,城市,温度,湿度,风速
2024-06-01,北京,25.3,60,3.2
2024-06-01,上海,27.1,75,2.8
2024-06-01,北京,25.3,60,3.2
2024-06-02,北京,,61,3.5
2024-06-02,上海,28.0,,3.1
2024-06-03,北京,25.9,58,
2024-06-03,广州,99.9,80,2.2
2024-06-04,北京,26.1,59,3.0
2024-06-04,广州,29.0,82,2.5
"""
df = pd.read_csv(io.StringIO(raw))
print(f"清洗前: {len(df)} 行,缺失 {df.isna().sum().sum()} 个")

# ① 去重
df = df.drop_duplicates()
# ② 日期列转类型
df["日期"] = pd.to_datetime(df["日期"])
# ③ 异常值:温度 > 50 视为传感器故障,置 NaN 后按城市均值填充
df.loc[df["温度"] > 50, "温度"] = np.nan
df["温度"] = df.groupby("城市")["温度"].transform(
    lambda s: s.fillna(s.mean()))
# ④ 其余缺失:湿度/风速用整体均值填充
df["湿度"] = df["湿度"].fillna(df["湿度"].mean())
df["风速"] = df["风速"].fillna(df["风速"].mean())

print(f"清洗后: {len(df)} 行,缺失 {df.isna().sum().sum()} 个")
print(f"温度均值: {df['温度'].mean():.2f}")
print(df.to_string(index=False))
```

**输出解读**:

```
清洗前: 9 行,缺失 3 个
清洗后: 8 行,缺失 0 个
温度均值: 27.02
        日期  城市        温度        湿度  风速
 2024-06-01  北京  25.300000  60.000000  3.2
 2024-06-01  上海  27.100000  75.000000  2.8
 2024-06-02  北京  25.766667  61.000000  3.5
 2024-06-02  上海  28.000000  67.857143  3.1
 2024-06-03  北京  25.900000  58.000000  2.9
 2024-06-03  广州  29.000000  80.000000  2.2
 2024-06-04  北京  26.100000  59.000000  3.0
 2024-06-04  广州  29.000000  82.000000  2.5
```

三个细节值得记住:①`groupby(...).transform` 与 `fillna` 组合实现「按组填充」,这是比整体填充更精细的策略;②异常值先置 NaN 再走缺失值流程,统一处理;③清洗后统计量(均值 27.02)已经剔除了 99.9 这个离群值的干扰。真实的赛题数据比这脏得多,但这四步(去重、类型、异常、缺失)是通用骨架。

### 例题 2:销售数据分组聚合与透视

> 某公司给出 200 条销售记录(月份、地区、销量、单价)。求:(1) 各地区的总销量与平均销售额;(2) 按「地区 × 月份」的销售额透视表,找出销售额最高的组合。

**代码**:

```python
import pandas as pd
import numpy as np

rng = np.random.default_rng(5)
n = 200
df = pd.DataFrame({
    "月份": rng.integers(1, 13, n),
    "地区": rng.choice(["华东", "华南", "华北", "西南"], n),
    "销量": rng.integers(10, 200, n),
    "单价": rng.normal(30, 5, n).round(2),
})
df["销售额"] = df["销量"] * df["单价"]

# (1) 分组聚合:同一列多指标 + 多列不同指标
summary = df.groupby("地区").agg(
    总销量=("销量", "sum"),
    平均销售额=("销售额", "mean"),
    订单数=("销售额", "count"),
).round(2)
print(summary)

# (2) 透视表:地区 × 月份 → 销售额之和
pivot = df.pivot_table(index="地区", columns="月份",
                       values="销售额", aggfunc="sum",
                       fill_value=0)
best = pivot.stack().idxmax()        # 找出最大销售额的 (地区, 月份)
best = (best[0], int(best[1]))
print("\n销售额最高的组合:", best, "=", round(pivot.loc[best], 2))
print("\n透视表(前 4 行):")
print(pivot.round(0).head(4))
```

**输出解读**:

```
        总销量  平均销售额  订单数
地区
华东   5217   2998.94    53
华北   5326   3221.75    50
华南   5741   2993.58    58
西南   4450   3439.12    39

销售额最高的组合: ('华北', 2) = 28449.36

透视表(前 4 行):
月份      1       2        3       4    ...
地区
华东  12904.0   7269.0  12623.0  12646.0  ...
华北   4491.0  28449.0  17065.0  14189.0  ...
华南  15749.0  22052.0   7903.0  16726.0  ...
西南  13739.0   3830.0   9892.0  10402.0  ...
```

`agg` 的新式写法 `agg(新列名=("原列", "函数"))` 直接给结果列命名,比旧式字典更直观。透视表把「长表」变「宽表」,正是论文里二维表格的生成方式;`pivot.stack().idxmax()` 一行定位最大值所在组合,是「透视 + 反透视」的典型用法。

### 例题 3:时间序列重采样与平滑

> 某城市 2023 年逐日气温(含噪声)已存为时间索引序列。请:(1) 重采样为周均值;(2) 计算 7 日中心滑动平均;(3) 对比原始序列与平滑序列的方差——平滑是建模前常用的降噪手段。

**代码**:

```python
import pandas as pd
import numpy as np

rng = np.random.default_rng(0)
idx = pd.date_range("2023-01-01", "2023-12-31", freq="D")
base = 15 + 12 * np.sin(2 * np.pi * np.arange(len(idx)) / 365 - np.pi / 2)
temp = pd.Series(base + rng.normal(0, 2, len(idx)), index=idx)

weekly = temp.resample("W").mean()              # 周均值
smooth = temp.rolling(7, center=True).mean()    # 7 日中心滑动平均

print(f"原始序列: 均值 {temp.mean():.2f}, 标准差 {temp.std():.2f}")
print(f"7日平滑后: 均值 {smooth.mean():.2f}, 标准差 {smooth.std():.2f}")
print(f"周均值序列长度: {len(weekly)} 个点")
print("原始前 3 天:", temp.head(3).round(2).tolist())
print("平滑前 3 天:", smooth.head(3).round(2).tolist())   # 中心滑动,头部为 NaN
```

**输出解读**:

```
原始序列: 均值 14.94, 标准差 8.65
7日平滑后: 均值 15.13, 标准差 8.37
周均值序列长度: 53 个点
原始前 3 天: [3.25, 2.74, 4.29]
平滑前 3 天: [nan, nan, nan]
```

两个发现:①滑动平均**几乎不改变均值**,但压低了标准差(噪声被抹平)——这是低通滤波的直觉;②`center=True` 的中心滑动平均在序列两端会产生 NaN,画图前需要 `dropna()` 或改用 `center=False`。竞赛中「原始数据 → 滑动平滑 → 建模」是标准链路,但论文里必须说明平滑窗口的选取依据(如 7 天对应周周期)。

## ⚠️ 常见易错点

1. **链式赋值无效**。`df[df['x'] > 0]['y'] = 1` 会触发 SettingWithCopyWarning 且**不生效**;必须用 `df.loc[df['x'] > 0, 'y'] = 1` 一步到位
2. **`inplace=True` 依赖症**。`df.dropna(inplace=True)` 风格在 pandas 3.x 已被官方不推荐,且链式操作时容易「改了不知道改没改」;统一用 `df = df.dropna()` 赋值式写法
3. **日期列当字符串用**。不 `parse_dates` / `to_datetime` 就直接 `resample` 会报错;时间类操作前先确认 `df.dtypes` 里是 `datetime64[ns]`
4. **groupby 后直接取列再聚合**。`df.groupby('地区')['销量'].sum()` 只聚合一列;要聚合多列用 `agg` 字典/新式命名写法,而不是循环调多次
5. **merge 默认 inner 丢数据**。`pd.merge` 默认 `how='inner'` 只保留两表共有的键;清洗阶段合并多张表时先 `how='left'` 再检查缺失,避免「数据被悄悄丢掉」
6. **删缺失值太豪爽**。`dropna()` 可能一刀切掉 30% 的数据;先看 `df.isna().sum()` 与缺失比例,能填充的(均值/中位数/前向)就别删,删除前在论文里说明理由

## ✏️ 自测练习

**第 1 题(判断)**:`df[df['x'] > 0]['y'] = 0` 为什么无效?正确写法是什么?

<details><summary>查看答案</summary>

`df[df['x'] > 0]` 先返回了一个**中间副本**,再对副本的 `['y']` 赋值,原 DataFrame 不受影响(并发出 SettingWithCopyWarning)。正确写法是 `df.loc[df['x'] > 0, 'y'] = 0`,布尔掩码与列选择在同一次 `loc` 中完成。

</details>

**第 2 题(补全)**:用 groupby 同时求每个地区「销量的均值」和「利润的总和」,并给结果列起名 `平均销量`、`总利润`。

<details><summary>查看答案</summary>

```python
import pandas as pd

df = pd.DataFrame({"地区": ["华东", "华南", "华东", "华南"],
                   "销量": [10, 20, 30, 40],
                   "利润": [1, 2, 6, 8]})
df.groupby("地区").agg(
    平均销量=("销量", "mean"),
    总利润=("利润", "sum"),
)
```

新式命名元组写法自 pandas 0.25 起可用,比旧式 `agg({"销量": "mean"})` 更能控制输出列名。

</details>

**第 3 题(计算)**:对逐日时间序列 `s`(索引为 DatetimeIndex)求 5 日滑动平均,并说明结果前 4 个值为何是 NaN。

<details><summary>查看答案</summary>

```python
import pandas as pd
import numpy as np

s = pd.Series(np.arange(30) % 10 + 1.0,
              index=pd.date_range("2023-01-01", periods=30, freq="D"))
s.rolling(5, center=True).mean()
```

默认 `center=False` 时窗口需要 5 个历史值,前 4 个位置窗口不满,结果为 NaN。取 `center=True` 则改为前后各 2 天,NaN 出现在两端。两种方式的平滑曲线整体相差不大,论文画图时通常 `dropna()` 后再画。

</details>

**第 4 题(概念)**:`merge` 的 `how='inner' / 'left' / 'outer'` 三者区别?

<details><summary>查看答案</summary>

- `inner`:只保留两表键**共有**的行(交集),最易丢数据
- `left`:保留左表全部行,右表键匹配不上填 NaN(最常用于「主表 + 补充表」)
- `outer`:保留两表全部行(并集),缺失填 NaN,适合合并后检查覆盖情况

合并后立刻 `df.isna().sum()` 检查新增缺失,是防止静默丢数据的习惯。

</details>

## 🏆 竞赛实战链接

- **出镜频率**:国赛每年至少一道题以「附件表格数据」为核心(A/C 题几乎必考);美赛 C 题数据量大,常需多表合并与透视
- **论文加分点**:①「数据预处理」小节给出**清洗前后的对比表**(行数、缺失数、统计量);②说明异常值判定准则(如 3σ)与缺失值填充方法的理由;③中间统计表用 `to_markdown()` 或直接制表输出,保持论文表格式一致
- **工具**:`df.to_csv("result.csv", index=False)` 把结果回写;`df.to_markdown()` 快速生成论文表格草稿

## 💻 代码实现

竞赛数据处理的完整骨架(读入 → 摸底 → 清洗 → 聚合 → 导出):

```python
import pandas as pd
import numpy as np

# 1. 读入(编码、日期列一次到位;此处用模拟数据代替附件)
rng = np.random.default_rng(0)
idx = pd.date_range("2024-01-01", periods=200, freq="D")
df = pd.DataFrame({
    "日期": idx,
    "城市": rng.choice(["北京", "上海", "广州"], 200),
    "温度": rng.normal(25, 6, 200).round(1),
})

# 2. 摸底
print(df.info())
print(df.describe().round(2))
print("缺失情况:\n", df.isna().sum())

# 3. 清洗
df = df.drop_duplicates()
df.loc[df["温度"] > 50, "温度"] = np.nan
df["温度"] = df.groupby("城市")["温度"].transform(lambda s: s.fillna(s.mean()))
df = df.fillna(df.mean(numeric_only=True))

# 4. 派生列 + 聚合
df["月"] = df["日期"].dt.month
result = df.groupby(["城市", "月"]).agg(
    平均温度=("温度", "mean"),
    观测数=("温度", "count"),
).reset_index()

# 5. 导出
result.to_csv("result.csv", index=False)
print(result.head())
```

## 📚 延伸阅读

- **官方文档**:Pandas 用户指南「10 minutes to pandas」(https://pandas.pydata.org/docs/user_guide/10min.html)
- **书籍**:Wes McKinney《利用 Python 进行数据分析》第 3 版——Pandas 创始人之作
- **进阶关联**:学完本单元 → 《Matplotlib数据可视化》与《Seaborn高级可视化》(把清洗后的数据画出来)→ 《建模数据处理流水线》(把清洗流程工程化、防泄漏)

## 🧠 小结

1. 读入数据先「三连摸底」:`head` 看长相、`info` 看类型缺失、`describe` 看分布
2. 清洗四件套:去重、类型转换、异常值、缺失值;顺序通常是「去重 → 类型 → 异常置缺 → 填充」
3. 筛选用 `loc` + 布尔掩码一步到位,远离链式赋值;聚合用 `groupby + agg` 新式命名写法
4. 时间数据三件套:`to_datetime` 解析、`resample` 重采样、`rolling` 平滑,是国赛 C 类题的高频操作
5. 每一步清洗都留下「前后对比」证据,论文的「数据处理」小节就水到渠成
