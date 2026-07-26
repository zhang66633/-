"""自由问答（纯对话）SSE 流式接口。

不走 LangGraph 建模流水线，但支持 LLM 自主调用工具（KB 检索 / 数学计算 / 交互）：
  - LLM 决定何时调用哪个工具
  - 后端执行工具后将结果回灌 LLM
  - 全过程流式事件给前端（text delta / tool call / tool result / clarify）

SSE 事件协议：
  data: {"delta": "..."}\n\n                 文本增量
  data: {"tool_call": {"name":"...","args":{...}}}\n\n    工具调用开始
  data: {"tool_result": {"name":"...","preview":"..."}}\n\n 工具执行完成（含结果摘要）
  data: {"clarify": {"questions":[...]}}\n\n   LLM 需要用户澄清（前端渲染选项卡片）
  data: {"code_exec": {"status":"running"}}\n\n 代码开始执行
  data: {"code_exec": {"status":"done","stdout":"...","images":[...]}}\n\n 代码执行完成
  data: [DONE]\n\n                            全部结束
  data: {"error": "..."}\n\n                 错误
"""

import asyncio
import json
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from .schemas.request import ChatRequest
from ..core.llm.factory import LLMFactory
from ..core.prompts._shared import MARKDOWN_RULES, TEACH_SHARED_RULES
from ..tools.kb_tools import create_kb_tools
from ..tools.math_tools import create_math_tools
from ..tools.interaction_tools import create_interaction_tools
from ..tools.web_search_tools import create_web_search_tools
from ..auth import GitHubUser, get_current_user

logger = logging.getLogger(__name__)

chat_router = APIRouter()

# 滑动窗口：保留最近 N 条消息（不含 system），防止多轮后 token 膨胀。
MAX_HISTORY_MESSAGES = 20
# 单次对话最多工具调用轮数，防止无限循环
MAX_TOOL_ITERATIONS = 3

# ── Retriever 缓存（避免每请求重建 BM25 索引）──────────────────────
_cached_retriever = None

def _get_retriever():
    """懒加载 + 缓存 HybridRetriever 实例（BM25 索引只建一次）。"""
    global _cached_retriever
    if _cached_retriever is None:
        from ..knowledge.retriever import HybridRetriever
        from ..config import get_settings
        settings = get_settings()
        _cached_retriever = HybridRetriever(
            kb_root=settings.kb_root,
            persist_dir=settings.chroma_dir,
        )
    return _cached_retriever

CHAT_SYSTEM_PROMPT = f"""# 数学建模助手

你是一位专业、友善的数学建模助手，擅长解答数学建模、算法、优化、统计、
数据分析、竞赛备赛等相关问题，也能进行一般性的技术问答与咨询。

## 回答风格
- 直接、清晰、有条理，先给结论再给解释
- 对概念性问题给出准确定义与直觉解释
- 对方法类问题给出适用场景、步骤与优缺点
- 涉及代码时给出简洁可运行的示例

## 工具使用规则
- 当用户问到具体方法（如线性规划、PSO、SVM）或真实案例时，**优先调用工具**：
  - `search_method_cards`：查找方法的原理、公式、适用场景
  - `search_similar_papers`：查找竞赛真题与优秀论文示例
  - `get_analysis_template`：查找评价/解题框架模板
- 不要凭空编造方法或论文，工具没有再据实回答"暂无相关资料"
- 工具返回内容应**总结归纳**后给出，不要整段搬运
- `ask_user`：当用户请求模糊（如只说"帮我建模"但没说问题类型/数据/目标）时调用，
  提出 1-3 个关键问题各附 2-4 个选项。**问题已明确时不要调用**
- `run_code`：需要数值验证、画函数图、跑仿真或复杂计算时调用，
  代码须完整可运行，用 print() 输出关键结果
- `web_search`：需要最新信息、竞赛真题、优秀论文、算法应用案例时调用，
  搜索后**总结归纳**给出，注明来源链接

{MARKDOWN_RULES}"""

