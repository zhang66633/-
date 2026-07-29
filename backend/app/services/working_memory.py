"""工作记忆 — 方案模式问题状态文档 + 阶段检查点。

每个 solution 会话维护:
  - problem_doc.md:       持续更新的问题状态文档（LLM 整体重写）
  - checkpoints/*.json:   每个阶段独立的检查点（可恢复）
  - problem_doc.*.bak:    重写前快照（保留 10 份）

设计参考: MEMORY_CONTEXT_GUIDE.md §5.1
"""

from __future__ import annotations

import json
import shutil
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)

# ── 阶段顺序映射 ────────────────────────────────────────────

STAGE_ORDER = [
    "classify",
    "retrieve",
    "analysis",
    "modeling",
    "solving",
    "verification",
    "writing",
]

STAGE_LABELS = {
    "classify": "一、问题分类",
    "retrieve": "二、知识检索",
    "analysis": "三、问题分析",
    "modeling": "四、模型建立",
    "solving": "五、求解计算",
    "verification": "六、验证分析",
    "writing": "七、论文写作",
}

# ── 重写 prompt ─────────────────────────────────────────────

REWRITE_PROMPT = """你是一个数学建模问题状态管理器。根据已完成阶段的最新输出，更新下面的问题状态文档。

## 当前文档
{current_doc}

## 本次新增阶段: {stage_label}
{stage_output}

## 已完成的全部阶段
{completed_stages}

## 规则
1. 这是状态档案，不是日志。每个章节记录"结论是什么"，不是"发生了什么"
2. 整合新内容到对应章节，保持结构清晰
3. 合并重复信息，删除矛盾内容（以最新为准）
4. 总字数控制在 3000 字以内
5. 如果新内容与已有内容无实质变化，只更新对应章节
6. 保持 Markdown 格式，按以下章节结构组织:

# 问题状态文档
- 一、问题分类（问题类型、复杂度、数据依赖）
- 二、知识检索（推荐方法、参考论文、匹配模板）
- 三、问题分析（结构化分析结果）
- 四、模型建立（模型假设、公式、变量定义）
- 五、求解计算（代码要点、求解结果、图表）
- 六、验证分析（验证结论、灵敏度、改进方向）
- 七、论文写作（论文全文摘要）

输出完整的新文档（不是 diff）："""


class WorkingMemory:
    """方案模式会话的工作记忆管理器。"""

    def __init__(self, session_id: str):
        settings = get_settings()
        self.session_id = session_id
        self.session_dir = settings.project_root / "data" / "sessions" / session_id
        self.checkpoints_dir = self.session_dir / "checkpoints"
        self.problem_doc_path = self.session_dir / "problem_doc.md"
        self.messages_path = self.session_dir / "messages.json"
        self._max_backups = 10

    # ── 初始化 ──────────────────────────────────────────────

    def init_session(self, problem_raw: str) -> None:
        """新建会话目录 + 初始 problem_doc。"""
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)

        if not self.problem_doc_path.exists():
            initial = f"""# 问题状态文档

## 一、问题分类
（待完成）

## 二、知识检索
（待完成）

## 三、问题分析
（待完成）

## 四、模型建立
（待完成）

## 五、求解计算
（待完成）

## 六、验证分析
（待完成）

## 七、论文写作
（待完成）

---

**原始问题**:
{problem_raw[:500]}
"""
            self._atomic_write(self.problem_doc_path, initial)

    # ── 检查点 ──────────────────────────────────────────────

    def save_checkpoint(self, stage: str, output: str, extra: dict | None = None) -> Path:
        """保存阶段检查点。返回 checkpoint 文件路径。"""
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "stage": stage,
            "stage_label": STAGE_LABELS.get(stage, stage),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "output_summary": output[:500],
            "output": output,
            **(extra or {}),
        }
        path = self.checkpoints_dir / f"{stage}.json"
        self._atomic_write_json(path, data)
        return path

    def load_checkpoint(self, stage: str) -> dict | None:
        """加载指定阶段的检查点。"""
        path = self.checkpoints_dir / f"{stage}.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            logger.warning("检查点损坏: %s", path)
            return None

    def get_completed_stages(self) -> list[str]:
        """返回已完成的阶段列表（有序）。"""
        completed = []
        for stage in STAGE_ORDER:
            if (self.checkpoints_dir / f"{stage}.json").exists():
                completed.append(stage)
        return completed

    def get_latest_stage(self) -> str | None:
        """返回最新已完成的阶段名。"""
        completed = self.get_completed_stages()
        return completed[-1] if completed else None

    def get_resume_stage(self) -> str | None:
        """返回应该从哪个阶段恢复（最新完成阶段的下一个）。"""
        completed = self.get_completed_stages()
        if not completed:
            return None
        last = completed[-1]
        try:
            idx = STAGE_ORDER.index(last)
            if idx + 1 < len(STAGE_ORDER):
                return STAGE_ORDER[idx + 1]
        except ValueError:
            pass
        return None

    # ── 问题状态文档 ────────────────────────────────────────

    def get_problem_doc(self) -> str:
        """读取当前问题状态文档。"""
        if self.problem_doc_path.exists():
            return self.problem_doc_path.read_text(encoding="utf-8")
        return ""

    def update_problem_doc(
        self,
        stage: str,
        stage_output: str,
        completed_stages: list[str] | None = None,
    ) -> str | None:
        """用 LLM 整体重写问题状态文档。

        Returns:
            新文档内容，LLM 不可用时返回 None。
        """
        current = self.get_problem_doc()
        if not current:
            return None

        completed = completed_stages or self.get_completed_stages()
        stage_label = STAGE_LABELS.get(stage, stage)
        completed_labels = ", ".join(STAGE_LABELS.get(s, s) for s in completed)

        prompt = REWRITE_PROMPT.format(
            current_doc=current,
            stage_label=stage_label,
            stage_output=stage_output[:3000],
            completed_stages=completed_labels,
        )

        try:
            from ..core.llm.factory import get_llm
            llm = get_llm("analysis")  # 用 analysis 模型做轻量重写
            response = llm.invoke(prompt)
            new_doc = str(response.content).strip()
        except Exception as e:
            logger.warning("LLM 整体重写失败，跳过: %s", e)
            return None

        if not new_doc or len(new_doc) < 50:
            logger.warning("LLM 重写输出过短，跳过更新")
            return None

        # 备份旧版本
        self._backup_problem_doc()

        # 原子写入新版本
        self._atomic_write(self.problem_doc_path, new_doc)
        return new_doc

    # ── 消息持久化 ──────────────────────────────────────────

    def save_messages(self, messages: list[dict]) -> None:
        """持久化前端展示消息（原子写入）。"""
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self._atomic_write_json(self.messages_path, messages)

    def load_messages(self) -> list[dict]:
        """加载持久化的消息列表。"""
        if not self.messages_path.exists():
            return []
        try:
            return json.loads(self.messages_path.read_text(encoding="utf-8"))
        except Exception:
            logger.warning("消息文件损坏: %s", self.messages_path)
            return []

    # ── 会话状态 ────────────────────────────────────────────

    def is_active(self) -> bool:
        """检查会话是否存在未完成的任务。"""
        if not self.problem_doc_path.exists():
            return False
        completed = self.get_completed_stages()
        return len(completed) > 0 and len(completed) < len(STAGE_ORDER)

    # ── 工具方法 ────────────────────────────────────────────

    def _backup_problem_doc(self) -> None:
        """备份当前 problem_doc，保留最近 N 份。"""
        if not self.problem_doc_path.exists():
            return
        # 清理旧备份
        backups = sorted(self.session_dir.glob("problem_doc.*.bak"))
        for old in backups[:-(self._max_backups - 1)]:
            try:
                old.unlink()
            except Exception:
                pass
        # 创建新备份
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.session_dir / f"problem_doc.{ts}.bak"
        shutil.copy2(self.problem_doc_path, backup_path)

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        """原子写入：先写 .tmp 再 rename，崩溃不留残骸。"""
        tmp = path.with_suffix(".tmp")
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(path)

    @staticmethod
    def _atomic_write_json(path: Path, data: Any) -> None:
        """原子写入 JSON。"""
        tmp = path.with_suffix(".tmp")
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
