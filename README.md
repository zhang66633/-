# MathModelAgent — 数学建模多智能体辅助系统

基于 FastAPI + LangGraph + Vue 3 的数学建模辅助系统。三种使用模式：

| 模式 | 入口 | 说明 |
|------|------|------|
| **自由问答** | `/chat` | 纯对话咨询，SSE 流式输出，多轮上下文，支持工具调用 |
| **教学模式** | `/teach` | 苏格拉底式引导提问，培养建模思维，不直接给答案 |
| **方案模式** | `/solution` | 多智能体流水线（分析→建模→求解→验证→写作），WebSocket 实时进度 |

### 核心能力

- **代码执行**: 沙箱内运行 Python（matplotlib/numpy/scipy/pandas/sympy/cvxpy），图表自动内联显示
- **文件上传**: CSV/Excel/TXT/PDF 上传后沙箱内直接读取
- **Web 搜索**: DuckDuckGo 免费搜索，无需 API Key
- **澄清交互**: LLM 自主判断信息不足时弹出选项卡片，用户选择后继续
- **知识库**: 方法卡片/真题论文/框架模板，多路召回 + RRF 融合 + LLM 精排
- **用户认证**: GitHub OAuth + JWT（7天过期）+ 访客模式

另有知识库管理（`/knowledge`）、API Key 管理（`/apikeys`）、设置（`/settings`）页面。

## 快速开始

### Windows 一键启动

```bat
start.bat    REM 启动后端(端口读 backend/.env) + 前端(5174)
stop.bat     REM 停止全部
```

### 手动启动

#### 1. 配置环境变量

```bash
cd backend
cp .env.example .env    # 填入 DeepSeek API Key 等
```

#### 2. 启动后端

```bash
cd backend
pip install -e .
uvicorn app.main:app --host 127.0.0.1 --port 8002
```

> Redis 非必须：无 Redis 时自动回退 fakeredis（同进程 pub/sub）。
> 向量索引：首次启动自动检测并后台重建，无需手动 reindex。

#### 3. 启动前端

```bash
cd frontend
pnpm install
pnpm dev                  # http://localhost:5174
```

前端通过 Vite 代理将 `/api` 和 `/ws` 转发到 `127.0.0.1:8002`。

### Docker Compose

```bash
docker-compose up
```

## 项目结构

```
math_agent/
├── start.bat / stop.bat       # Windows 一键启停
├── RESOURCES_AND_ROADMAP.md   # 资源库 + 开发路线图（含实现细节）
├── MEMORY_CONTEXT_GUIDE.md    # 记忆/上下文/长程任务设计参考
├── docker-compose.yml
│
├── backend/                   # FastAPI + LangGraph 后端
│   ├── app/
│   │   ├── main.py            # 入口（启动时自动检测向量索引）
│   │   ├── config.py          # 配置（各 agent 角色模型、沙箱参数）
│   │   ├── api/
│   │   │   ├── chat_routes.py # POST /api/chat — SSE 流式对话
│   │   │   ├── files.py       # 文件上传/下载 + 图片服务
│   │   │   ├── ws.py          # WebSocket 任务进度
│   │   │   └── knowledge_routes.py
│   │   ├── core/              # LangGraph 编排 + prompts
│   │   ├── knowledge/         # 混合检索（向量+BM25+RRF+LLM精排）
│   │   ├── sandbox/           # 代码沙箱（subprocess + 网络阻断）
│   │   ├── tools/             # KB/数学/交互/搜索工具
│   │   └── services/          # Redis PubSub（fakeredis 回退）
│   └── knowledge_base/        # 知识数据（YAML 真源，入库 git）
│
└── frontend/                  # Vue 3 + Vite + TailwindCSS
    └── src/
        ├── pages/             # chat / teach / solution / knowledge / apikeys
        ├── components/        # ChatArea / Bubble / ClarifyCard / ProgressTimeline
        ├── composables/       # useStreamChat / useTypewriter
        ├── stores/            # Pinia: chatSession / task / auth
        └── utils/             # markdown(marked+DOMPurify) / exportPaper
```

## 技术栈

- **前端**: Vue 3 + Vite 6 + TypeScript + TailwindCSS + Pinia + lucide-vue-next
- **后端**: FastAPI + LangGraph + LangChain + uvicorn
- **实时**: SSE（对话流式）+ WebSocket（任务进度，Redis PubSub / fakeredis）
- **知识库**: YAML 真源 + ChromaDB（多路召回 + RRF + LLM rerank + 时间衰减）
- **沙箱**: subprocess + socket 阻断 + rlimit（Unix）+ matplotlib Agg 自动保存
- **LLM**: DeepSeek（默认）/ 任意 OpenAI 兼容接口，按 agent 角色配置模型
- **安全**: DOMPurify（XSS）+ 路径校验 + JWT 7天过期 + 环境清洗

## 备注

- `backend/data/`（apikeys/sessions/chroma_db/uploads）含本地运行时数据，已被 `.gitignore` 排除。
- `backend/knowledge_base/` 的 YAML 源文件在 git 中，clone 后启动即自动建索引。
- 默认分支为 `main`。