TEACH_SYSTEM_PROMPT = f"""# 数学建模引导式导师

你是一位耐心、善于启发的数学建模导师。你的目标不是直接给出答案，
而是通过苏格拉底式提问，引导学生自己一步步建立建模思维。

{TEACH_SHARED_RULES}

## 引导路径（按学生进度灵活调整）
1. 理解题意：核心目标是什么？是优化/预测/评价/统计？
2. 决策变量：哪些量是可以由我们决定的？
3. 约束条件：现实中受到哪些限制？
4. 目标函数：如何用数学表达式描述目标？
5. 模型与方法：哪类模型适合？为什么？

## 工具使用规则
- 你**也可以**调用工具查找参考资料，但**不应把工具结果直接给到学生**
- 用工具查询后，把**关键信息转成引导性问题**问学生
- 鼓励学生自己查阅、自己思考，工具只用来确认你的引导方向是否正确
- 可用工具: KB 检索（search_method_cards / search_similar_papers / get_analysis_template）
  与数学计算（sympy_compute / solve_optimization）—— 数学工具仅在需要确认某公式/数值时调用
- `ask_user`：学生描述模糊、无法判断引导方向时调用，提出 1-2 个关键问题让学生选择
- `run_code`：需要数值验证或画图辅助讲解时调用，执行后引导学生理解输出结果
- `web_search`：需要查找最新案例、论文或教程辅助引导时调用，把关键信息转成引导性问题

{MARKDOWN_RULES}"""


def _system_prompt(mode: str) -> str:
    return TEACH_SYSTEM_PROMPT if mode == "teach" else CHAT_SYSTEM_PROMPT


def _to_lc_messages(req: ChatRequest) -> list:
    """把请求中的消息历史转成 LangChain 消息，并做滑动窗口截断。"""
    history = req.messages[-MAX_HISTORY_MESSAGES:]
    msgs = [SystemMessage(content=_system_prompt(req.mode))]

    # 如果本轮有附件，注入文件上下文供 LLM 参考
    if req.files:
        file_lines = []
        for f in req.files:
            file_lines.append(f"- {f.filename} (file_id: {f.file_id})")
        file_ctx = (
            "## 用户上传的附件\n"
            "以下文件已上传，可在 run_code 中通过 file_ids 参数引用：\n"
            + "\n".join(file_lines)
            + "\n调用 run_code 时把对应 file_id 传入 file_ids 即可在代码中直接用文件名读取。"
        )
        msgs.append(SystemMessage(content=file_ctx))

    for m in history:
        if m.role == "user":
            msgs.append(HumanMessage(content=m.content))
        elif m.role == "assistant":
            msgs.append(AIMessage(content=m.content))
        elif m.role == "system":
            msgs.append(SystemMessage(content=m.content))
    return msgs


def _result_preview(content: str, max_chars: int = 200) -> str:
    """给前端预览用的摘要（避免推送几 KB 的结果）。"""
    if not content:
        return ""
    if len(content) <= max_chars:
        return content
    return content[:max_chars] + f"…(+{len(content) - max_chars} 字符)"


def _sse(d: dict) -> str:
    return f"data: {json.dumps(d, ensure_ascii=False)}\n\n"

async def _stream_solution(req: ChatRequest, api_key_config: dict | None = None):
    """方案模式 — 走全流程 LangGraph 管道，SSE 推送进度 + 最终输出。"""
    user_msgs = [m.content for m in req.messages if m.role == "user"]
    problem = user_msgs[-1] if user_msgs else ""
    if not problem:
        yield _sse({"error": "请输入问题描述"})
        yield "data: [DONE]\n\n"
        return

    import uuid
    task_id = str(uuid.uuid4())[:8]

    from ..core.state import create_initial_state
    from ..core.workflow import get_orchestrator

    state = create_initial_state(
        problem_raw=problem, mode="execute", session_id=task_id
    )
    if api_key_config:
        state["api_key_config"] = api_key_config

    orchestrator = get_orchestrator()

    yield _sse({"event": "node_start", "node": "pipeline", "data": {"task_id": task_id}})

    try:
        result = await asyncio.to_thread(orchestrator.invoke, state, {"recursion_limit": 50})
    except Exception as e:
        yield _sse({"error": f"编排器运行失败: {str(e)}"})
        yield "data: [DONE]\n\n"
        return

    final = result.get("final_response", "") or result.get("writing_output", "") or "（未生成内容，请重试）"
    writing = result.get("writing_output", "")
    model_output = result.get("model_output", "")

    # 拆分各部分供前端展示
    yield _sse({
        "event": "pipeline_done",
        "task_id": task_id,
        "has_paper": bool(writing),
        "summary": f"分析: {len(result.get('analysis_output',''))}字 / 建模: {len(model_output)}字 / 求解: {len(result.get('solving_output',''))}字 / 论文: {len(writing)}字",
    })

    # Stream final output as delta chunks
    chunk_size = 150
    for i in range(0, len(final), chunk_size):
        yield _sse({"delta": final[i:i + chunk_size]})
        await asyncio.sleep(0.03)

    yield _sse({"done": True, "task_id": task_id, "mode": "solution"})
    yield "data: [DONE]\n\n"


