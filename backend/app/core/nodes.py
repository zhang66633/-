"""图节点函数 — classify / retrieve / plan / agent / format。"""

import json
import re
import time
from pathlib import Path
from typing import List

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from app.config import get_settings
from app.core.state import AgentState
from app.knowledge.loader import KnowledgeBaseLoader
from app.knowledge.retriever import HybridRetriever
from app.sandbox.executor import SandboxExecutor
from app.services.redis_pubsub import get_publisher
from app.tools.interaction_tools import RunCodeTool
from app.tools.kb_tools import create_kb_tools
from app.tools.math_tools import create_math_tools
from app.tools.web_search_tools import create_web_search_tools

from .llm.factory import get_llm
from .prompts.classifier import CLASSIFIER_SYSTEM_PROMPT, CLASSIFIER_USER_TEMPLATE
from .prompts.planner import PLANNER_SYSTEM_PROMPT, PLANNER_USER_TEMPLATE
from .prompts.analysis import (
    ANALYSIS_SYSTEM_PROMPT, ANALYSIS_USER_TEMPLATE,
    ANALYSIS_TEACH_SYSTEM_PROMPT, ANALYSIS_TEACH_USER_TEMPLATE,
)
from .prompts.modeling import (
    MODELING_SYSTEM_PROMPT, MODELING_USER_TEMPLATE,
    MODELING_TEACH_SYSTEM_PROMPT, MODELING_TEACH_USER_TEMPLATE,
)
from .prompts.solving import (
    SOLVING_SYSTEM_PROMPT, SOLVING_USER_TEMPLATE,
    SOLVING_TEACH_SYSTEM_PROMPT, SOLVING_TEACH_USER_TEMPLATE,
    SOLVING_TOOL_SYSTEM_PROMPT, SOLVING_TOOL_USER_TEMPLATE,
)
from .prompts.verification import (
    VERIFICATION_SYSTEM_PROMPT, VERIFICATION_USER_TEMPLATE,
    VERIFICATION_TEACH_SYSTEM_PROMPT, VERIFICATION_TEACH_USER_TEMPLATE,
)
from .prompts.writing import (
    WRITING_SYSTEM_PROMPT, WRITING_USER_TEMPLATE,
    WRITING_TEACH_SYSTEM_PROMPT, WRITING_TEACH_USER_TEMPLATE,
    WRITING_OUTLINE_PROMPT, WRITING_SECTION_PROMPT, WRITING_ABSTRACT_PROMPT,
    RED_TEAM_PROMPT, WRITING_REVISE_PROMPT,
)


# ── helper: publish node progress ────────────────────────────────────


def _pub_event(task_id: str, event: str, node: str, data: dict | None = None):
    """Fire-and-forget publish a progress event to Redis."""
    try:
        return get_publisher().publish(task_id, event, node, data)
    except Exception:
        pass  # best-effort; never block the workflow on publish failures


def _is_cancelled(task_id: str) -> bool:
    """Check if the task has been cancelled."""
    try:
        from app.services.session import get_session_manager
        event = get_session_manager().get_cancel_event(task_id)
        return event.is_set()
    except Exception:
        return False


