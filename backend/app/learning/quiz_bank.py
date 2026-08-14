"""静态选择题题库加载器 — 合并 learning/quiz_data/*.yaml,提供筛选与答案裁剪。

数据文件约定: quiz_data/ 下每个 *.yaml 是一批题目(按角色/批次拆分,便于并行编写),
加载时合并为单一题库;对外一律经 public_view 裁剪 answer_index,防止答案泄露。
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

QUIZ_DATA_DIR = Path(__file__).resolve().parent / "quiz_data"

_QUERYABLE_FIELDS = ("category", "difficulty", "role", "unit_id")

# 稳定排序键: 角色 → 类别 → 难度 → id(保证每题永久题号不随加载顺序漂移)
_ROLE_ORDER = {"modeler": 0, "programmer": 1, "writer": 2}
_CATEGORY_ORDER = {
    "优化": 0,
    "预测": 1,
    "评价": 2,
    "统计": 3,
    "图论": 4,
    "微分方程": 5,
    "综合": 6,
    "编程": 7,
    "论文写作": 8,
}
_DIFF_ORDER = {"beginner": 0, "intermediate": 1, "advanced": 2}


def _sort_key(q: dict):
    return (
        _ROLE_ORDER.get(q["role"], 9),
        _CATEGORY_ORDER.get(q["category"], 9),
        _DIFF_ORDER.get(q["difficulty"], 9),
        q["id"],
    )


@lru_cache(maxsize=1)
def _load_all() -> list[dict]:
    """加载并合并全部题库文件,按稳定规则排序(带缓存)。"""
    questions: list[dict] = []
    seen_ids: set[str] = set()
    for f in sorted(QUIZ_DATA_DIR.glob("*.yaml")):
        if f.name.startswith("_"):
            continue
        batch = yaml.safe_load(f.read_text(encoding="utf-8")) or []
        for q in batch:
            qid = q.get("id")
            if not qid:
                raise ValueError(f"{f.name} 存在缺少 id 的题目")
            if qid in seen_ids:
                raise ValueError(f"题库 id 重复: {qid}")
            seen_ids.add(qid)
            _validate_question(q, f.name)
            questions.append(q)
    questions.sort(key=_sort_key)
    return questions


def _validate_question(q: dict, source: str) -> None:
    required = (
        "id",
        "unit_id",
        "role",
        "category",
        "difficulty",
        "question",
        "options",
        "answer_index",
        "explanation",
    )
    missing = [k for k in required if k not in q]
    if missing:
        raise ValueError(f"{source} 题目 {q.get('id')} 缺少字段: {missing}")
    if len(q["options"]) != 4:
        raise ValueError(f"{source} 题目 {q['id']} 选项数必须为 4")
    if not all(isinstance(o, str) for o in q["options"]):
        # YAML 常见坑: 选项含「冒号+空格」未加引号被解析成 dict
        raise ValueError(
            f"{source} 题目 {q['id']} 选项必须全部为字符串(检查含冒号的值是否未加引号)"
        )
    if not (0 <= q["answer_index"] < 4):
        raise ValueError(f"{source} 题目 {q['id']} answer_index 越界")
    if q["role"] not in ("modeler", "programmer", "writer"):
        raise ValueError(f"{source} 题目 {q['id']} role 非法: {q['role']}")
    if q["difficulty"] not in ("beginner", "intermediate", "advanced"):
        raise ValueError(f"{source} 题目 {q['id']} difficulty 非法: {q['difficulty']}")


def list_questions(**filters: str | None) -> list[dict]:
    """按字段过滤题库(未指定即不过滤),返回内部完整结构。"""
    result = _load_all()
    for key, value in filters.items():
        if value is None or value == "" or key not in _QUERYABLE_FIELDS:
            continue
        result = [q for q in result if q.get(key) == value]
    return result


def get_question(question_id: str) -> dict | None:
    for q in _load_all():
        if q["id"] == question_id:
            return q
    return None


def get_by_unit(unit_id: str) -> list[dict]:
    return list_questions(unit_id=unit_id)


def question_no(question_id: str) -> int | None:
    """题目的永久题号(全库稳定排序中的序号,1 起)。"""
    for i, q in enumerate(_load_all(), start=1):
        if q["id"] == question_id:
            return i
    return None


def public_view(q: dict) -> dict:
    """题目对外视图: 去掉答案,保留题干/选项/元信息,附永久题号。"""
    return {
        "no": question_no(q["id"]),
        "id": q["id"],
        "unit_id": q["unit_id"],
        "role": q["role"],
        "category": q["category"],
        "difficulty": q["difficulty"],
        "question": q["question"],
        "options": q["options"],
        "tags": q.get("tags", []),
    }


def categories_summary(role: str | None = None) -> list[dict]:
    """各分类题数统计(供题库页筛选栏/统计条使用)。"""
    counts: dict[str, int] = {}
    for q in _load_all():
        if role and q["role"] != role:
            continue
        counts[q["category"]] = counts.get(q["category"], 0) + 1
    return [{"name": k, "count": v} for k, v in sorted(counts.items(), key=lambda x: -x[1])]


def total_count() -> int:
    return len(_load_all())