async def _event_stream(req: ChatRequest, api_key_config: dict | None = None):
    """SSE 生成器：流式输出 LLM 增量，并在 LLM 调用工具时通知前端。"""
    # ── solution 模式走 LangGraph 管道 ──
    if req.mode == "solution":
        async for frame in _stream_solution(req, api_key_config):
            yield frame
        return

    try:
        llm = LLMFactory.create("chat", api_key_config=api_key_config)
        # 合并所有工具: KB 检索 + 数学计算 + 交互（ask_user / run_code）+ Web 搜索
        tools = create_kb_tools() + create_math_tools() + create_interaction_tools() + create_web_search_tools()
        tool_map = {t.name: t for t in tools}
        llm_with_tools = llm.bind_tools(tools)

        messages = _to_lc_messages(req)

        # ── RAG 预检索：如果用户开启了 use_rag，先查知识库并注入上下文 ──
        if req.use_rag:
            try:
                from ..knowledge.chain import format_docs

                retriever = _get_retriever()
                last_user = next(
                    (m for m in reversed(messages) if isinstance(m, HumanMessage)),
                    None,
                )
                if last_user:
                    query = str(last_user.content)
                    docs = await asyncio.to_thread(retriever.invoke, query, k=5)
                    if docs:
                        ctx = format_docs(docs)
                        messages.insert(
                            1,  # After system prompt, before history
                            SystemMessage(
                                content=f"## 知识库参考资料（预检索）\n以下是从知识库中检索到的相关数学建模方法、论文和竞赛真题。请优先参考这些内容回答问题，必要时再调用搜索工具进行补充查询。\n\n{ctx}"
                            ),
                        )
            except Exception:
                pass  # RAG 预检索失败不阻塞对话

        # 循环：每轮 LLM 输出可能含文本 + tool_calls；若有 tool_calls 则执行后回灌
        for _ in range(MAX_TOOL_ITERATIONS):
            text_buf: list[str] = []
            full_message = None  # 累加所有 chunk 得到完整 AIMessage

            async for chunk in llm_with_tools.astream(messages):
                # 累加 chunk 以获取完整的 tool_calls
                full_message = chunk if full_message is None else full_message + chunk

                # 文本增量
                delta = getattr(chunk, "content", None)
                if delta:
                    if isinstance(delta, list):
                        delta = "".join(
                            part.get("text", "") if isinstance(part, dict) else str(part)
                            for part in delta
                        )
                    if delta:
                        text_buf.append(delta)
                        yield f"data: {json.dumps({'delta': delta}, ensure_ascii=False)}\n\n"

            # 从累加后的完整消息中提取 tool_calls（args 已完整解析）
            tool_calls_final = getattr(full_message, "tool_calls", None) or []

            # 没有工具调用 → 这一轮是纯文本回答，跳出循环
            if not tool_calls_final:
                break

            # ── 特殊处理: ask_user → 发 clarify 帧，结束本轮 ──
            ask_calls = [tc for tc in tool_calls_final if tc.get("name") == "ask_user"]
            if ask_calls:
                questions = (ask_calls[0].get("args") or {}).get("questions", [])
                yield f"data: {json.dumps({'clarify': {'questions': questions}}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
                return

            # 通知前端：开始调用工具
            for tc in tool_calls_final:
                yield f"data: {json.dumps({'tool_call': {'name': tc.get('name'), 'args': tc.get('args') or {}}}, ensure_ascii=False)}\n\n"

            # 把 LLM 的 tool_calls 写回消息历史（AIMessage with tool_calls）
            messages.append(
                AIMessage(
                    content="".join(text_buf),
                    tool_calls=[
                        {
                            "id": tc.get("id") or tc.get("tool_call_id"),
                            "name": tc.get("name"),
                            "args": tc.get("args") or {},
                        }
                        for tc in tool_calls_final
                    ],
                )
            )

            # 执行每个工具
            for tc in tool_calls_final:
                tool_name = tc.get("name")
                tool_args = tc.get("args") or {}
                tool = tool_map.get(tool_name)
                if tool is None:
                    result_text = f"未知工具: {tool_name}"
                else:
                    # run_code 额外推送执行状态事件
                    if tool_name == "run_code":
                        yield f"data: {json.dumps({'code_exec': {'status': 'running'}}, ensure_ascii=False)}\n\n"

                    try:
                        result_text = await asyncio.to_thread(tool.invoke, tool_args)
                    except Exception as e:  # noqa: BLE001
                        logger.exception("tool %s failed", tool_name)
                        result_text = f"工具执行失败: {e}"

                    # run_code: 解析结果，推送 stdout + images
                    if tool_name == "run_code":
                        code_data = _parse_code_result(result_text)
                        yield f"data: {json.dumps({'code_exec': {'status': 'done', **code_data}}, ensure_ascii=False)}\n\n"

                # 通知前端：工具结果摘要
                yield f"data: {json.dumps({'tool_result': {'name': tool_name, 'preview': _result_preview(result_text)}}, ensure_ascii=False)}\n\n"

                # 把结果写回历史，供下一轮 LLM 使用
                messages.append(
                    ToolMessage(
                        content=result_text,
                        tool_call_id=tc.get("id") or tc.get("tool_call_id") or tool_name,
                    )
                )

        yield "data: [DONE]\n\n"

    except Exception as e:  # noqa: BLE001
        logger.exception("chat stream failed")
        err = str(e)
        if "incorrect api key" in err.lower() or "invalid api key" in err.lower():
            err = "API Key 无效，请在首页重新配置你的 Key"
        elif "401" in err or "403" in err:
            err = f"API Key 验证失败 (401)，请检查 Key 是否正确。原始错误: {err[:200]}"
        elif "api_key" in err.lower() or "api key" in err.lower():
            err = f"API Key 错误: {err[:300]}"
        yield f"data: {json.dumps({'error': err}, ensure_ascii=False)}\n\n"