# ============================================================
# 节点 1: 问题分类
# ============================================================
def classify_problem(state: AgentState) -> dict:
    """识别问题类型、复杂度、数据依赖。"""
    task_id = state["session_id"]
    _pub_event(task_id, "node_start", "classify")

    llm = get_llm("classifier", state.get("api_key_config"))
    prompt = CLASSIFIER_USER_TEMPLATE.format(problem=state["problem_raw"])

    response = llm.invoke([
        SystemMessage(content=CLASSIFIER_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ])

    # 解析 JSON 输出
    result = _extract_json(str(response.content))

    _pub_event(task_id, "node_end", "classify", {
        "problem_type": result.get("problem_type", ""),
        "problem_complexity": result.get("problem_complexity", "simple"),
        "summary": result.get("summary", ""),
    })

    return {
        "problem_type": result.get("problem_type", ""),
        "problem_complexity": result.get("problem_complexity", "simple"),
        "data_dependency": result.get("data_dependency", "theoretical"),
        "messages": [
            SystemMessage(
                content=f"分类结果: 类型={result.get('problem_type')}, "
                        f"复杂度={result.get('problem_complexity')}, "
                        f"摘要={result.get('summary', '')}"
            )
        ],
    }


# ============================================================
# 节点 2: 知识库检索
# ============================================================
def retrieve_knowledge(state: AgentState) -> dict:
    """从三层知识库检索相关内容。"""
    task_id = state["session_id"]
    _pub_event(task_id, "node_start", "retrieve_knowledge")
    settings = get_settings()

    loader = KnowledgeBaseLoader(settings.kb_root)

    methods: List[dict] = []
    papers: List[dict] = []
    templates: List[dict] = []
    problems: List[dict] = []

    problem_type = state["problem_type"]

    if problem_type:
        # 标签过滤 — 精确匹配
        for card in loader.get_methods_by_category(problem_type):
            methods.append({
                "id": card.id,
                "name": card.name,
                "principle": card.principle[:300],
                "category": card.category,
                "page_content": card.principle[:500],
            })

        for paper in loader.get_papers_by_type(problem_type):
            # Build rich page_content for downstream agents
            pc = f"{paper.title} [{paper.year} {paper.competition} {paper.problem_id}] {paper.model.approach[:200]}"
            papers.append({
                "id": paper.id,
                "title": paper.title,
                "year": paper.year,
                "competition": paper.competition,
                "problem_id": paper.problem_id,
                "approach": paper.model.approach,
                "page_content": pc[:500],
            })

        for tpl in loader.get_templates_for_type(problem_type):
            templates.append({
                "id": tpl.id,
                "name": tpl.name,
                "applicable_to": tpl.applicable_to,
                "page_content": tpl.name,
            })

        for prob in loader.get_problems_by_type(problem_type):
            pc = f"{prob.title} [{prob.year} {prob.competition} {prob.problem_id}] {prob.background[:300]}"
            problems.append({
                "id": prob.id,
                "title": prob.title,
                "year": prob.year,
                "competition": prob.competition,
                "problem_id": prob.problem_id,
                "background": prob.background[:300],
                "objectives": prob.objectives,
                "page_content": pc[:500],
            })

    # 语义搜索 — 始终执行，与 tag 结果互补
    tag_ids = {m.get("id") for m in methods} | {p.get("id") for p in papers} | {t.get("id") for t in templates} | {pr.get("id") for pr in problems}
    try:
        retriever = HybridRetriever(
            kb_root=settings.kb_root,
            persist_dir=settings.chroma_dir,
        )
        docs = retriever.invoke(state["problem_raw"], k=5)
        for doc in docs:
            meta = doc.metadata
            doc_id = meta.get("id", "")
            if doc_id in tag_ids:
                continue  # 跳过 tag 已有结果
            if meta.get("type") == "method_card":
                methods.append({
                    "id": meta.get("id"), "name": meta.get("name", ""),
                    "principle": "", "category": [],
                    "page_content": doc.page_content[:500],
                })
            elif meta.get("type") == "paper":
                papers.append({
                    "id": meta.get("id"),
                    "title": meta.get("title", ""),
                    "year": meta.get("year"),
                    "competition": meta.get("competition"),
                    "problem_id": meta.get("problem_id", ""),
                    "approach": "",
                    "page_content": doc.page_content[:500],
                })
            elif meta.get("type") == "template":
                templates.append({
                    "id": meta.get("id"), "name": meta.get("name", ""),
                    "applicable_to": [],
                    "page_content": doc.page_content[:500],
                })
            elif meta.get("type") == "problem":
                problems.append({
                    "id": meta.get("id"),
                    "title": meta.get("title", ""),
                    "year": meta.get("year"),
                    "competition": meta.get("competition"),
                    "problem_id": meta.get("problem_id", ""),
                    "background": "",
                    "objectives": [],
                    "page_content": doc.page_content[:500],
                })
    except Exception:
        pass  # 向量库未初始化时优雅降级

    _pub_event(task_id, "node_end", "retrieve_knowledge", {
        "methods_count": len(methods),
        "papers_count": len(papers),
        "templates_count": len(templates),
        "problems_count": len(problems),
    })

    return {
        "kb_methods": methods,
        "kb_papers": papers,
        "kb_templates": templates,
        "kb_problems": problems,
        "messages": [
            SystemMessage(
                content=f"知识库检索: 找到 {len(methods)} 个方法, "
                        f"{len(papers)} 篇论文, {len(templates)} 个模板, "
                        f"{len(problems)} 道竞赛真题"
            )
        ],
    }


# ============================================================
# 节点 3: 执行规划
# ============================================================
def plan_execution(state: AgentState) -> dict:
    """根据分类和知识库，动态生成子 agent 执行计划。"""
    task_id = state["session_id"]
    _pub_event(task_id, "node_start", "plan_execution")
    llm = get_llm("planner", state.get("api_key_config"))

    # 构建知识库上下文
    methods_str = "\n".join(
        f"- {m['name']}: {m.get('principle', '')[:100]}" for m in state["kb_methods"]
    ) or "（无推荐的特定方法）"

    templates_str = "\n".join(
        f"- {t['name']}" for t in state["kb_templates"]
    ) or "（无匹配模板）"

    papers_str = "\n".join(
        f"- [{p['year']}] {p['title']}" for p in state["kb_papers"]
    ) or "（无参考论文）"

    problems_str = "\n".join(
        f"- [{p.get('year', '?')} {p.get('competition', '?')} {p.get('problem_id', '?')}] "
        f"{p.get('title', '?')}"
        for p in state["kb_problems"]
    ) or "（无相关竞赛真题）"

    system_prompt = PLANNER_SYSTEM_PROMPT.format(
        methods=methods_str,
        templates=templates_str,
        papers=papers_str,
        problems=problems_str,
    )

    user_prompt = PLANNER_USER_TEMPLATE.format(
        problem=state["problem_raw"],
        problem_type=state["problem_type"],
        complexity=state["problem_complexity"],
        data_dependency=state["data_dependency"],
    )

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])

    plan = _extract_json(str(response.content))

    # 确保返回的是字符串列表
    if isinstance(plan, list) and all(isinstance(x, str) for x in plan):
        execution_plan: List[str] = plan
    else:
        # 默认计划
        execution_plan = ["analysis", "modeling", "solving", "verification", "writing"]

    return {
        "execution_plan": execution_plan,
        "current_step_index": -1,
        "messages": [
            SystemMessage(
                content=f"执行计划: {' → '.join(execution_plan)}"
            )
        ],
    }


