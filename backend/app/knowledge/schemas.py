"""Knowledge base Pydantic schemas for YAML validation."""

from typing import List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class Formula(BaseModel):
    name: str = ""
    latex: str = ""
    description: str = ""


class CodeSnippet(BaseModel):
    language: str = ""
    description: str = ""
    code: str = ""


class Mistake(BaseModel):
    mistake: str = ""
    solution: str = ""


class MethodCard(BaseModel):
    id: str = Field(pattern=r"^mc_\d+$")
    name: str
    name_en: str = ""
    category: List[str]
    principle: str
    # 兼容纯字符串（新格式 "公式文本"）和结构化对象（旧格式 {name,latex,description}）
    formulas: List[Union[str, Formula]] = Field(default_factory=list)
    applicable_when: List[str] = Field(default_factory=list)
    not_applicable_when: List[str] = Field(default_factory=list)
    typical_scenarios: List[str] = Field(default_factory=list)
    common_mistakes: List[Union[str, Mistake]] = Field(default_factory=list)
    code_snippets: List[Union[str, CodeSnippet]] = Field(default_factory=list)
    related_cards: List[str] = Field(default_factory=list)
    related_papers: List[str] = Field(default_factory=list)
    difficulty: int = Field(ge=1, le=5, default=3)
    quality_rating: int = Field(ge=1, le=5, default=3)
    tags: dict = Field(default_factory=dict)


class PaperAnalysis(BaseModel):
    problem_summary: str = ""
    key_assumptions: List[str] = Field(default_factory=list)
    decision_variables: str = ""
    objective: str = ""
    constraints: str = ""


class PaperModel(BaseModel):
    approach: str = ""
    innovation: str = ""
    solution_method: str = ""


class PaperEvaluation(BaseModel):
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    lessons: str = ""


class Paper(BaseModel):
    """论文知识卡片 — 深度结构化拆解。

    分析、模型、评价三字段兼容两种格式：
    - 旧格式: 嵌套对象 (PaperAnalysis/PaperModel/PaperEvaluation)
    - 新格式: 自由 dict (直接写 background/decomposition/formulas 等)
    """
    id: str = Field(pattern=r"^paper_.+$")
    year: int
    competition: str
    problem_id: str = ""
    title: str
    tags: dict = Field(default_factory=dict)
    problem_ref: str = ""
    problem_context: str = ""
    methodology_chain: List[str] = Field(default_factory=list)
    key_formulas: List[Formula] = Field(default_factory=list)
    algorithm_outline: List[CodeSnippet] = Field(default_factory=list)
    assumption_analysis: List[str] = Field(default_factory=list)
    reusable_patterns: List[str] = Field(default_factory=list)
    common_pitfalls: List[Mistake] = Field(default_factory=list)
    difficulty: int = Field(ge=1, le=5, default=3)
    difficulty_level: str = "medium"
    # 三核心字段: 兼容 dict（新格式）或 嵌套对象（旧格式）
    analysis: Union[dict, PaperAnalysis] = Field(default_factory=PaperAnalysis)
    model: Union[dict, PaperModel] = Field(default_factory=PaperModel)
    evaluation: Union[dict, PaperEvaluation] = Field(default_factory=PaperEvaluation)
    # 新增：结构化经验提取
    takeaways: List[str] = Field(default_factory=list)
    source: str = ""
    quality_rating: int = Field(ge=1, le=5, default=3)


class Problem(BaseModel):
    """竞赛真题 — 原始问题描述，与论文解耦存储。

    1:N 关系：一个题目可以有多篇模范论文从不同角度求解。
    通过 (year, competition, problem_id) 自然键与 Paper 关联。
    """
    id: str = Field(pattern=r"^prob_\d+$")
    year: int
    competition: str               # 国赛 / 美赛 / 研赛
    problem_id: str                # A / B / C / D / E
    title: str                     # 题目名称
    full_text: str = ""            # 完整题目原文 (2000-5000 chars)
    background: str = ""           # 问题背景简述
    objectives: List[str] = Field(default_factory=list)   # 求解目标列表
    data_description: str = ""     # 提供的附件数据说明
    data_files: List[dict] = Field(default_factory=list)  # 附件数据文件信息
    deliverables: List[str] = Field(default_factory=list) # 需要提交的内容
    tags: dict = Field(default_factory=lambda: {
        "problem_type": [],
        "difficulty": "medium",
    })
    linked_papers: List[str] = Field(default_factory=list)  # 关联的论文 ID
    source_url: str = ""           # 来源链接


class TemplateStep(BaseModel):
    step: int
    name: str
    guiding_questions: List[str] = Field(default_factory=list)
    decision_tree: List[str] = Field(default_factory=list)
    checklist: List[str] = Field(default_factory=list)
    # 新格式兼容
    action: str = ""
    outputs: List[str] = Field(default_factory=list)


class Template(BaseModel):
    id: str = Field(pattern=r"^tpl_.+$")
    name: str
    name_en: str = ""
    description: str = ""
    category: str = ""
    applicable_to: List[str] = Field(default_factory=list)
    steps: List[TemplateStep] = Field(default_factory=list)
    applicable_methods: List[dict] = Field(default_factory=list)
    quality_rating: int = Field(ge=1, le=5, default=3)
    tags: dict = Field(default_factory=dict)
