# MathModelAgent — 数学建模多智能体学习与辅助平台

基于 FastAPI + LangGraph + Vue 3 的数学建模全流程平台，覆盖「学→练→问→做」完整闭环。7 位智能体各司其职，服务于建模手、编程手、论文手三人团队。

---

## 🧑‍🤝‍🧑 智能体团队

每个智能体都有名字、emoji 和教学风格，学生始终知道「哪位老师在教我」：

| | 智能体 | 职责 | 教学风格 |
|---|--------|------|----------|
| 🧭 | **导航员** | 诊断水平 · 规划路径 · 调度智能体 | "别急，先看看你在哪、要去哪" |
| 🔍 | **分析师** | 问题拆解 · 题意分析 · 假设提炼 | "把大问题拆成小问题" |
| 🧩 | **建模师** | 模型原理 · 方法选择 · 公式推导 | "数学就是把世界装进方程里" |
| 💻 | **求解器** | 代码实现 · 算法调试 · 数据处理 | "公式漂亮没用，跑得通才算" |
| 🔬 | **检验员** | 模型验证 · 灵敏度分析 · 找漏洞 | "好模型经得起拷问" |
| ✍️ | **编辑** | 论文写作 · 图表制作 · 排版润色 | "你的模型很厉害，但得让人看得懂" |
| 📊 | **管家** | 进度追踪 · 遗忘提醒 · 成就记录 | "你的每一点进步，我帮你记" |

智能体不是冷冰冰的工具——选中文档文字可以随手「问AI」，智能体立刻解释；听不懂时它会推荐 B 站视频、GitHub 仓库、教材章节。

---

## 🗺️ 两种工作场景

### 论文工作台 — 实战解题

| 模式 | 入口 | 说明 |
|------|------|------|
| 💬 自由问答 | `/chat` | SSE 流式对话，多轮上下文，工具调用 |
| 🎓 教学模式 | `/teach` | 苏格拉底式引导提问，培养建模思维，不直接给答案 |
| 📋 方案模式 | `/solution` | 多智能体流水线（分析→建模→求解→验证→写作），WebSocket 实时进度 |

另有知识库管理（`/knowledge`）、API Key 管理（`/apikeys`）、设置（`/settings`）。

### 学习中心 — 从入门到竞赛

面向**建模手 · 编程手 · 论文手**三人团队的个性化学习系统：

| 入口 | 路由 | 说明 |
|------|------|------|
| 🎯 学习工位 | `/learn` | 知识图谱技能树导航 + 智能体对话式讲解 + 55+ 真实学习单元 |
| 🎯 学习单元 | `/learn/:unitId` | 三栏布局：目录+笔记 | Markdown 文档（选中文字→笔记/问AI） | AI 助手聊天 |
| ✏️ 训练场 | `/practice` | 智能体出题+批改+反馈，错题回顾 |
| 💬 答疑室 | `/qa` | 自由 @智能体提问，联网推荐 B站/GitHub/教材 |
| 📈 成长档案 | `/progress` | 掌握度雷达图、学习统计、艾宾浩斯复习提醒 |

#### 学习机制

| 机制 | 说明 |
|------|------|
| 🕸️ 知识图谱技能树 | 知识点非线性关联，前置依赖 + 横向拓展，从 47 张方法卡片中提取 |
| 🧠 贝叶斯知识追踪 (BKT) | 四参数模型，P(掌握|证据) 动态更新，知道你到底会没会 |
| 📉 艾宾浩斯遗忘曲线 | 根据上次学习时间衰减掌握度，自动提醒复习最佳时机 |
| 🎚️ 动态难度调整 (DDA) | 根据掌握度自动匹配 next 难度，不浪费你的时间 |

#### 学习内容

55+ 真实 Markdown 学习单元，覆盖 7 大方法类别：

| 类别 | 单元数 | 示例 |
|------|--------|------|
| 优化 | 12 | 线性规划、整数规划、非线性规划、多目标优化 |
| 预测 | 6 | 时间序列、回归分析、灰色预测、神经网络 |
| 评价 | 7 | 层次分析法、模糊综合评价、TOPSIS、熵权法 |
| 统计 | 4 | 假设检验、方差分析、相关分析、主成分分析 |
| 图论 | 3 | 最短路径、网络流、最小生成树 |
| 微分方程 | 2 | 常微分方程、偏微分方程建模 |
| 综合 | 4+11+13 | 建模流程、编程实践、论文写作 |

每个单元包含 Markdown 文档（公式、代码示例、应用场景）+ 智能体互动讲解。

---

## ⚙️ 核心能力

