# LaTeX数学建模模板

> **难度**:进阶 · **预计学习时长**:50 分钟 · **主讲智能体**:✏️ 编辑 · **类别**:论文写作

## 🎯 学习目标

学完本单元,你应该能够:

- 说出 LaTeX 相对 Word 的四个优势,并完成本地环境(TeX Live + VS Code)或 Overleaf 的搭建
- 熟练使用 equation/align/cases 等公式环境、booktabs 三线表与 graphicx 插图
- 读懂并修复 5 类高频编译错误
- 基于本单元给出的完整模板,独立排出一篇结构齐全的国赛风格论文

## 📖 核心概念

### 1. 为什么用 LaTeX

- **公式质量**:数学公式的排版质量是 Word 公式编辑器难以企及的,国赛 A 题的推导密度下差距尤其明显
- **交叉引用自动化**:图、表、公式、文献的编号与引用自动维护——赛程最后一天疯狂改图改公式时,Word 的手工编号必错,LaTeX 不会
- **格式一致性**:标题、字体、页边距一次定义全局生效,官方模板(cumcmthesis)直接保证格式合规
- **协作与版本管理**:纯文本格式可以用 Git 管理,三个队友同时改不同章节再合并,冲突远少于 Word

### 2. 环境搭建

- **本地**:安装 TeX Live(Windows/macOS/Linux 全平台),编辑器用 VS Code + LaTeX Workshop 插件;编译用 XeLaTeX(必须——中文支持)
- **在线**:Overleaf 免安装,自带实时预览与协作功能,国赛/美赛期间服务器负载高,建议本地留备份
- **文档类**:国赛官方模板使用 `cumcmthesis` 文档类(竞赛官网或 LaTeXStudio 提供);美赛使用 `mcmthesis`;平时练习可用 `ctexart`(中文文章类)

### 3. 核心环境速查

| 需求 | 环境/命令 | 说明 |
|------|----------|------|
| 行内公式 | `$...$` | 如 $x_i \geq 0$ |
| 单行独立公式 | `equation` | 自动编号 (1)(2)… |
| 多行对齐 | `align` | `&` 对齐,`\\` 换行 |
| 分段函数 | `cases` | 大括号分段定义 |
| 矩阵 | `matrix`/`pmatrix` | 圆括号矩阵最常用 |
| 三线表 | `booktabs` 宏包 | `\toprule \midrule \bottomrule` |
| 插图 | `graphicx` | `\includegraphics` |
| 引用 | `\label{...}` + `\ref{...}` | 图/表/公式/节通用 |

### 4. 编译流水线与五类高频错误

正确流程:**XeLaTeX → BibTeX → XeLaTeX → XeLaTeX**(第二次编译生成引用编号,第三次让引用稳定;用 biblatex 时把 BibTeX 换成 Biber)。五类高频错误:

1. `Undefined control sequence` —— 拼错了命令名或没加载宏包(用了 `\bm` 但没 `\usepackage{bm}`)
2. `Missing $ inserted` —— 数学符号(下划线、希腊字母、^)出现在文本模式,漏了 `$...$`
3. `Undefined references` —— 忘了编译两次,或 `\label` 与 `\ref` 名字不一致
4. 中文乱码/报错 —— 用了 pdfLaTeX 编译中文(必须 XeLaTeX + `ctex` 文档类),或文件编码不是 UTF-8
5. 图片找不到 —— `\includegraphics` 的路径错误,或文件名含中文/空格

### 5. 参考文献:thebibliography 与 BibTeX

- **简单场景**(文献 10 条以内):用 `thebibliography` 环境手工排版,格式按 GB/T 7714
- **规范场景**:用 BibTeX + 参考文献库 `refs.bib`,配合 `gbt7714` 样式宏包,自动按国标排版;编译时多跑一步 BibTeX

## 🧮 写作要点清单

