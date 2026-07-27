"""图节点函数 — classify / retrieve / plan / agent / format。"""

import json
import re
import time
from pathlib import Path
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage

from app.config import get_settings
from app.core.state import AgentState
from app.knowledge.loader import KnowledgeBaseLoader
from app.knowledge.retriever import HybridRetriever
from app.sandbox.executor import SandboxExecutor
from app.services.redis_pubsub import get_publisher

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
)
from .prompts.verification import (
    VERIFICATION_SYSTEM_PROMPT, VERIFICATION_USER_TEMPLATE,
    VERIFICATION_TEACH_SYSTEM_PROMPT, VERIFICATION_TEACH_USER_TEMPLATE,
)
from .prompts.writing import (
    WRITING_SYSTEM_PROMPT, WRITING_USER_TEMPLATE,
    WRITING_TEACH_SYSTEM_PROMPT, WRITING_TEACH_USER_TEMPLATE,
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


def solving_agent_node(state: AgentState) -> dict:
    """求解计算 Agent — 生成代码、沙箱执行、错误修正、图表输出。"""
    idx = _next_step(state)
    task_id = state["session_id"]
    _pub_event(task_id, "node_start", "solving_agent", {"step": idx + 1})
    llm = get_llm("solving", state.get("api_key_config"))
    sandbox = SandboxExecutor()

    model_text = state.get("model_output") or "无模型"

    if state["mode"] == "teach":
        system_prompt = SOLVING_TEACH_SYSTEM_PROMPT.format(model_info=model_text[:3000])
        user_prompt = SOLVING_TEACH_USER_TEMPLATE.format(
            problem=state["problem_raw"],
            model=model_text[:3000],
        )
    else:
        system_prompt = SOLVING_SYSTEM_PROMPT.format(model_info=model_text[:3000])
        user_prompt = SOLVING_USER_TEMPLATE.format(
            problem=state["problem_raw"],
            model=model_text[:3000],
        )

    # 最多重试 2 次
    max_attempts = 2
    all_images: list[str] = []
    final_output = ""

    for attempt in range(max_attempts + 1):
        # 第一次调用 LLM，重试时附加错误信息
        if attempt == 0:
            prompt = user_prompt
        else:
            prompt = (
                f"{user_prompt}\n\n"
                f"【重要】上次代码执行失败，请修正：\n"
                f"错误信息：\n```\n{last_error[:1000]}\n```\n"
                f"请修复代码并重新输出完整的求解方案。"
            )

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt),
        ])

        full_text = str(response.content)

        # 提取代码块
        code = _extract_code_block(full_text)
        if not code:
            final_output = full_text
            break

        # 沙箱执行
        exec_result = sandbox.run(code)

        if exec_result["success"]:
            # 成功 — 拼接完整输出
            images = exec_result.get("images", [])
            run_id = exec_result.get("run_id", "")
            # 本地路径 → HTTP URL（前端通过 /api/images/{run_id}/{filename} 访问）
            image_urls = [
                f"/api/images/{run_id}/{Path(p).name}" for p in images
            ] if run_id else []
            all_images = image_urls
            final_output = (
                f"{full_text}\n\n"
                f"### 执行结果\n```\n{exec_result['stdout'][:2000]}\n```\n"
            )
            if image_urls:
                final_output += f"\n生成图表: {len(image_urls)} 张\n"
                for url in image_urls:
                    final_output += f"\n![图表]({url})\n"

            # 发布 tool_call 事件，前端渲染代码执行卡片（代码/stdout/图表）
            _pub_event(task_id, "tool_call", "solving_agent", {
                "tool_name": "run_code",
                "input": {"code": code[:3000]},
                "output": [{
                    "name": "run_code",
                    "preview": (exec_result['stdout'][:1500] or "执行完成（无标准输出）"),
                    "images": image_urls,
                }],
            })
            break
        else:
            last_error = exec_result.get("stderr", "")
            if attempt < max_attempts:
                print(f"[求解Agent] 第{attempt+1}次执行失败，重试中...")
            else:
                final_output = (
                    f"{full_text}\n\n"
                    f"### 执行失败（已重试{max_attempts}次）\n"
                    f"```\n{last_error[:1000]}\n```"
                )

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


def writing_agent_node(state: AgentState) -> dict:
    """论文写作 Agent — 整合全流程输出为竞赛论文。"""
    idx = _next_step(state)
    task_id = state["session_id"]
    _pub_event(task_id, "node_start", "writing_agent", {"step": idx + 1})
    llm = get_llm("writing", state.get("api_key_config"))

    if state["mode"] == "teach":
        system_prompt = WRITING_TEACH_SYSTEM_PROMPT.format(
            analysis=state.get("analysis_output", "无")[:3000],
            model=state.get("model_output", "无")[:3000],
            solving=state.get("solving_output", "无")[:3000],
            verification=state.get("verification_output", "无")[:3000],
        )
        user_prompt = WRITING_TEACH_USER_TEMPLATE.format(problem=state["problem_raw"])
    else:
        # DeepSeek V4 Pro 上下文 1M，写作阶段直接吃完整中间产出，
        # 不做截断，确保论文能引用全部求解结果与数值。
        system_prompt = WRITING_SYSTEM_PROMPT.format(
            analysis=state.get("analysis_output", "无"),
            model=state.get("model_output", "无"),
            solving=state.get("solving_output", "无"),
            verification=state.get("verification_output", "无"),
        )
        user_prompt = WRITING_USER_TEMPLATE.format(problem=state["problem_raw"])

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])

    writing_output = str(response.content)

    # 清理 Markdown 代码块标记
    import re
    writing_output = re.sub(r"^```(?:markdown|md)?\s*\n", "", writing_output)
    writing_output = re.sub(r"\n```\s*$", "", writing_output)

    # 续写兜底：Markdown 论文以"参考文献"为末章，若缺失且正文偏长，
    # 视为被 max_tokens 截断，续写补全（max_tokens 已拉满，极少触发）。
    max_continuations = 2
    for _ in range(max_continuations):
        if "参考文献" in writing_output or len(writing_output) < 2000:
            break
        _pub_event(task_id, "node_progress", "writing_agent", {"continuing": True})
        cont_resp = llm.invoke([
            SystemMessage(content="请继续输出被截断的论文，从上次中断处接着写，不要重复已有内容，直到写完参考文献章节。"),
            HumanMessage(content=f"已生成内容（结尾部分）：\n```\n{writing_output[-2000:]}\n```\n请从这里继续："),
        ])
        cont_text = str(cont_resp.content)
        cont_text = re.sub(r"^```(?:markdown|md)?\s*\n", "", cont_text)
        cont_text = re.sub(r"\n```\s*$", "", cont_text)
        if not cont_text.strip():
            break
        writing_output += "\n" + cont_text

    _pub_event(task_id, "node_end", "writing_agent", {
        "step": idx + 1,
        "output_length": len(writing_output),
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