# ============================================================
# Agent 节点 — 每个 agent 节点递增 current_step_index
# ============================================================
def _next_step(state: AgentState) -> int:
    """获取当前步骤索引并递增。"""
    return state.get("current_step_index", -1) + 1


def analysis_agent_node(state: AgentState) -> dict:
    """问题分析 Agent — 用 LLM 深度分析问题结构。"""
    idx = _next_step(state)
    task_id = state["session_id"]
    _pub_event(task_id, "node_start", "analysis_agent", {"step": idx + 1})
    llm = get_llm("analysis", state.get("api_key_config"))

    # 构建知识库上下文
    methods_str = "\n".join(
        f"- **{m['name']}**: {m.get('principle', '')[:200]}"
        for m in state["kb_methods"][:5]
    ) or "（无推荐方法）"

    templates_str = "\n".join(
        f"- {t['name']}（适用于: {', '.join(t.get('applicable_to', []))}）"
        for t in state["kb_templates"][:3]
    ) or "（无匹配模板）"

    if state["mode"] == "teach":
        system_prompt = ANALYSIS_TEACH_SYSTEM_PROMPT.format(
            methods=methods_str,
            templates=templates_str,
        )
        user_prompt = ANALYSIS_TEACH_USER_TEMPLATE.format(
            problem=state["problem_raw"],
            problem_type=state["problem_type"],
        )
    else:
        system_prompt = ANALYSIS_SYSTEM_PROMPT.format(
            methods=methods_str,
            templates=templates_str,
        )
        user_prompt = ANALYSIS_USER_TEMPLATE.format(
            problem=state["problem_raw"],
            problem_type=state["problem_type"],
        )

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])

    analysis_output = str(response.content)

    _pub_event(task_id, "node_end", "analysis_agent", {
        "step": idx + 1,
        "output_length": len(analysis_output),
    })

    return {
        "analysis_output": analysis_output,
        "current_step_index": idx,
        "messages": [
            SystemMessage(
                content=f"[分析Agent] 第{idx+1}步完成，"
                        f"输出 {len(analysis_output)} 字"
            )
        ],
    }


