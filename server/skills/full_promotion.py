"""全链路宣推 Skill

工作流：分析听众画像 → 推荐宣推歌曲 → 生成投放计划
一站式帮音乐人从数据洞察到可执行的宣推策略。
"""

from __future__ import annotations

import json
from typing import AsyncGenerator

from langchain_core.tools import BaseTool

from skills.base import BaseSkill, SkillStep


class FullPromotionSkill(BaseSkill):
    name = "full_promotion"
    description = "从听众分析到宣推策略的全链路方案：分析听众画像 → 推荐最值得推的歌 → 生成投放计划"
    trigger_keywords = ["全链路", "完整宣推", "帮我做推广", "一套宣推", "全流程推广", "系统推广"]

    def get_steps(self, user_input: str, context: dict) -> list[SkillStep]:
        budget = context.get("budget", 1000.0)
        return [
            SkillStep(
                name="audience_analysis",
                description="👥 正在分析你的听众画像...",
                tool_name="get_audience_portrait",
                tool_args={},
                output_key="portrait",
            ),
            SkillStep(
                name="song_recommend",
                description="🎵 基于数据推荐最值得推广的歌曲...",
                tool_name="recommend_songs_to_promote",
                tool_args={"budget": budget, "goal": "播放量增长"},
                output_key="recommendations",
            ),
            SkillStep(
                name="create_plan",
                description="📋 生成定制投放计划...",
                tool_name="generate_promotion_plan",
                tool_args={"budget": budget},
                dynamic_args={
                    "song_name": (
                        "recommendations",
                        lambda r: r.get("recommendations", [{}])[0]
                            .get("song", {}).get("name", "海边的风"),
                    ),
                },
                output_key="plan",
            ),
        ]

    async def execute(
        self,
        user_input: str,
        context: dict,
        tool_map: dict[str, BaseTool],
    ) -> AsyncGenerator[dict, None]:
        steps = self.get_steps(user_input, context)
        results: dict[str, dict] = {}

        for step in steps:
            yield {
                "type": "step_start",
                "step": step.name,
                "description": step.description,
            }

            if step.tool_name and step.tool_name in tool_map:
                args = {**step.tool_args}
                for arg_name, (source_key, extractor) in step.dynamic_args.items():
                    if source_key in results:
                        args[arg_name] = extractor(results[source_key])

                tool_fn = tool_map[step.tool_name]
                try:
                    result = await tool_fn.ainvoke(args)
                    if isinstance(result, str):
                        result = json.loads(result)
                except Exception as e:
                    result = {"error": str(e)}

                results[step.output_key] = result

                yield {
                    "type": "step_result",
                    "step": step.name,
                    "data": result,
                }

        # 组装卡片
        if "portrait" in results:
            yield {
                "type": "card",
                "card": {
                    "card_type": "audience_portrait",
                    "title": "👥 听众画像",
                    "data": results["portrait"],
                    "actions": [],
                },
            }

        if "recommendations" in results:
            yield {
                "type": "card",
                "card": {
                    "card_type": "song_recommend",
                    "title": "🎵 推歌建议",
                    "data": results["recommendations"],
                    "actions": [],
                },
            }

        if "plan" in results:
            yield {
                "type": "card",
                "card": {
                    "card_type": "promotion_plan",
                    "title": "📋 投放计划",
                    "data": results["plan"],
                    "actions": [{"label": "开始投放", "action_type": "deeplink", "url": "/promotion/create"}],
                },
            }

        # 总结
        recs = results.get("recommendations", {}).get("recommendations", [])
        top_song = recs[0]["song"]["name"] if recs else "你的歌曲"

        summary = f"✅ **全链路宣推方案已就绪！**\n\n"
        summary += f"基于你的听众画像分析，我推荐重点推广 **《{top_song}》**：\n"
        summary += f"- 👥 听众画像已分析，核心受众定位清晰\n"
        summary += f"- 🎵 从 {len(recs)} 首候选中选出最优推广歌曲\n"
        summary += f"- 📋 投放计划已生成，包含渠道分配和执行节奏\n\n"
        summary += "确认方案后可直接开始投放，投放结束后我可以帮你做复盘分析。"

        yield {"type": "token", "content": summary}
        yield {"type": "done", "summary": summary}
