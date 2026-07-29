"""知识图谱构建与查询 — 基于现有方法卡片提取依赖关系.

技能树为有向图: 节点=知识点, 边=前置依赖/横向关联/难度递进.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class SkillNode:
    """知识图谱中的技能节点"""
    node_id: str
    name: str
    category: str = ""              # 优化/预测/评价/统计/...
    difficulty: int = 1             # 1=入门 2=进阶 3=竞赛
    role: str = "all"               # modeler/programmer/writer/all
    method_card_id: str = ""        # 关联的方法卡片ID
    description: str = ""
    mastery: float = 0.0            # 当前用户掌握度 (运行时赋值)


@dataclass
class SkillEdge:
    """技能节点之间的边"""
    source: str          # 前置节点
    target: str          # 后置节点
    edge_type: str       # "prerequisite" | "related" | "progression"
    description: str = ""


@dataclass
class KnowledgeGraph:
    """技能知识图谱"""
    nodes: dict[str, SkillNode] = field(default_factory=dict)
    edges: list[SkillEdge] = field(default_factory=list)

    def add_node(self, node: SkillNode) -> None:
        self.nodes[node.node_id] = node

    def add_edge(self, source: str, target: str,
                 edge_type: str = "prerequisite",
                 description: str = "") -> None:
        self.edges.append(SkillEdge(
            source=source, target=target,
            edge_type=edge_type, description=description,
        ))

    def get_prerequisites(self, node_id: str) -> list[str]:
        """获取某个节点的直接前置依赖"""
        return [e.source for e in self.edges
                if e.target == node_id and e.edge_type == "prerequisite"]

    def get_related(self, node_id: str) -> list[str]:
        """获取横向关联节点"""
        related = []
        for e in self.edges:
            if e.edge_type == "related":
                if e.source == node_id:
                    related.append(e.target)
                elif e.target == node_id:
                    related.append(e.source)
        return related

    def get_unlockable(self, completed_ids: set[str]) -> list[str]:
        """根据已完成的节点，返回可以解锁的节点"""
        unlockable = []
        for node_id, node in self.nodes.items():
            if node_id in completed_ids:
                continue
            prereqs = set(self.get_prerequisites(node_id))
            if prereqs.issubset(completed_ids):
                unlockable.append(node_id)
        return unlockable

    def get_nodes_by_category(self, category: str) -> list[SkillNode]:
        return [n for n in self.nodes.values() if n.category == category]

    def get_nodes_by_role(self, role: str) -> list[SkillNode]:
        return [n for n in self.nodes.values()
                if n.role == role or n.role == "all"]


# ── 从方法卡片构建知识图谱 ──────────────────────────────

def build_graph_from_method_cards(kb_dir: str) -> KnowledgeGraph:
    """从 knowledge_base/methods/ 中的 YAML 方法卡片构建知识图谱.

    每个方法卡片生成一个节点, related_cards 转化为横向关联边,
    prerequisites (卡片中如有定义) 转化为前置依赖边.
    """
    graph = KnowledgeGraph()
    methods_path = Path(kb_dir) / "methods"

    if not methods_path.exists():
        return graph

    cards: list[dict] = []
    for yf in sorted(methods_path.glob("*.yaml")):
        try:
            with open(yf, encoding="utf-8") as f:
                card = yaml.safe_load(f)
                if card:
                    cards.append(card)
        except Exception:
            continue

    # 第一遍: 创建节点
    for card in cards:
        cid = card.get("id", "")
        if not cid:
            continue

        category = ""
        cats = card.get("category", [])
        if cats:
            category = cats[0]

        node = SkillNode(
            node_id=cid,
            name=card.get("name", cid),
            category=category,
            difficulty=_difficulty_from_tags(card.get("difficulty", "beginner")),
            role=_role_from_card(card),
            method_card_id=cid,
            description=card.get("principle", "")[:200],
        )
        graph.add_node(node)

    # 第二遍: 创建边
    for card in cards:
        cid = card.get("id", "")
        if not cid:
            continue

        # related_cards → 横向关联边
        for related in card.get("related_cards", []) or []:
            if related in graph.nodes:
                graph.add_edge(cid, related, "related",
                               description=f"{card.get('name', '')} ↔ {graph.nodes[related].name}")

        # related_papers 如果引用了其他卡片的方法 → 也可视为关联
        for paper_ref in card.get("related_papers", []) or []:
            pass  # 论文引用暂不建边，后续可通过论文ID查找

    return graph


def _difficulty_from_tags(d: str) -> int:
    mapping = {"beginner": 1, "intermediate": 2, "advanced": 3, "competition": 3}
    return mapping.get(d, 1)


def _role_from_card(card: dict) -> str:
    """根据方法卡片的内容推断适合哪个角色."""
    categories = [c.lower() for c in card.get("category", [])]
    code_snippets = card.get("code_snippets", []) or []

    has_code = bool(code_snippets)
    is_math_heavy = any(c in " ".join(categories) for c in
                        ["优化", "微分方程", "图论", "统计"])

    if has_code and is_math_heavy:
        return "all"
    elif has_code:
        return "programmer"
    else:
        return "modeler"


# ── 全局单例 ──────────────────────────────────────────

_graph: Optional[KnowledgeGraph] = None


def get_knowledge_graph(kb_dir: str = "") -> KnowledgeGraph:
    global _graph
    if _graph is None and kb_dir:
        _graph = build_graph_from_method_cards(kb_dir)
    return _graph or KnowledgeGraph()