def _parse_code_result(result_text: str) -> dict:
    """从 RunCodeTool 的输出文本中提取 stdout 和 images。"""
    stdout_parts = []
    images: list[str] = []
    for line in result_text.split("\n"):
        if line.startswith("输出:"):
            continue
        if line.startswith("生成图表:"):
            paths = line.replace("生成图表:", "").strip()
            images = [p.strip() for p in paths.split(",") if p.strip()]
        elif line.startswith("错误:"):
            continue
        else:
            stdout_parts.append(line)
    return {"stdout": "\n".join(stdout_parts).strip(), "images": images}


@chat_router.post("/chat")
async def chat(req: ChatRequest, user: GitHubUser | None = Depends(get_current_user)):
    """自由问答 SSE 流式接口（支持 LLM 工具调用）。"""
    from .apikeys import get_active_api_key, _resolve_user_id
    uid = _resolve_user_id(user=user)
    active_key = get_active_api_key(uid)
    if not active_key:
        async def no_key():
            yield f"data: {json.dumps({'error': '请先在首页配置你的 API Key 后再发送消息。'}, ensure_ascii=False)}\n\n"
        return StreamingResponse(no_key(), media_type="text/event-stream")

    if not req.messages:
        async def empty():
            yield f"data: {json.dumps({'error': '消息不能为空'}, ensure_ascii=False)}\n\n"
        return StreamingResponse(empty(), media_type="text/event-stream")

    return StreamingResponse(
        _event_stream(req, api_key_config=active_key),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )