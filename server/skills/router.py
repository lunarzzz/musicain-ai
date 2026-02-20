"""Skill 路由器 — 判断用户意图应该走 Skill（多步编排）还是 Tool（单步调用）

路由逻辑:
  1. 先用关键词匹配所有 Skill，取最高分
  2. 如果分数 > 阈值，走 Skill 流程
  3. 否则，走常规 Tool Calling 流程
"""

from __future__ import annotations

from skills.base import BaseSkill
from skills.hot_trend_creation import HotTrendCreationSkill
from skills.full_promotion import FullPromotionSkill


# ── 注册所有 Skills ──────────────────────────────────

ALL_SKILLS: list[BaseSkill] = [
    HotTrendCreationSkill(),
    FullPromotionSkill(),
]

SKILL_MAP = {s.name: s for s in ALL_SKILLS}

# ── 意图匹配阈值 ────────────────────────────────────

SKILL_THRESHOLD = 0.3


def route(user_input: str) -> BaseSkill | None:
    """判断用户输入是否应该触发某个 Skill。

    返回:
        匹配到的 Skill 实例，或 None（走 Tool Calling）
    """
    best_skill: BaseSkill | None = None
    best_score = 0.0

    for skill in ALL_SKILLS:
        score = skill.matches(user_input)
        if score > best_score:
            best_score = score
            best_skill = skill

    if best_score >= SKILL_THRESHOLD:
        return best_skill

    return None


def get_skills_description() -> str:
    """生成 Skills 描述文本，注入到 System Prompt 中让 LLM 了解可用的 Skill"""
    lines = ["## 可用的高级技能（Skills）", "当用户需要完整的多步骤方案时，可以启用以下 Skill：", ""]
    for skill in ALL_SKILLS:
        kws = "、".join(skill.trigger_keywords[:4])
        lines.append(f"- **{skill.name}**：{skill.description}（触发词：{kws}）")
    return "\n".join(lines)