| 检查项 | 自检问题 |
|--------|---------|
| 编译引擎 | 全程 XeLaTeX?文件 UTF-8 编码? |
| 编译次数 | 引用编号稳定前编译了 2–3 次吗? |
| 公式环境 | 独立公式用 equation/align,没有用 `$$...$$`? |
| 标点 | 公式末尾按中文习惯加标点了吗? |
| 表格 | 三线表用 booktabs,无竖线? |
| 交叉引用 | 所有图、表、公式、节都是 `\ref` 引用,无手写编号? |
| 参考文献 | 文内引用与文献表一一对应? |

## 💡 经典例题

### 例题 1:公式排版——Word 迁移 vs LaTeX 原生(对照)

**差(Word 迁移习惯)**:

```latex
$$x_{ij} = \frac{1}{2}(\frac{a}{b} + \frac{c}{d})$$   % 用 $$...$$,分数套分数
```

**问题**:①`$$...$$` 是 TeX 原始语法,LaTeX 中应使用 `\[...\]` 或 equation 环境(编号、间距、与宏包的兼容性都会受影响);②嵌套 `\frac` 层层缩小,打印后几乎看不清;③公式没有编号,后文无法引用。

**好**:

```latex
\begin{equation}\label{eq:distance}
  d_{ij} = \frac{a}{b} + \frac{c}{d}
         = \frac{ad + cb}{bd},
\end{equation}
```

**点评**:equation 环境自动编号 (1),`\label{eq:distance}` 让后文可以 `\eqref{eq:distance}` 引用;公式末尾的逗号符合中文排版标点习惯;复杂的分数结构应主动化简为 `\frac{ad+cb}{bd}`,保证可读性。

### 例题 2:分段函数与矩阵(实战写法)

目标函数中的分段成本:

```latex
\begin{equation}\label{eq:cost}
  C(q) =
  \begin{cases}
    c_1 q, & 0 \leq q \leq q_0, \\[2pt]
    c_1 q_0 + c_2 (q - q_0), & q > q_0,
  \end{cases}
\end{equation}
```

> 要点:`cases` 环境内用 `&` 对齐公式与条件,`\\[2pt]` 加大行距避免分数线拥挤;条件部分写清取值区间,这是建模论文公式的规范细节。

协方差矩阵用 `pmatrix`:

```latex
\begin{equation}
  \Sigma = \begin{pmatrix}
    \sigma_1^2 & \rho\sigma_1\sigma_2 \\
    \rho\sigma_1\sigma_2 & \sigma_2^2
  \end{pmatrix}
\end{equation}
```

### 例题 3:编译错误诊断(三则)

| 报错信息 | 诊断 | 修复 |
|---------|------|------|
| `Undefined control sequence. \bm{\theta}` | 使用了 `\bm` 但未加载 bm 宏包 | 导言区加 `\usepackage{bm}` |
| `Missing $ inserted. ... x_i >= 0` | `>=` 与 `_` 在文本模式使用 | 改为 `$x_i \geq 0$`(注意是 `\geq` 不是 `>=`) |
| `LaTeX Warning: Reference 'tab:result' undefined` | 只编译了一次,或 label/ref 名不一致 | 再编译一次;检查 `\label{tab:result}` 与 `\ref{tab:result}` 拼写一致 |

## ⚠️ 常见易错点

1. **用 pdfLaTeX 编译中文**。直接报错或乱码——中文文档必须 XeLaTeX + ctex 文档类
2. **数学模式使用错误**。`$$...$$` 写独立公式、下划线/上标/希腊字母漏 `$` 直接写在文本里——前者用 equation/align 环境,后者补 `$...$`
3. **引用未编译两次**。正文出现 `??`——图、表、公式、文献的引用编号需要第二、三次编译才稳定
4. **表格竖线 + 全边框**。LaTeX 论文同样遵循三线表规范(booktabs),把 Word 网格表习惯带进来会破坏排版质量
5. **公式后无标点**。中文论文的独立公式末尾要按句子加逗号/句号,公式是句子的组成部分
6. **图片路径或命名问题**。文件名含中文/空格导致找不到;建议 `fig/fig3.pdf` 小写英文命名

## ✏️ 自测练习(选择题)

**第 1 题**:用 pdfLaTeX 编译中文论文出现乱码或报错,正确的做法是:

A. 把中文全部替换为英文
B. 改用 XeLaTeX 编译 + ctex 文档类,并确认文件为 UTF-8 编码
C. 升级 pdfLaTeX 到最新版本
D. 在导言区加入 \usepackage{chinese}

<details><summary>查看答案与解析</summary>
**答案:B**。中文文档必须用 XeLaTeX + ctex 文档类(ctexart/cumcmthesis),且文件编码为 UTF-8;pdfLaTeX 引擎不支持中文。A 逃避问题;C 解决不了引擎不支持中文的根本原因;D 的宏包不存在,属于编造命令。
</details>

**第 2 题**:编译报错 `Missing $ inserted`,报错定位在 `x_i 是第 i 个变量,其中 x_i >= 0`。原因与修复正确的是:

A. 变量不能带下标,应把 $x_i$ 改写为 $xi$
B. 中文与数学混排不被支持,应全部改英文
C. article 文档类不支持行内变量,应改为 report
D. 下划线 `_` 与 `>=` 在文本模式使用——应改为数学模式「$x_i$ 是第 $i$ 个变量,其中 $x_i \geq 0$」

<details><summary>查看答案与解析</summary>
**答案:D**。下划线、上标、希腊字母等数学符号出现在文本模式会触发 `Missing $ inserted`;应放进 `$...$`,且比较符号写作 `\geq` 而不是 `>=`。A 错——下标是 LaTeX 常规能力,问题在于漏了数学模式;B、C 都与病因无关。
</details>

**第 3 题**:交叉引用处出现 `??`(如「见表 ??」),最可能的原因与正确处理是:

A. 公式太长,需要拆分成多个 equation 环境
B. 图片路径错误,应检查 \includegraphics 的文件名
C. 只编译了一次——引用编号需完整编译流水线 XeLaTeX → BibTeX/Biber → XeLaTeX → XeLaTeX;若仍为 ??,检查 \label 与 \ref 名称是否一致
D. 文档类版本过低,应更换

<details><summary>查看答案与解析</summary>
**答案:C**。`\ref` 的编号信息需要第二、三次编译写入辅助文件并稳定,只编译一次必然 `??`;多次编译后仍为 `??`,则是 \label 与 \ref 拼写不一致(注意大小写)。A、D 与引用机制无关;B 是「图片找不到」的病因,不是引用未解析。
</details>

## 🏆 竞赛实战链接

- **国赛官方模板**:cumcmthesis 文档类由 LaTeXStudio 社区维护、与官方 Word 模板格式一致,是国赛 LaTeX 队伍的事实标准;使用时以当年官方《论文格式规范》为准
- **美赛模板**:mcmthesis 文档类(CTAN 与 Overleaf 均可获取)内置 Summary Sheet 环境,一键生成合规首页
- **评阅视角**:LaTeX 论文在公式、图表、编号上的规范感,直接影响「表述的清晰性」评分;同一支队伍的建模水平,LaTeX 版论文的观感通常优于 Word 版——这是排版质量带来的可信度加成
- **风险提示**:赛前一周务必全流程演练一次「模板下载→编译→插图→参考文献→生成 PDF」,把环境问题消灭在赛场之外

## 💻 代码实现

**完整可编译模板**(保存为 `main.tex`,XeLaTeX 编译两次):