- **代码执行**: 沙箱内运行 Python（matplotlib/numpy/scipy/pandas/sympy/cvxpy），图表自动内联显示
- **竞赛数据文件**: 真题附件（xlsx/csv）自动提取表结构+复制到本地，沙箱内 `pd.read_parquet()` 秒级加载
- **预计算加速**: 87.8万行销售数据 → 品类/单品/周内效应预聚合 parquet，加载时间从 42s 降到 0.03s
- **文件上传**: CSV/Excel/TXT/PDF 上传后沙箱内直接读取
- **Web 搜索**: DuckDuckGo 免费搜索，智能体可推荐 B站视频/GitHub仓库/教材资源
- **澄清交互**: LLM 自主判断信息不足时弹出选项卡片，用户选择后继续
- **知识库**: 方法卡片/真题论文/框架模板/竞赛真题/学习素材，多路召回 + RRF 融合 + MMR 重排 + LLM 精排
- **工具结果截断**: 借鉴 cc-haha `maxResultSizeChars`，超长结果写磁盘防撑爆上下文
- **工具基类工厂**: 借鉴 cc-haha `buildTool` 模式，统一安全默认值 + 并发安全标记
- **用户认证**: GitHub OAuth + JWT（7天过期）+ 访客模式

---

## 🚀 快速开始(三步装好)

### 环境要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| Python | ≥ 3.11 | 后端 |
| Node.js | ≥ 18 | 前端构建(CI 用 Node 22) |
| pnpm | ≥ 10 | 前端包管理器(`npm i -g pnpm` 或 `corepack enable`) |
| Docker | 可选 | 仅代码沙箱硬隔离需要;不装则自动回退本地 subprocess |

### 1. 克隆

```bash
git clone https://github.com/zhang66633/NB_project.git
cd NB_project
```

### 2. 一键安装(自动建虚拟环境、装依赖、生成 .env)

```bat
install.bat            REM Windows
```

```bash
bash install.sh        # Linux / macOS(可选参数 --docker 构建沙箱镜像)
```

### 3. 启动

```bat
start.bat              REM Windows 一键启动前后端
```

```bash
python start.py        # Linux / macOS
```

打开 **http://localhost:5174** → 首页「API Key」输入框粘贴你的 DeepSeek/OpenAI 兼容 Key 即可开始使用(Key 只保存在本机 `backend/data`,不上传)。

### 手动启动(可选)

```bash
cd backend
cp .env.example .env    # 填 OPENAI_API_KEY 等(不填也能启动,Key 也可在网页里配置)
python -m venv .venv && .venv/bin/pip install -e .
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8002

cd ../frontend
pnpm install
pnpm dev                # http://localhost:5174(代理 /api → 127.0.0.1:8002)
```

### Docker Compose(可选)

```bash
docker-compose up
```

### 常见问题

- **没配 API Key 能用吗**: 能打开和学习,但 AI 对话/方案生成会提示先配置 Key(网页首页粘贴即可)。
- **不登录能用吗**: 能 — 访客模式全功能可用,对话与任务都持久化在本机;GitHub 登录仅限项目贡献者(多端同步用)。
- **数据存哪 / 会丢吗**: 对话、任务、学习记录、Key 全部落盘在 `backend/data/`(SQLite/JSON);聊天另存浏览器 localStorage 并自动同步到后端 SQLite,清缓存/换浏览器也不丢。
- **沙箱**: 默认本地 subprocess(网络阻断);装好 Docker 后可用 `install --docker` 构建硬隔离沙箱镜像。
- **PDF OCR 功能**需要系统安装 poppler 与 tesseract(可选)。

---

## 📁 项目结构