def modeling_agent_node(state: AgentState) -> dict:
    """模型构建 Agent — 基于分析结果建立数学模型。"""
    idx = _next_step(state)
    task_id = state["session_id"]
    _pub_event(task_id, "node_start", "modeling_agent", {"step": idx + 1})
    llm = get_llm("modeling", state.get("api_key_config"))

    # 构建知识库上下文
    methods_str = "\n".join(
        f"- **{m['name']}**: {m.get('principle', '')[:200]}"
        for m in state["kb_methods"]
    ) or "（无推荐方法）"

    templates_str = "\n".join(
        f"- {t['name']}"
        for t in state["kb_templates"]
    ) or "（无匹配模板）"

    if state["mode"] == "teach":
        system_prompt = MODELING_TEACH_SYSTEM_PROMPT.format(
            methods=methods_str,
            templates=templates_str,
        )
        user_prompt = MODELING_TEACH_USER_TEMPLATE.format(
            problem=state["problem_raw"],
            analysis=state.get("analysis_output", "无分析结果"),
            problem_type=state["problem_type"],
        )
    else:
        system_prompt = MODELING_SYSTEM_PROMPT.format(
            methods=methods_str,
            templates=templates_str,
        )
        user_prompt = MODELING_USER_TEMPLATE.format(
            problem=state["problem_raw"],
            analysis=state.get("analysis_output", "无分析结果"),
            problem_type=state["problem_type"],
        )

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])

    model_output = str(response.content)

    _pub_event(task_id, "node_end", "modeling_agent", {
        "step": idx + 1,
        "output_length": len(model_output),
    })

    return {
        "model_output": model_output,
        "current_step_index": idx,
        "messages": [
            SystemMessage(
                content=f"[建模Agent] 第{idx+1}步完成，"
                        f"输出 {len(model_output)} 字"
            )
        ],
    }


def _collect_image_urls(text: str) -> list[str]:
    """从工具输出文本中提取 /api/images/... 形式的图表 URL。"""
    return re.findall(r"/api/images/[^\s,，)）'\"]+\.png", text or "")