```latex
% !TeX program = xelatex
\documentclass{ctexart}          % 国赛请替换为 cumcmthesis 文档类
\usepackage{amsmath, amssymb}    % 数学公式增强
\usepackage{booktabs}            % 三线表
\usepackage{graphicx}            % 插图
\usepackage{caption}             % 图表标题
\usepackage[colorlinks=true]{hyperref}  % 超链接与交叉引用

\title{基于整数规划与遗传算法的仓库供货优化模型}
\author{××大学 ×××队}            % 国赛提交时按官方模板的匿名要求处理

\begin{document}
\maketitle

\begin{abstract}
针对 10 个仓库、50 个门店的供货优化问题,本文建立以月运输总成本
最小为目标的 0-1 整数规划模型,设计遗传算法求解,并与 CPLEX 精确
解对比验证。结果表明:最优方案月成本 47.82 万元,较现行方案降低
13.5\%。灵敏度分析表明方案对需求波动稳健。
\end{abstract}
\keywords{整数规划;遗传算法;供货优化}

\section{问题分析}
本题本质是一个资源受限的组合优化问题,决策变量为供货关系矩阵,
目标为总成本最小,约束包括供需平衡与仓库容量限制。

\section{模型建立}
设 $x_{ij}=1$ 表示仓库 $i$ 向门店 $j$ 供货,目标函数为
\begin{equation}\label{eq:obj}
  \min z = \sum_{i=1}^{10} \sum_{j=1}^{50} c_{ij} x_{ij},
\end{equation}
其中 $c_{ij}$ 为仓库 $i$ 至门店 $j$ 的单位运输成本(元/箱)。

\section{模型求解}
遗传算法求解结果如表~\ref{tab:compare} 所示,收敛过程见图~\ref{fig:conv}。

\begin{table}[htbp]
  \centering
  \caption{三种算法的求解结果对比}
  \label{tab:compare}
  \begin{tabular}{lccc}
    \toprule
    算法 & 最优成本(万元) & 计算时间(s) & 与最优解差距 \\
    \midrule
    CPLEX(精确解) & 47.82 & 1260.4 & -- \\
    遗传算法       & 48.15 & 3.2    & 0.69\% \\
    模拟退火       & 48.63 & 5.8    & 1.69\% \\
    \bottomrule
  \end{tabular}
\end{table}

\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.75\textwidth]{fig/fig3_conv.pdf}
  \caption{遗传算法总成本收敛曲线}
  \label{fig:conv}
\end{figure}

\begin{thebibliography}{9}
\bibitem{jiang2003} 姜启源, 谢金星, 叶俊. 数学模型(第三版)[M]. 北京: 高等教育出版社, 2003.
\bibitem{gen1989} Goldberg D E. Genetic Algorithms in Search, Optimization and Machine Learning[M]. Boston: Addison-Wesley, 1989.
\end{thebibliography}

\end{document}
```

**要点逐条说明**:①文档类用 ctex 系列保证中文,XeLaTeX 编译;②公式、表、图全部 `\label` + `\ref` 交叉引用,编号自动维护;③表格为 booktabs 三线表,单位在表头,小数位统一;④图片为 PDF 矢量图,`0.75\textwidth` 控制宽度避免溢出;⑤参考文献为 GB/T 7714 格式示例。国赛使用时将 `\documentclass{ctexart}` 换成 `\documentclass{cumcmthesis}`,其余结构不变。

## 📚 延伸阅读

- **入门书**:lshort-zh(《一份(不太)简短的 LaTeX 2ε 介绍》,CTAN 免费获取)——中文 LaTeX 入门首选
- **进阶书**:刘海洋《LaTeX 入门》——中文排版细节讲得最透
- **在线**:Overleaf 官方教程与模板库;CTAN 的 [booktabs 文档](https://ctan.org/pkg/booktabs) 学习三线表细节
- **模板**:LaTeXStudio 的 CUMCMThesis 仓库(GitHub 搜索 CUMCMThesis);CTAN 的 mcmthesis
- **进阶关联**:三线表与图表的排版规范见《图表设计与可视化》单元;参考文献库的构建见《文献检索与引用规范》单元

## 🧠 小结

1. LaTeX 四优势:公式质量、交叉引用自动化、格式一致性、Git 协作;编译一律 XeLaTeX
2. 核心环境:equation/align/cases/pmatrix、booktabs、graphicx;公式末尾按中文习惯加标点
3. 编译流水线:XeLaTeX → BibTeX → XeLaTeX → XeLaTeX;`??` 说明编译次数不够或 label 名不一致
4. 五类高频错误:宏包未加载、漏 $、引用未解析、编译引擎错、图片路径错——本单元例题 3 逐一覆盖
5. 用本单元完整模板开始:国赛换 cumcmthesis,美赛换 mcmthesis,赛前全流程演练一次
