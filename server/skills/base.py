"""Skill 基类 — 定义多步骤工作流的基础抽象

Tool  = 原子操作（一个函数调用）
Skill = 多步编排（组合 N 个 Tool + 中间推理，产出结构化结果）

每个 Skill 定义:
  - name / description（LLM 用来判断是否触发）
  - steps: 有序的执行步骤
  - execute(): 按步骤编排 Tools，产出最终结果
"""

from __future__ import annotations

import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator

from langchain_core.tools import BaseTool


@dataclass
class SkillStep:
    """Skill 中的一个执行步骤"""
    name: str                          # 步骤名称
    description: str                   # 步骤描述（展示给用户）
    tool_name: str | None = None       # 要调用的 Tool（None 表示纯 LLM 推理步骤）
    tool_args: dict = field(default_factory=dict)        # 固定参数
    dynamic_args: dict = field(default_factory=dict)     # 动态参数（从上下文/前序结果中取值）
    output_key: str = ""               # 结果存入上下文的 key


@dataclass
class SkillResult:
    """Skill 执行结果"""
    skill_name: str
    success: bool
    steps_completed: list[dict] = field(default_factory=list)
    final_output: dict = field(default_factory=dict)
    cards: list[dict] = field(default_factory=list)
    summary: str = ""
    error: str | None = None


class BaseSkill(ABC):
    """Skill 基类"""

    name: str = ""
    description: str = ""
    trigger_keywords: list[str] = []   # 辅助意图识别的关键词

    @abstractmethod
    def get_steps(self, user_input: str, context: dict) -> list[SkillStep]:
        """根据用户输入和上下文，返回要执行的步骤列表"""
        ...

    @abstractmethod
    async def execute(
        self,
        user_input: str,
        context: dict,
        tool_map: dict[str, BaseTool],
    ) -> AsyncGenerator[dict, None]:
        """执行 Skill，逐步 yield 进度和结果。

        每次 yield 一个 dict，格式：
        - {"type": "step_start", "step": "步骤名", "description": "描述"}
        - {"type": "step_result", "step": "步骤名", "data": {...}}
        - {"type": "card", "card": {...}}
        - {"type": "token", "content": "文本内容"}
        - {"type": "done", "summary": "总结"}
        """
        ...

    def matches(self, user_input: str) -> float:
        """判断用户输入是否匹配此 Skill，返回 0~1 的置信度"""
        input_lower = user_input.lower()
        score = 0.0
        for kw in self.trigger_keywords:
            if kw in input_lower:
                score += 0.3
        return min(score, 1.0)