def solving_agent_node(state: AgentState) -> dict:
    """求解计算 Agent。

    - teach 模式：引导式教学（不执行代码）。
    - execute 模式：多轮 tool loop —— 通过 bind_tools 动态调用
      run_code / sympy / 优化 / 知识库 / 搜索，形成"求解→检验→灵敏度"闭环，
      产出证据驱动的结构化求解报告。
    """
    idx = _next_step(state)
    task_id = state["session_id"]
    _pub_event(task_id, "node_start", "solving_agent", {"step": idx + 1})
    llm = get_llm("solving", state.get("api_key_config"))

    model_text = state.get("model_output") or "无模型"

    # ── teach 模式：保持原有引导式输出 ──
    if state["mode"] == "teach":
        system_prompt = SOLVING_TEACH_SYSTEM_PROMPT.format(model_info=model_text[:3000])
        user_prompt = SOLVING_TEACH_USER_TEMPLATE.format(
            problem=state["problem_raw"],
            model=model_text[:3000],
        )
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])
        final_output = str(response.content)
        _pub_event(task_id, "node_end", "solving_agent", {
            "step": idx + 1,
            "output_length": len(final_output),
            "images_count": 0,
        })
        return {
            "solving_output": final_output,
            "current_step_index": idx,
            "messages": [SystemMessage(content=f"[求解Agent] 第{idx+1}步完成（教学模式）")],
        }

    # ── execute 模式：多轮 tool loop ──
    tools = (
        [RunCodeTool()]
        + create_math_tools()
        + create_kb_tools()
        + create_web_search_tools()
    )
    tool_map = {t.name: t for t in tools}
    llm_with_tools = llm.bind_tools(tools)

    system_prompt = SOLVING_TOOL_SYSTEM_PROMPT.format(model_info=model_text)
    user_prompt = SOLVING_TOOL_USER_TEMPLATE.format(
        problem=state["problem_raw"],
        model=model_text,
    )
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    all_images: list[str] = []
    max_rounds = 10  # 工具调用轮数上限（每轮可并发多个工具）

    for _ in range(max_rounds):
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        tool_calls = getattr(response, "tool_calls", None) or []
        if not tool_calls:
            break  # LLM 停止调用工具 → 最后一条即结构化求解报告

        for tc in tool_calls:
            tool_name = tc.get("name")
            tool_args = tc.get("args") or {}
            tool = tool_map.get(tool_name)

            if tool is None:
                result_text = f"未知工具: {tool_name}"
            else:
                try:
                    result_text = tool.invoke(tool_args)
                except Exception as e:  # noqa: BLE001
                    result_text = f"工具执行失败: {e}"

            # 收集 run_code 产出的图表 URL
            if tool_name == "run_code":
                all_images.extend(_collect_image_urls(result_text))

            # 前端渲染工具调用卡片
            _pub_event(task_id, "tool_call", "solving_agent", {
                "tool_name": tool_name,
                "input": {k: (str(v)[:1500] if k == "code" else v) for k, v in tool_args.items()},
                "output": [{
                    "name": tool_name,
                    "preview": result_text[:1500],
                    "images": _collect_image_urls(result_text),
                }],
            })

            messages.append(ToolMessage(
                content=result_text,
                tool_call_id=tc.get("id") or tool_name,
            ))

    # 最终求解报告 = 最后一条 AI 文本消息
    final_output = ""
    for m in reversed(messages):
        if isinstance(m, AIMessage) and m.content and not (getattr(m, "tool_calls", None)):
            final_output = str(m.content)
            break

    if not final_output:
        # 兜底：轮数耗尽仍在调工具，强制让 LLM 基于已有结果总结
        fallback = llm.invoke(messages + [HumanMessage(
            content="请停止调用工具，基于以上已获得的全部求解结果，立即输出结构化求解报告。"
        )])
        final_output = str(fallback.content)

    _pub_event(task_id, "node_end", "solving_agent", {
        "step": idx + 1,
        "output_length": len(final_output),
        "images_count": len(all_images),
    })

    return {
        "solving_output": final_output,
        "current_step_index": idx,
        "messages": [
            SystemMessage(
                content=f"[求解Agent] 第{idx+1}步完成，"
                        f"图表 {len(all_images)} 张，"
                        f"输出 {len(final_output)} 字"
            )
        ],
    }


def _extract_code_block(text: str) -> str:
    """从 LLM 输出中提取 Python 代码块。"""
    import re
    match = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # 如果没有代码块标记，返回空（避免执行非代码内容）
    return ""


