# networkx图论编程

> **难度**:进阶 · **预计学习时长**:45 分钟 · **主讲智能体**:🧩 求解器 · **方法类别**:编程工具

## 🎯 学习目标

学完本单元,你应该能够:

- 用 `Graph` / `DiGraph` 构建带属性的网络,区分有向与无向场景
- 调用 Dijkstra 求带权最短路径,输出完整路径与总长度
- 求解最小生成树(成本最小连通方案)与最大流(容量网络瓶颈分析)
- 用连通分量与中心性指标分析网络的鲁棒性与关键节点
- 用 networkx 绘制论文级的网络图

## 📖 核心概念

### 1. 图的两种基本类型

- **`nx.Graph`**:无向图,边没有方向——道路、光缆、社交关系
- **`nx.DiGraph`**:有向图,边有方向——水流、物流、依赖关系

```python
import networkx as nx

G = nx.Graph()
G.add_node("北京", population=2186)          # 节点可带属性
G.add_edges_from([("北京", "上海"), ("上海", "广州")])
G.add_weighted_edges_from([("北京", "上海", 1213),
                           ("上海", "广州", 1458)])   # 边可带权重
print("节点数:", G.number_of_nodes(), "边数:", G.number_of_edges())
```

### 2. 最短路径:Dijkstra 及其家族

```python
import networkx as nx

G = nx.Graph()
G.add_weighted_edges_from([
    ("A", "B", 2), ("A", "C", 5), ("B", "C", 1), ("B", "D", 4), ("C", "D", 2),
])

path = nx.dijkstra_path(G, "A", "D", weight="weight")
length = nx.dijkstra_path_length(G, "A", "D", weight="weight")
print("路径:", path, "长度:", length)     # ['A', 'B', 'C', 'D'] 5

# 无权(所有边长度 1)用 BFS
print(nx.shortest_path(G, "A", "D"))     # 不传 weight 即无权
```

- **单源**:`dijkstra_path(G, source, target, weight=)`
- **多源**:`multi_source_dijkstra`(多起点,选址问题的利器)
- **全对**:`floyd_warshall(G)` 或 `all_pairs_dijkstra`,用于「任意两点间距离矩阵」

### 3. 最小生成树与最大流

```python
import networkx as nx

# 最小生成树:连通所有点的最小总成本
G = nx.Graph()
G.add_weighted_edges_from([("A", "B", 3), ("A", "C", 4),
                           ("B", "C", 1), ("B", "D", 5), ("C", "D", 2)])
mst = nx.minimum_spanning_tree(G)
print("MST 边:", [(u, v, d["weight"]) for u, v, d in mst.edges(data=True)])

# 最大流:容量网络从源到汇的最大流量
D = nx.DiGraph()
D.add_weighted_edges_from([("s", "a", 10), ("s", "b", 5),
                           ("a", "b", 3), ("a", "t", 8), ("b", "t", 7)],
                          weight="capacity")
flow_value, flow_dict = nx.maximum_flow(D, "s", "t", capacity="capacity")
print("最大流:", flow_value)             # 15
```

### 4. 连通性与中心性

```python
import networkx as nx

G = nx.erdos_renyi_graph(30, 0.1, seed=0)
print("连通分量数:", nx.number_connected_components(G))
print("最大连通片规模:", max(len(c) for c in nx.connected_components(G)))

# 中心性:谁是关键节点?
dc = nx.degree_centrality(G)            # 度中心性:连接了多少邻居
bc = nx.betweenness_centrality(G)       # 介数中心性:多少条最短路径经过它
print("度中心性最高节点:", max(dc, key=dc.get))
print("介数中心性最高节点:", max(bc, key=bc.get))
```

### 5. 网络可视化

```python
import matplotlib.pyplot as plt
import networkx as nx

G = nx.erdos_renyi_graph(15, 0.25, seed=1)
pos = nx.spring_layout(G, seed=42)      # 力导向布局,固定种子使图可复现
fig, ax = plt.subplots(figsize=(7, 5))
nx.draw(G, pos, ax=ax, node_size=400, node_color="steelblue",
        with_labels=True, font_color="white")
ax.set_title("随机网络结构")
fig.savefig("network.png", dpi=200)
```

## 🧮 核心 API 速查