```
NB_project/
├── install.bat / install.sh     # 一键安装(venv+依赖+.env)
├── start.bat / stop.bat / start.py  # 一键启停
├── ARCHITECTURE.md              # 技术架构文档
├── LEARNING_PLAN.md             # 学习系统设计文档
├── docker-compose.yml
│
├── backend/                     # FastAPI + LangGraph 后端
│   ├── app/
│   │   ├── main.py              # 入口（启动时自动检测向量索引）
│   │   ├── config.py            # 配置（各 agent 角色模型、沙箱参数）
│   │   ├── api/
│   │   │   ├── chat_routes.py   # POST /api/chat — SSE 流式对话
│   │   │   ├── tasks.py         # 任务编排（附件提取、后台流水线）
│   │   │   ├── files.py         # 文件上传/下载 + 图片服务
│   │   │   ├── ws.py            # WebSocket 任务进度
│   │   │   ├── knowledge_routes.py     # 知识库 CRUD
│   │   │   ├── learning_routes.py      # 学习路径 + 单元详情 + 完成标记
│   │   │   ├── profile_routes.py       # 用户画像 + 诊断 + 进度
│   │   │   ├── session_routes.py       # 会话管理
│   │   │   └── export_routes.py        # 论文导出
│   │   ├── core/                # LangGraph 编排 + prompts
│   │   │   ├── nodes.py         # 8 节点（分类/检索/规划/分析/建模/求解/验证/写作）
│   │   │   ├── state.py         # AgentState（含 data_files 数据文件字段）
│   │   │   ├── workflow.py      # LangGraph StateGraph 拓扑
│   │   │   └── prompts/         # 各 Agent 系统提示词 + agent_personas（7 智能体 persona）
│   │   ├── knowledge/           # 混合检索（向量+BM25+RRF+MMR+LLM精排+时间衰减）
│   │   ├── sandbox/             # 代码沙箱（subprocess + 网络阻断 + 数据文件自动挂载）
│   │   ├── tools/               # KB/数学/交互/搜索工具 + base.py（build_tool 工厂）
│   │   ├── learning/            # 学习系统
│   │   │   ├── schemas.py       # 数据模型（学习路径/单元/技能掌握度/练习记录）
│   │   │   ├── path_generator.py     # 55+ 真实学习单元内容 + 路径生成
│   │   │   ├── knowledge_graph.py    # 知识图谱（技能节点+依赖边）
│   │   │   └── mastery_tracker.py    # 贝叶斯掌握度追踪 + 艾宾浩斯遗忘曲线
│   │   └── services/            # Redis PubSub（fakeredis 回退）+ 工作记忆 + 情景记忆
│   ├── knowledge_base/          # 知识数据（YAML 真源，入库 git）
│   │   ├── methods/             # 方法卡片（47张）
│   │   ├── papers/              # 优秀论文拆解
│   │   ├── problems/            # 竞赛真题（含 data_files 附件信息）
│   │   └── templates/           # 解题框架模板
│   ├── data/                    # 运行时数据（gitignore）
│   │   ├── problems/            # 竞赛真题附件数据文件
│   │   ├── chroma_db/           # ChromaDB 向量索引
│   │   └── uploads/             # 用户上传文件
│   └── scripts/                 # 工具脚本
│       ├── run_c_problem_test.py     # 2023C 端到端测试
│       ├── precompute_2023C.py       # 预计算聚合数据
│       ├── import_problems.py        # 导入竞赛真题（含附件提取+复制）
│       └── paper_quality_check.py    # 论文质检（12项评分）
│
└── frontend/                    # Vue 3 + Vite + TailwindCSS
    └── src/
        ├── pages/               # chat / teach / solution / knowledge / apikeys /
        │   │                    # learn/[unitId] / practice / qa / progress / login / settings
        ├── components/          # ChatArea / Bubble / ClarifyCard / ProgressTimeline /
        │   │                    # AppSidebar / LearningDoc / NotePanel / SkillGraph / OnboardingWizard
        ├── composables/         # useStreamChat / useTypewriter
        ├── stores/              # Pinia: chatSession / task / auth / learning / onboarding
        ├── apis/                # API 层: learningApi / chatApi / ...
        ├── config/              # navItems（论文工作台 + 学习中心分组导航）
        └── utils/               # markdown(marked+DOMPurify) / exportPaper
```

---

## 🛠️ 技术栈

- **前端**: Vue 3 + Vite 6 + TypeScript + TailwindCSS + Pinia + lucide-vue-next + @tanstack/vue-virtual
- **后端**: FastAPI + LangGraph + LangChain + uvicorn
- **实时**: SSE（对话流式）+ WebSocket（任务进度，Redis PubSub / fakeredis）
- **知识库**: YAML 真源 + ChromaDB（向量+BM25 多路召回 + RRF + MMR + LLM rerank + 时间衰减）
- **学习系统**: 知识图谱技能树 + 贝叶斯知识追踪 (BKT) + 艾宾浩斯遗忘曲线 + 动态难度调整 (DDA)
- **数据文件**: xlsx/csv → parquet 预计算 + 列名标准化，沙箱秒级加载
- **沙箱**: Docker 容器默认硬隔离（`--network=none` + 内存/进程/能力限制）；无 Docker 时自动回退 subprocess 并告警（仅限可信输入）
- **LLM**: DeepSeek（默认）/ 任意 OpenAI 兼容接口，按 agent 角色配置模型，写作节点 384K max_tokens
- **安全**: DOMPurify（XSS）+ 路径校验 + JWT 7天过期 + 环境清洗
- **借鉴模式**: cc-haha 的 buildTool 工厂 / maxResultSizeChars 截断 / History Snip 上下文压缩

---

## 📝 备注

- `backend/data/`（apikeys/sessions/chroma_db/uploads）含本地运行时数据，已被 `.gitignore` 排除。
- `backend/knowledge_base/` 的 YAML 源文件在 git 中，clone 后启动即自动建索引。
- 默认分支为 `main`。
- 学习系统详细设计见 [LEARNING_PLAN.md](./LEARNING_PLAN.md)；历史架构讨论见 [ARCHITECTURE.md](./ARCHITECTURE.md)（早期方案已归档，开发以 [PLAN.md](./PLAN.md) 与 [RULES.md](./RULES.md) 为准）。