def verification_agent_node(state: AgentState) -> dict:
    """验证分析 Agent — 检验模型+结果，判定通过或回退。"""
    idx = _next_step(state)
    task_id = state["session_id"]
    _pub_event(task_id, "node_start", "verification_agent", {"step": idx + 1})
    llm = get_llm("verification", state.get("api_key_config"))

    if state["mode"] == "teach":
        system_prompt = VERIFICATION_TEACH_SYSTEM_PROMPT
        user_prompt = VERIFICATION_TEACH_USER_TEMPLATE.format(
            problem=state["problem_raw"],
            analysis=state.get("analysis_output", "无")[:2000],
            model=state.get("model_output", "无")[:2000],
            solving=state.get("solving_output", "无")[:2000],
        )
    else:
        system_prompt = VERIFICATION_SYSTEM_PROMPT
        user_prompt = VERIFICATION_USER_TEMPLATE.format(
            problem=state["problem_raw"],
            analysis=state.get("analysis_output", "无")[:2000],
            model=state.get("model_output", "无")[:2000],
            solving=state.get("solving_output", "无")[:2000],
        )

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])

    full_text = str(response.content)

    # 提取 JSON 判定块
    ver_json = {}
    json_match = re.search(r'\{[^{}]*"verdict"\s*:\s*"(PASS|FAIL)"[^{}]*\}', full_text)
    if json_match:
        try:
            ver_json = json.loads(json_match.group(0))
        except json.JSONDecodeError:
            ver_json = {}

    passed = ver_json.get("verdict", "PASS") == "PASS"
    rollback = ver_json.get("rollback_target", "modeling") if not passed else "modeling"

    # 如果有代码块，尝试执行灵敏度分析
    code = _extract_code_block(full_text)
    if code and passed:
        try:
            sandbox = SandboxExecutor()
            exec_result = sandbox.run(code)
            if exec_result["success"]:
                full_text += f"\n\n### 灵敏度分析执行结果\n```\n{exec_result['stdout'][:2000]}\n```\n"
        except Exception:
            pass

    _pub_event(task_id, "node_end", "verification_agent", {
        "step": idx + 1,
        "passed": passed,
        "rollback_target": rollback if not passed else None,
    })

    return {
        "verification_passed": passed,
        "verification_output": full_text,
        "verification_feedback": full_text[:500] if not passed else None,
        "rollback_target": rollback if not passed else None,
        "retry_count": state.get("retry_count", 0) + (0 if passed else 1),
        "current_step_index": idx,
        "messages": [
            SystemMessage(
                content=f"[验证Agent] 第{idx+1}步完成 — "
                        f"{'✅ 通过' if passed else '❌ 不通过，回退到 ' + rollback}"
            )
        ],
    }


# ── 论文章节规格（方案模式分章节写作）──────────────────────────────
# (章节标题, 写作要求) —— 顺序即生成顺序；摘要最后单独生成。
PAPER_SECTIONS: list[tuple[str, str]] = [
    ("一、问题重述",
     "用数学语言重述问题：明确已知量、未知量、优化/分析目标。"
     "不要照抄题目原文，要提炼出数学要素。篇幅 300-500 字。"),
    ("二、问题分析",
     "分析问题的关键特征、难点与建模思路，2-4 段，体现'表象→机理'的递进。"
     "不要罗列假设（假设在第三章），不要堆砌空话。"),
    ("三、模型假设与符号说明",
     "假设用有序列表，每条一句话，共 4-6 条，不给每条配冗长展开。"
     "符号说明用 Markdown 表格（符号 | 含义 | 单位）。假设与符号全文只在此处定义一次。"),
    ("四、模型的建立与求解",
     "核心章，占全文 50% 以上篇幅。按题目子问题分 ### 4.1 / 4.2 等小节。"
     "每个子问题必须包含：①原理与方法（为什么用、适用条件）②目标函数与约束（$$...$$ 公式块）"
     "③求解算法与过程 ④真实求解结果（具体数值，来自求解材料，禁止编造）⑤结果检验与分析。"
     "每个结论必须配证据（数值/表格/图），图表引用材料中真实的 /api/images/ 链接并配'图1 xxx'说明。"),
    ("五、模型检验与灵敏度分析",
     "独立成章（竞赛显式给分项）。①模型正确性检验（量纲、边界、与常识对比、误差分析）"
     "②对 1-2 个关键参数做灵敏度分析：参数如何变化、结果如何响应，用表格或图呈现，"
     "并给出'模型是否稳健'的结论。"),
    ("六、模型评价与改进",
     "优点 2-3 条、不足与改进方向 2-3 条，各一句话，具体不空泛。"),
    ("参考文献",
     "用 `[1] 作者. 文献名. 来源, 年份.` 格式列 3-5 条与建模方法相关的文献。"
     "**只引用你确定真实存在的经典文献**（如本领域公认的经典教材、专著、奠基性论文）；"
     "若输入材料（知识库检索/网络搜索结果）中含有真实文献，优先引用它们；"
     "严禁编造不知名论文的具体卷期页码——宁可只写'作者. 文献名. 年份'也不虚构出版细节。"),
]


def _clean_md(text: str) -> str:
    """去掉 LLM 输出外层的 Markdown 代码块标记。"""
    text = str(text)
    text = re.sub(r"^```(?:markdown|md)?\s*\n", "", text)
    text = re.sub(r"\n```\s*$", "", text)
    return text.strip()


def writing_agent_node(state: AgentState) -> dict:
    """论文写作 Agent。

    - teach 模式：引导式写作教学。
    - execute 模式：分章节流水线 ——
      大纲 → 逐章生成 → 摘要(最后写,提炼真实结果) → 拼装 → 红队审校 → 最小化修订。
    """
    idx = _next_step(state)
    task_id = state["session_id"]
    _pub_event(task_id, "node_start", "writing_agent", {"step": idx + 1})
    llm = get_llm("writing", state.get("api_key_config"))

    # ── teach 模式：保持原有教学输出 ──
    if state["mode"] == "teach":
        system_prompt = WRITING_TEACH_SYSTEM_PROMPT.format(
            analysis=state.get("analysis_output", "无")[:3000],
            model=state.get("model_output", "无")[:3000],
            solving=state.get("solving_output", "无")[:3000],
            verification=state.get("verification_output", "无")[:3000],
        )
        user_prompt = WRITING_TEACH_USER_TEMPLATE.format(problem=state["problem_raw"])
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])
        writing_output = _clean_md(response.content)
        _pub_event(task_id, "node_end", "writing_agent", {
            "step": idx + 1, "output_length": len(writing_output),
        })
        return {
            "writing_output": writing_output,
            "current_step_index": idx,
            "messages": [SystemMessage(content=f"[写作Agent] 第{idx+1}步完成（教学模式）")],
        }

    # ── execute 模式：分章节流水线 ──
    # 上下文 1M，各章共享完整材料，保证跨章一致与联想。
    # 按调用类型绑定合理的 max_tokens：单次只写一章/一段，无需 384K 全量预算，
    # 否则模型会放开了写超长内容，11 次串行调用慢到无法迭代。
    llm_outline = llm.bind(max_tokens=4096)
    llm_section = llm.bind(max_tokens=12000)
    llm_abstract = llm.bind(max_tokens=2048)
    llm_redteam = llm.bind(max_tokens=4096)
    llm_revise = llm.bind(max_tokens=65536)  # 修订会重生整篇，给足余量

    materials = {
        "problem": state["problem_raw"],
        "analysis": state.get("analysis_output", "无"),
        "model": state.get("model_output", "无"),
        "solving": state.get("solving_output", "无"),
        "verification": state.get("verification_output", "无"),
    }

    # 1) 大纲
    _pub_event(task_id, "node_progress", "writing_agent", {"stage": "outline"})
    outline = _clean_md(llm_outline.invoke([HumanMessage(
        content=WRITING_OUTLINE_PROMPT.format(**materials)
    )]).content)

    # 提取标题（大纲首行 "# xxx"）
    paper_title = "数学建模论文"
    first_line = outline.split("\n", 1)[0].strip()
    if first_line.startswith("#"):
        paper_title = first_line.lstrip("#").strip() or paper_title

    # 2) 逐章生成
    section_texts: list[str] = []
    for i, (title, requirements) in enumerate(PAPER_SECTIONS):
        _pub_event(task_id, "node_progress", "writing_agent",
                   {"stage": "section", "title": title, "index": i + 1})
        sec = _clean_md(llm_section.invoke([HumanMessage(
            content=WRITING_SECTION_PROMPT.format(
                outline=outline, section_title=title,
                section_requirements=requirements, **materials,
            )
        )]).content)
        if sec and not sec.startswith("##"):
            sec = f"## {title}\n\n{sec}"
        section_texts.append(sec)

    # 3) 摘要最后写（提炼正文真实结果）
    _pub_event(task_id, "node_progress", "writing_agent", {"stage": "abstract"})
    paper_body = "\n\n".join(section_texts)
    abstract = _clean_md(llm_abstract.invoke([HumanMessage(
        content=WRITING_ABSTRACT_PROMPT.format(outline=outline, paper_body=paper_body)
    )]).content)

    # 4) 拼装：标题 + 摘要 + 正文
    paper = f"# {paper_title}\n\n{abstract}\n\n{paper_body}"

    # 5) 红队审校（合规 + 洞察双 gate）
    _pub_event(task_id, "node_progress", "writing_agent", {"stage": "red_team"})
    critique = _clean_md(llm_redteam.invoke([HumanMessage(
        content=RED_TEAM_PROMPT.format(paper=paper)
    )]).content)

    # 6) 有实质问题则最小化修订一轮
    if critique and "PASS" not in critique.upper().split("\n")[0]:
        _pub_event(task_id, "node_progress", "writing_agent", {"stage": "revise"})
        revised = _clean_md(llm_revise.invoke([HumanMessage(
            content=WRITING_REVISE_PROMPT.format(paper=paper, critique=critique)
        )]).content)
        if revised and len(revised) > len(paper) // 2:  # 修订结果应大体完整
            paper = revised

    writing_output = paper

    _pub_event(task_id, "node_end", "writing_agent", {
        "step": idx + 1,
        "output_length": len(writing_output),
        "red_team": "PASS" if "PASS" in critique.upper().split("\n")[0] else "REVISED",
    })

    return {
        "writing_output": writing_output,
        "current_step_index": idx,
        "messages": [
            SystemMessage(
                content=f"[写作Agent] 第{idx+1}步完成，"
                        f"论文 {len(writing_output)} 字"
            )
        ],
    }


