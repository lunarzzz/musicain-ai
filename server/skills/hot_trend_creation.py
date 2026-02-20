"""热点创作一条龙 Skill

工作流：获取热点 → 生成创作灵感 → 生成宣推标签
一次性帮音乐人从热点到可执行的创作/宣推方案。
"""

from __future__ import annotations

import json
from typing import AsyncGenerator

from langchain_core.tools import BaseTool

from skills.base import BaseSkill, SkillStep


class HotTrendCreationSkill(BaseSkill):
    name = "hot_trend_creation"
    description = "从热点趋势出发，一站式完成灵感生成和宣推标签，帮你从热点到创作方案闭环"
    trigger_keywords = ["一条龙", "完整创作", "从热点到创作", "帮我写歌", "一整套", "全流程创作"]

    def get_steps(self, user_input: str, context: dict) -> list[SkillStep]:
        # 从用户输入中提取风格偏好
        style = context.get("style", "流行")
        return [
            SkillStep(
                name="fetch_trends",
                description="📡 正在获取最新热点趋势...",
                tool_name="get_trending_topics",
                tool_args={"platform": "all", "limit": 5},
                output_key="trends",
            ),
            SkillStep(
                name="generate_inspiration",
                description="💡 基于热点生成创作灵感...",
                tool_name="generate_song_inspiration",
                tool_args={"style": style},
                dynamic_args={"topic": ("trends", lambda r: r.get("topics", [{}])[0].get("title", ""))},
                output_key="inspiration",
            ),
            SkillStep(
                name="generate_tags",
                description="🏷️ 生成宣推标签和话题...",
                tool_name="generate_promo_tags",
                dynamic_args={"topic": ("trends", lambda r: r.get("topics", [{}])[0].get("title", ""))},
                output_key="tags",
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
            # 通知前端：步骤开始
            yield {
                "type": "step_start",
                "step": step.name,
                "description": step.description,
            }

            if step.tool_name and step.tool_name in tool_map:
                # 构建参数
                args = {**step.tool_args}
                for arg_name, (source_key, extractor) in step.dynamic_args.items():
                    if source_key in results:
                        args[arg_name] = extractor(results[source_key])

                # 调用 Tool
                tool_fn = tool_map[step.tool_name]
                try:
                    result = await tool_fn.ainvoke(args)
                    if isinstance(result, str):
                        result = json.loads(result)
                except Exception as e:
                    result = {"error": str(e)}

                results[step.output_key] = result

                # 通知前端：步骤完成 + 数据
                yield {
                    "type": "step_result",
                    "step": step.name,
                    "data": result,
                }

        # 组装卡片
        if "trends" in results:
            yield {
                "type": "card",
                "card": {
                    "card_type": "hot_trend",
                    "title": "🔥 热点趋势",
                    "data": results["trends"],
                    "actions": [],
                },
            }

        if "inspiration" in results:
            yield {
                "type": "card",
                "card": {
                    "card_type": "hot_trend",
                    "title": "💡 创作灵感",
                    "data": results["inspiration"],
                    "actions": [],
                },
            }

        if "tags" in results:
            yield {
                "type": "card",
                "card": {
                    "card_type": "hot_trend",
                    "title": "🏷️ 宣推标签",
                    "data": results["tags"],
                    "actions": [],
                },
            }

        # 总结
        topics = results.get("trends", {}).get("topics", [])
        top_topic = topics[0]["title"] if topics else "当前热点"
        song_names = results.get("inspiration", {}).get("song_names", [])

        summary = f"✅ **创作方案已生成！**\n\n"
        summary += f"基于热点 **「{top_topic}」**，我为你准备了：\n"
        summary += f"- 🎵 {len(song_names)} 个歌名灵感\n"
        summary += f"- 🎤 Hook 创意和歌曲结构建议\n"
        summary += f"- 🏷️ 平台专属宣推标签\n\n"
        summary += "你可以基于以上方案开始创作，完成后我可以帮你做上传预检和宣推计划。"

        yield {"type": "token", "content": summary}
        yield {"type": "done", "summary": summary}