| 任务 | API | 说明 |
|------|-----|------|
| 建图 | `nx.Graph()` / `nx.DiGraph()` | 无向 / 有向 |
| 加边 | `add_edge` / `add_edges_from` / `add_weighted_edges_from` | 权重默认存为 `"weight"` |
| 最短路径 | `nx.dijkstra_path(G, s, t, weight=)` | 返回节点列表 |
| 路径长度 | `nx.dijkstra_path_length(G, s, t, weight=)` | 返回数值 |
| 全对距离 | `nx.all_pairs_dijkstra(G, weight=)` | 距离矩阵素材 |
| 最小生成树 | `nx.minimum_spanning_tree(G, weight=)` | 返回新图 |
| 最大流 | `nx.maximum_flow(G, s, t, capacity=)` | 返回 (流值, 流字典) |
| 最小割 | `nx.minimum_cut(G, s, t, capacity=)` | 返回 (割值, 割集) |
| 连通分量 | `nx.connected_components(G)` | 无向图;有向图用 `strongly_connected_components` |
| 中心性 | `degree_centrality` / `betweenness_centrality` | 关键节点分析 |
| 聚类系数 | `nx.average_clustering(G)` | 网络「抱团」程度 |
| 随机图 | `nx.erdos_renyi_graph(n, p, seed=)` | 测试用 |
| 绘图 | `nx.draw(G, pos, ax=)` + `spring_layout(seed=)` | OO 风格出图 |

## 💡 经典例题

### 例题 1:城市间最短路径(交通网络)

> 某地区 6 个城市间的公路里程(双向)如代码所示。求从 A 到 F 的最短路径与总里程,并输出 A 到所有城市的最短距离表。

**代码**:

```python
import networkx as nx

G = nx.Graph()
G.add_weighted_edges_from([
    ("A", "B", 120), ("A", "C", 150), ("B", "D", 100),
    ("C", "D", 80), ("B", "E", 200), ("D", "E", 90),
    ("C", "F", 110), ("E", "F", 70),
])

path = nx.dijkstra_path(G, "A", "F", weight="weight")
length = nx.dijkstra_path_length(G, "A", "F", weight="weight")
print(f"最短路径: {' → '.join(path)},总里程 {length} km")

dist, _ = nx.single_source_dijkstra(G, "A", weight="weight")
print("A 到各城市最短距离:", {k: v for k, v in sorted(dist.items())})
```

**输出解读**:

```
最短路径: A → C → F,总里程 260 km
A 到各城市最短距离: {'A': 0, 'B': 120, 'C': 150, 'D': 220, 'E': 310, 'F': 260}
```

直接走 A→B→D→E→F 是 380 km,但 Dijkstra 找到了经 C 的绕行路线(260 km)——**最短 ≠ 最少边数**,这正是带权最短路径与 BFS 的区别。`single_source_dijkstra` 一次给出源点到所有点的最短距离,这张表就是论文里的「距离矩阵」;若进一步按城市规模加权(需求量 × 距离),就演变为选址问题(参见《scipy.optimize求解优化问题》单元)。

### 例题 2:供水网络最大流与瓶颈分析

> 某供水系统:水源到 A、B 两个加压站(容量 16、13),A↔B 有双向管道(10、4),A→C(12)、B→D(14)、C→D(9)、C→汇(20)、D→汇(7)。求源到汇的最大流量,并找出「满载」的瓶颈管道。

**代码**:

```python
import networkx as nx

G = nx.DiGraph()
G.add_weighted_edges_from([
    ("源", "A", 16), ("源", "B", 13),
    ("A", "B", 10), ("B", "A", 4),
    ("A", "C", 12), ("B", "D", 14),
    ("C", "D", 9), ("C", "汇", 20), ("D", "汇", 7),
], weight="capacity")

val, flow = nx.maximum_flow(G, "源", "汇", capacity="capacity")
bottlenecks = [(u, v) for u, v, d in G.edges(data=True)
               if flow[u][v] == d["capacity"]]
print("最大流量:", val)
print("瓶颈(满载)管道:", bottlenecks)

cut_val, partition = nx.minimum_cut(G, "源", "汇", capacity="capacity")
print("最小割容量:", cut_val, "割集:", partition)
```

**输出解读**:

```
最大流量: 19
瓶颈(满载)管道: [('A', 'C'), ('D', '汇')]
最小割容量: 19 割集: ({'B', '源', 'A', 'D'}, {'汇', 'C'})
```

最大流 19 = 最小割容量 19——**最大流最小割定理**的数值验证。瓶颈分析的意义在于改造决策:管道 A→C 与 D→汇 满载,扩容这两条管道才能提升总供水量,而扩容其他管道毫无用处。这种「瓶颈定位」是网络类赛题(供水、供电、通信)论文中最有说服力的段落:`minimum_cut` 直接输出割集,把「卡脖子位置」讲清楚。

### 例题 3:光缆铺设与网络鲁棒性

> 某大学 5 个校区之间铺设光缆,两两铺设成本(万元)如代码所示。求:(1) 连通全部校区的最小成本方案(最小生成树);(2) 若按「逐个移除度数最高节点」模拟故障,最大连通片规模如何衰减(网络鲁棒性)。

**代码**:

```python
import networkx as nx

G = nx.Graph()
G.add_weighted_edges_from([
    ("校区A", "校区B", 8), ("校区A", "校区C", 5),
    ("校区B", "校区C", 10), ("校区B", "校区D", 2),
    ("校区C", "校区D", 3), ("校区C", "校区E", 7),
    ("校区D", "校区E", 4),
])
mst = nx.minimum_spanning_tree(G)
cost = sum(d["weight"] for _, _, d in mst.edges(data=True))
print("最小生成树边:", [(u, v, w) for u, v, w in
                      sorted((u, v, d["weight"])
                             for u, v, d in mst.edges(data=True))])
print("总成本:", cost, "万元")

# 鲁棒性:反复移除当前度数最高的节点,记录最大连通片规模
H = G.copy()
sizes = [max(len(c) for c in nx.connected_components(H))]
for _ in range(3):
    hub = max(H.degree, key=lambda t: t[1])[0]
    H.remove_node(hub)
    sizes.append(max(len(c) for c in nx.connected_components(H)))
print("移除度数最高节点后,最大连通片规模变化:", sizes)
```

**输出解读**:

```
最小生成树边: [('校区A', '校区C', 5), ('校区B', '校区D', 2),
             ('校区C', '校区D', 3), ('校区D', '校区E', 4)]
总成本: 14 万元
移除度数最高节点后,最大连通片规模变化: [5, 4, 2, 1]
```

(1) 最小生成树总成本 14 万元:贪心策略「永远先连最便宜的边、不成环」即 Kruskal 算法,networkx 默认实现的就是它;(2) 鲁棒性模拟显示:打掉度数最高的枢纽校区 D 后,网络立刻碎成三片,最大连通片从 5 骤降到 2——枢纽节点的存亡决定全局连通性。这个「打节点」实验是网络脆弱性分析的标准操作,把 `degree` 换成 `betweenness_centrality` 还可以对比「按介数攻击」与「按度数攻击」的效果差异,是网络赛题的高级加分点。

## ⚠️ 常见易错点

1. **无向/有向用错**。公路、光缆、社交关系是 `Graph`;水流、物流、资金流是 `DiGraph`。有向图里 `dijkstra_path(G, s, t)` 与 `dijkstra_path(G, t, s)` 结果不同,路径可能不存在
2. **权重属性名不统一**。默认权重键是 `"weight"`;若边属性存的是 `"distance"` / `"length"`,必须显式传 `weight="distance"`,否则 Dijkstra 退化成「数边数」,结果完全错误
3. **最大流忘记容量属性**。`maximum_flow` 不传 `capacity` 参数时,无边容量属性视为**无限容量**——得到的「最大流」毫无意义;`add_weighted_edges_from(..., weight="capacity")` 一步把权重存成容量键
4. **目标不可达没处理**。不连通的图上 `dijkstra_path` 抛 `NetworkXNoPath` 异常;先 `nx.has_path(G, s, t)` 或按连通分量分组处理
5. **节点编号混乱**。节点是任意可哈希对象(整数、字符串、坐标元组);但「节点 i 就是下标 i」只在显式编号时成立,`G.nodes` 是节点集合不是下标列表
6. **大图直接 `nx.draw`**。节点上千时默认布局又慢又糊;先抽子图/聚合社区,布局用 `spring_layout(seed=)` 固定,论文里标注「节点大小 ∝ 度数」等图例说明

## ✏️ 自测练习(选择题)

**第 1 题**

```python
import networkx as nx
G = nx.Graph()
G.add_weighted_edges_from([
    ("A", "B", 120), ("A", "C", 150), ("B", "D", 100),
    ("C", "D", 80), ("B", "E", 200), ("D", "E", 90),
    ("C", "F", 110), ("E", "F", 70),
], weight="length")            # 里程存进 "length" 属性
print(nx.dijkstra_path_length(G, "A", "F"))   # 忘了传 weight="length"
```

输出是:

A. 2
B. 260
C. 380
D. 抛 NetworkXNoPath

<details><summary>查看答案与解析</summary>
**答案:A**。默认权重键是 `"weight"`,而这里里程存进了 `"length"` 属性;不传 weight 参数时,Dijkstra 把所有边按权重 1 处理,退化成「数边数」——A→C→F 只经过 2 条边,返回 2。正确写法 `weight="length"` 得到 260(A→C→F,150+110);380 是 A→B→D→E→F 的加权里程(一条看似「顺路」但更长的路径);图是连通的,不会抛 NetworkXNoPath。属性名与默认键不一致时忘记显式传 weight,得到的是「边数最少」而不是「里程最短」,结果完全错误。
</details>

**第 2 题** 供水管网建模:水从水源经管道流向汇点,管道容量有方向性。应使用:

A. nx.Graph
B. nx.DiGraph
C. 两者等价,结果相同
D. nx.MultiGraph

<details><summary>查看答案与解析</summary>
**答案:B**。水沿管道**单向**流动,必须用 `nx.DiGraph`(有向图)。`nx.Graph` 无向图允许反向流动,最大流结果会错误;「两者等价」错误——有向图中 `dijkstra_path(G, s, t)` 与 `dijkstra_path(G, t, s)` 可能不同甚至无路;`MultiGraph` 用于两节点间有多条平行边的场景,与方向性无关。判断口诀:信息/物质能否沿边反向流动——公路、光缆用 Graph,水流、物流、资金流用 DiGraph。
</details>

**第 3 题** 建图时把容量存进了默认的 `"weight"` 键,随后调用 `nx.maximum_flow(D, "s", "t")`(未显式传 `capacity` 参数),会发生什么?

A. 自动读取 "weight" 属性作为容量,结果正确
B. 与显式传 capacity="weight" 的结果完全一致
C. 静默返回一个偏大的荒谬值
D. 边缺少 "capacity" 属性,检测到无限容量路径,抛 NetworkXUnbounded

<details><summary>查看答案与解析</summary>
**答案:D**。`maximum_flow` 默认找 `"capacity"` 属性;边没有该属性时容量被当作**无穷大**,存在无限容量的 s-t 路径时直接抛 `NetworkXUnbounded`(networkx 3.x 实跑验证)。它既不会自动读取 "weight",也不会静默给出结果——但数据已经「错了」:正确姿势是 `add_weighted_edges_from(..., weight="capacity")` 把权重存成容量键,再 `nx.maximum_flow(D, "s", "t", capacity="capacity")`。这与 Dijkstra 的 weight 键陷阱是同一类错误。
</details>

## 🏆 竞赛实战链接

- **出镜频率**:物流配送(国赛 B 题)、交通规划、电力/供水网络、社交网络舆论传播(美赛 C/D)都涉及图模型;最短路径、MST、最大流是三大基础问题
- **论文加分点**:①网络图可视化:`nx.draw` 出的结构图 + 最短路径高亮;②瓶颈/最小割分析,把「该改造哪里」讲清楚;③中心性指标(介数)识别关键节点,与灵敏度分析呼应
- **工具**:`nx.to_pandas_edgelist(G)` 把图导出为 DataFrame 交给 Pandas 分析;`nx.write_gexf` 可导出供 Gephi 做更精美的大图可视化

## 💻 代码实现

三大问题的完整骨架汇总:

```python
import networkx as nx

# ---- 最短路径 ----
G = nx.Graph()
G.add_weighted_edges_from([("A", "B", 120), ("A", "C", 150),
                           ("C", "F", 110), ("E", "F", 70)])
print("最短路径:", nx.dijkstra_path(G, "A", "F", weight="weight"))

# ---- 最小生成树 ----
mst = nx.minimum_spanning_tree(G)
print("MST 总权重:", sum(d["weight"] for _, _, d in mst.edges(data=True)))

# ---- 最大流 + 最小割 ----
D = nx.DiGraph()
D.add_weighted_edges_from([("s", "a", 10), ("s", "b", 5),
                           ("a", "b", 3), ("a", "t", 8), ("b", "t", 7)],
                          weight="capacity")
val, flow = nx.maximum_flow(D, "s", "t", capacity="capacity")
cut, part = nx.minimum_cut(D, "s", "t", capacity="capacity")
print("最大流:", val, "最小割:", cut)

# ---- 网络鲁棒性:移除枢纽后最大连通片 ----
H = G.copy()
hub = max(H.degree, key=lambda t: t[1])[0]
H.remove_node(hub)
print("移除枢纽后最大连通片:",
      max(len(c) for c in nx.connected_components(H)))
```

## 📚 延伸阅读

- **官方文档**:networkx 教程(https://networkx.org/documentation/stable/tutorial.html)与算法库参考(https://networkx.org/documentation/stable/reference/algorithms/index.html)
- **理论配套**:最短路径/最大流的数学原理可配合《运筹学》教材网络优化章节;算法复杂度讨论见《算法导论》图算法部分
- **姊妹单元**:《遗传算法自实现》单元里有 TSP 的启发式解法——networkx 没有内置 TSP 求解,但 `nx.approximation.traveling_salesman_problem` 可做近似

## 🧠 小结

1. 建图先分有向/无向:信息能沿边反向流动 → `Graph`;单向流动 → `DiGraph`
2. 带权算法必须显式确认权重键:`weight="weight"` 是默认,属性名不同就要显式传
3. 三大基础问题:`dijkstra_path`(最短)、`minimum_spanning_tree`(最省连通)、`maximum_flow`(最大流 + `minimum_cut` 定位瓶颈)
4. 网络分析三板斧:连通分量看鲁棒性、中心性找关键节点、布局绘图讲清结构
5. networkx 的结果都能二次验证(手算小图、LP 对照),验证过的数字才敢写进论文
