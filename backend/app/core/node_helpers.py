"""编排器节点辅助层 — 从 nodes.py 抽出的纯辅助函数与哨兵异常（god-files 拆分 #31）。

节点函数本体仍在 nodes.py；本模块无节点依赖，可独立单测。
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import shutil
import tempfile
from pathlib import Path

from app.config import get_settings
from app.services.redis_pubsub import get_publisher

from .state import AgentState

logger = logging.getLogger(__name__)


class TaskCancelledError(Exception):
    """任务被取消时的哨兵异常 — 用于在节点内提前终止编排器。"""


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


def _check_cancelled(task_id: str) -> None:
    """节点入口的取消检查：已取消则抛哨兵异常，让编排器提前退出。"""
    if _is_cancelled(task_id):
        raise TaskCancelledError(task_id)


def _save_working_memory(session_id: str, stage: str, output: str, extra: dict | None = None):
    """保存阶段检查点 + 异步更新问题状态文档。

    检查点同步写入（保证断电不丢失），
    整体重写异步执行（不阻塞工作流）。
    """
    try:
        from app.services.working_memory import WorkingMemory

        wm = WorkingMemory(session_id)
        wm.save_checkpoint(stage, output, extra)
    except Exception as e:  # noqa: BLE001
        # 工作记忆不阻塞主流程，但记录失败便于排查
        logger.warning(
            "工作记忆检查点保存失败 (session=%s, stage=%s): %s",
            session_id,
            stage,
            e,
        )
        return

    # LLM 重写放后台线程，不阻塞流水线；
    # 当前线程无运行事件循环时跳过异步重写（检查点已保存，问题文档留待下次更新）
    try:
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, wm.update_problem_doc, stage, output, None)
    except RuntimeError:
        logger.warning(
            "当前线程无运行事件循环，跳过问题文档异步重写 (session=%s, stage=%s)",
            session_id,
            stage,
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(
            "问题文档异步重写失败 (session=%s, stage=%s): %s",
            session_id,
            stage,
            e,
        )


# ============================================================
# 节点 1: 问题分类
# ============================================================
def _next_step(state: AgentState) -> int:
    """获取当前步骤索引并递增。"""
    return state.get("current_step_index", -1) + 1


def _collect_image_urls(text: str) -> list[str]:
    """从工具输出文本中提取 /api/images/... 形式的图表 URL。"""
    return re.findall(r"/api/images/[^\s,，)）'\"]+\.png", text or "")


def _collect_file_urls(text: str, suffix: str) -> list[str]:
    """从工具输出文本中提取指定后缀的文件 URL。"""
    pattern = rf"/api/task_files/[^\s,，)）'\"]+\.{suffix}"
    return re.findall(pattern, text or "")


def _persist_task_files(
    task_id: str,
    image_urls: list[str] = (),
    xlsx_urls: list[str] = (),
    csv_urls: list[str] = (),
    html_urls: list[str] = (),
) -> dict[str, list[str]]:
    """把沙箱临时目录里的所有文件复制到任务持久目录，并登记进文件区。

    返回持久化后的各类 URL 列表。
    """
    from app.services.session import get_session_manager

    settings = get_settings()
    task_dir = settings.project_root / "data" / "task_files" / task_id
    temp_root = Path(tempfile.gettempdir()) / "mathmodel_outputs"
    session_mgr = get_session_manager()

    def _persist(urls: list[str], file_type: str) -> list[str]:
        durable: list[str] = []
        for url in urls:
            try:
                parts = url.rstrip("/").split("/")
                run_id_or_task_id, filename = parts[-2], parts[-1]
                src = temp_root / run_id_or_task_id / filename
                if not src.exists():
                    # 也可能在 task_files 目录
                    src = task_dir / filename
                if not src.exists():
                    continue
                task_dir.mkdir(parents=True, exist_ok=True)
                dst = task_dir / filename
                if not dst.exists():
                    shutil.copy2(src, dst)
                durable_url = f"/api/task_files/{task_id}/{filename}"
                session_mgr.add_artifact(
                    task_id,
                    {
                        "type": file_type,
                        "name": filename,
                        "url": durable_url,
                        "size": dst.stat().st_size,
                    },
                )
                durable.append(durable_url)
            except Exception:  # noqa: BLE001
                continue
        return durable

    return {
        "images": _persist(image_urls, "figure"),
        "xlsx": _persist(xlsx_urls, "xlsx"),
        "csv": _persist(csv_urls, "csv"),
        "html": _persist(html_urls, "html"),
    }


def _persist_task_images(task_id: str, image_urls: list[str]) -> list[str]:
    """把沙箱临时目录里的图表复制到任务持久目录，并登记进文件区。

    返回持久化后的 /api/task_files/{task_id}/{filename} URL 列表。
    """
    return _persist_task_files(task_id, image_urls=image_urls)["images"]


def _extract_code_block(text: str) -> str:
    """从 LLM 输出中提取 Python 代码块。"""
    import re

    match = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # 如果没有代码块标记，返回空（避免执行非代码内容）
    return ""


def _clean_md(text: str) -> str:
    """去掉 LLM 输出外层的 Markdown 代码块标记。"""
    text = str(text)
    text = re.sub(r"^```(?:markdown|md)?\s*\n", "", text)
    text = re.sub(r"\n```\s*$", "", text)
    return text.strip()


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


def _log_usage(task_id: str, node: str, response) -> None:
    """记录一次 LLM 调用的 token 用量（管线成本可观测性）。"""
    try:
        usage = getattr(response, "usage_metadata", None) or {}
        if usage:
            logger.info(
                "LLM 用量 [%s/%s]: in=%s out=%s total=%s",
                task_id,
                node,
                usage.get("input_tokens"),
                usage.get("output_tokens"),
                usage.get("total_tokens"),
            )
    except Exception:
        pass  # 用量缺失不影响主流程


def invoke_with_retry(llm, messages, task_id: str = "", node: str = "", retries: int = 2):
    """LLM 调用统一重试（指数退避 1s/2s）：抗 API 抖动、429、超时等瞬时故障。

    确定性错误（如 API Key 无效）重试后仍会抛出，错误照常上浮。
    """
    import time as _time

    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return llm.invoke(messages)
        except Exception as e:  # noqa: BLE001
            last_exc = e
            if attempt >= retries:
                break
            delay = 2**attempt  # 1s, 2s
            logger.warning(
                "LLM 调用失败 [%s/%s] 第 %d 次，%.0fs 后重试: %s",
                task_id,
                node or "llm",
                attempt + 1,
                delay,
                str(e)[:200],
            )
            _time.sleep(delay)
    raise last_exc  # type: ignore[misc]


def _extract_verdict_json(text: str) -> dict:
    """从验证节点输出提取含 verdict 的判定 JSON（容忍前后散文、嵌套、围栏）。

    替代旧的正则 `\\{[^{}]*"verdict"...\\}`（嵌套/跨行即失败）：
    先复用 _extract_json，失败时定位第一个含 "verdict" 的平衡花括号块。
    """
    parsed = _extract_json(str(text))
    if isinstance(parsed, dict) and "verdict" in parsed:
        return parsed

    text = str(text)
    start = text.find('"verdict"')
    if start < 0:
        return {}
    brace = text.rfind("{", 0, start)
    if brace < 0:
        return {}
    depth = 0
    for i in range(brace, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    obj = json.loads(text[brace : i + 1])
                    return obj if isinstance(obj, dict) else {}
                except json.JSONDecodeError:
                    return {}
    return {}