# ============================================================
# 节点: 格式化输出
# ============================================================
def format_response(state: AgentState) -> dict:
    """整合所有 agent 输出，按模式格式化。"""
    task_id = state["session_id"]
    _pub_event(task_id, "node_start", "format_response")

    if state["mode"] == "teach":
        final = _format_teach_response(state)
    else:
        final = _format_execute_response(state)

    _pub_event(task_id, "node_end", "format_response", {
        "mode": state["mode"],
        "output_length": len(final),
    })

    return {
        "final_response": final,
        "messages": [SystemMessage(content="编排完成，最终结果已生成。")],
    }


def _format_execute_response(state: AgentState) -> str:
    """方案输出模式: 以写作Agent的完整论文为最终输出。

    各阶段中间产出（analysis/model/solving/verification）已通过
    node_end 进度事件展示给用户，不再重复拼进最终论文，
    否则会出现"假设写两遍、约束写两遍"的内容重复。
    """
    writing = state.get("writing_output")
    if writing:
        return writing

    # 兜底：写作节点未产出时，退化为拼接中间结果
    parts = []
    if state.get("analysis_output"):
        parts.append(state["analysis_output"])
    if state.get("model_output"):
        parts.append(state["model_output"])
    if state.get("solving_output"):
        parts.append(state["solving_output"])
    if state.get("verification_output"):
        parts.append(state["verification_output"])
    return "\n\n---\n\n".join(parts) if parts else "（无输出）"


def _format_teach_response(state: AgentState) -> str:
    """教学模式: 整合为苏格拉底式引导对话。"""
    parts = ["## 🎓 教学模式 — 引导式分析\n"]

    if state.get("analysis_output"):
        parts.append("### 💡 问题思考引导\n")
        parts.append(state["analysis_output"])
        parts.append("")

    if state.get("model_output"):
        parts.append("### 🧩 模型思路启发\n")
        parts.append(state["model_output"])
        parts.append("")

    if state.get("solving_output"):
        parts.append("### 🔧 求解方向提示\n")
        parts.append(state["solving_output"])
        parts.append("")

    if state.get("verification_output"):
        parts.append("### ✅ 自检清单\n")
        parts.append(state["verification_output"])
        parts.append("")

    if state.get("writing_output"):
        parts.append("### 📝 框架建议\n")
        parts.append(state["writing_output"])
        parts.append("")

    if len(parts) <= 1:
        return "（教学模式 — 引导式对话待实现）"

    return "\n".join(parts)


# ============================================================
# 工具函数
# ============================================================
def _extract_json(text: str) -> dict | list:
    """从 LLM 输出中提取 JSON。"""
    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试提取 ```json ... ``` 代码块
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # 尝试提取 { } 或 [ ]
    for pattern in [r"\{[\s\S]*\}", r"\[[\s\S]*\]"]:
        match = re.search(pattern, text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                continue

    return {}
