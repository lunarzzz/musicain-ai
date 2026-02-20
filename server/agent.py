"""Agent 编排核心 — 意图识别 → 工具调用 → 结果合成 → 响应组装

采用 LangChain 的 create_tool_calling_agent，配合 Function Calling
实现多步推理与工具调度。
"""

from __future__ import annotations

import json
import uuid
from typing import AsyncGenerator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from config import settings
from models import CardData, CardType, Evidence, StreamChunk
import database as db
from skills.router import route as route_skill, get_skills_description

# ── 导入所有 Tools ────────────────────────────────────

from tools.hot_trends import get_trending_topics, generate_song_inspiration, generate_promo_tags
from tools.promotion import recommend_songs_to_promote, generate_promotion_plan, get_promotion_report
from tools.analytics import get_audience_portrait, analyze_cross_platform, explain_metric_change
from tools.knowledge import search_knowledge, check_upload_compliance

ALL_TOOLS = [
    get_trending_topics,
    generate_song_inspiration,
    generate_promo_tags,
    recommend_songs_to_promote,
    generate_promotion_plan,
    get_promotion_report,
    get_audience_portrait,
    analyze_cross_platform,
    explain_metric_change,
    search_knowledge,
    check_upload_compliance,
]

TOOL_MAP = {t.name: t for t in ALL_TOOLS}

# ── System Prompt ─────────────────────────────────────

SYSTEM_PROMPT = """你是「腾讯音乐人 AI 助手」，一个专业的音乐人工作流 Copilot。

## 你的能力
你可以通过调用工具来帮助音乐人完成以下任务：
1. **热点创作**：获取热点趋势、生成歌名灵感、生成宣推标签
2. **宣推建议**：推荐最值得宣推的歌曲、生成投放计划、投后复盘
3. **智能分析**：听众画像、跨平台表现分析、关键指标变化归因
4. **问答指南**：回答入驻、上传、审核、结算、版权、活动等问题

## 行为准则
- **始终提供可执行的建议**，不要只给笼统的方向
- **引用数据时标注来源和口径**，确保可信度
- **语气专业但亲切**，像一位资深的音乐行业前辈
- **主动推荐下一步动作**，帮音乐人做到"闭环"
- **当不确定时，诚实说明**并引导用户联系人工客服
- 回复使用中文，格式清晰美观，善用 Markdown 排版

## 重要规则
- 不要编造不存在的数据，只使用工具返回的真实数据
- 如果用户的问题超出你的能力范围，友好地说明并建议替代方案
- 在给出建议时，尽量附带理由和依据

""" + "\n\n" + get_skills_description()


# ── Agent 核心 ─────────────────────────────────────────

def _get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        model=settings.LLM_MODEL,
        temperature=settings.LLM_TEMPERATURE,
        streaming=True,
    )


def _build_messages(history: list[dict], user_msg: str) -> list:
    """构建 LangChain 消息列表"""
    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    for msg in history[-20:]:  # 保留最近 20 条历史
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))

    messages.append(HumanMessage(content=user_msg))
    return messages


def _generate_title(user_msg: str) -> str:
    """从首条消息生成会话标题"""
    title = user_msg.strip()[:30]
    if len(user_msg) > 30:
        title += "..."
    return title


def _extract_cards(tool_name: str, tool_result: dict) -> list[dict]:
    """从工具调用结果提取可展示的卡片数据"""
    cards = []

    if tool_name == "get_trending_topics":
        topics = tool_result.get("topics", [])
        cards.append({
            "card_type": "hot_trend",
            "title": "🔥 热点趋势",
            "data": {"topics": topics, "updated_at": tool_result.get("updated_at")},
            "actions": [{"label": "基于热点生成灵感", "action_type": "callback", "payload": {"action": "generate_inspiration"}}],
        })

    elif tool_name == "generate_song_inspiration":
        cards.append({
            "card_type": "hot_trend",
            "title": "💡 创作灵感",
            "data": tool_result,
            "actions": [{"label": "生成宣推标签", "action_type": "callback", "payload": {"action": "generate_tags"}}],
        })

    elif tool_name in ("recommend_songs_to_promote",):
        recs = tool_result.get("recommendations", [])
        cards.append({
            "card_type": "song_recommend",
            "title": "🎵 推歌建议",
            "data": {"recommendations": recs, "diagnosis": tool_result.get("diagnosis")},
            "actions": [{"label": "生成投放计划", "action_type": "callback", "payload": {"action": "create_plan"}}],
        })

    elif tool_name == "generate_promotion_plan":
        cards.append({
            "card_type": "promotion_plan",
            "title": "📋 投放计划",
            "data": tool_result,
            "actions": [{"label": "开始投放", "action_type": "deeplink", "url": "/promotion/create"}],
        })

    elif tool_name == "get_promotion_report":
        cards.append({
            "card_type": "data_report",
            "title": "📊 宣推复盘报告",
            "data": tool_result,
            "actions": [{"label": "追加投放", "action_type": "deeplink", "url": "/promotion/create"}],
        })

    elif tool_name == "get_audience_portrait":
        cards.append({
            "card_type": "audience_portrait",
            "title": "👥 听众画像",
            "data": tool_result,
            "actions": [],
        })

    elif tool_name == "analyze_cross_platform":
        cards.append({
            "card_type": "data_report",
            "title": "📈 跨平台分析",
            "data": tool_result,
            "actions": [],
        })

    elif tool_name == "explain_metric_change":
        cards.append({
            "card_type": "data_report",
            "title": "📉 指标变化分析",
            "data": tool_result,
            "actions": [],
        })

    elif tool_name in ("search_knowledge", "check_upload_compliance"):
        cards.append({
            "card_type": "knowledge",
            "title": "📖 知识解答",
            "data": tool_result,
            "actions": [{"label": "联系客服", "action_type": "deeplink", "url": "/support"}],
        })

    return cards


async def chat(user_msg: str, conversation_id: str | None = None) -> AsyncGenerator[str, None]:
    """处理用户消息，流式返回响应。

    产出 Server-Sent Events (SSE) 格式的 JSON chunks。
    """
    # 1. 创建或获取会话
    if not conversation_id or not db.get_conversation(conversation_id):
        conversation_id = db.create_conversation(_generate_title(user_msg))

    # 2. 保存用户消息
    db.save_message(conversation_id, "user", user_msg)

    # 3. 加载历史
    history = db.get_messages(conversation_id, limit=20)

    # 4. 构建消息
    messages = _build_messages(history[:-1], user_msg)  # 排除刚存的用户消息

    # 5. Skill 路由：判断是否走多步编排
    matched_skill = route_skill(user_msg)

    all_cards = []
    full_content = ""
    message_id = uuid.uuid4().hex[:16]

    if matched_skill:
        # ── Skill 模式：多步工作流 ──
        try:
            async for chunk in matched_skill.execute(user_msg, {}, TOOL_MAP):
                chunk_type = chunk.get("type")

                if chunk_type == "step_start":
                    step_chunk = json.dumps({
                        "type": "token",
                        "content": f"\n{chunk['description']}\n",
                    }, ensure_ascii=False)
                    full_content += f"\n{chunk['description']}\n"
                    yield f"data: {step_chunk}\n\n"

                elif chunk_type == "card":
                    all_cards.append(chunk["card"])
                    card_chunk = json.dumps({
                        "type": "card",
                        "card": chunk["card"],
                    }, ensure_ascii=False)
                    yield f"data: {card_chunk}\n\n"

                elif chunk_type == "token":
                    full_content += chunk.get("content", "")
                    token_chunk = json.dumps({
                        "type": "token",
                        "content": chunk["content"],
                    }, ensure_ascii=False)
                    yield f"data: {token_chunk}\n\n"

                elif chunk_type == "done":
                    pass  # 下面统一处理

        except Exception as e:
            error_msg = f"技能执行出错：{str(e)}"
            full_content = error_msg
            error_chunk = json.dumps({"type": "error", "content": error_msg}, ensure_ascii=False)
            yield f"data: {error_chunk}\n\n"

    else:
        # ── Tool 模式：单步 Function Calling ──
        llm = _get_llm()
        llm_with_tools = llm.bind_tools(ALL_TOOLS)

        try:
            # 第一轮：LLM 决定是否调用工具
            response = await llm_with_tools.ainvoke(messages)

            # 处理工具调用
            if response.tool_calls:
                # 执行所有工具调用
                tool_messages = [response]
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    tool_fn = TOOL_MAP.get(tool_name)

                    if tool_fn:
                        try:
                            result = await tool_fn.ainvoke(tool_args)
                            if isinstance(result, str):
                                result = json.loads(result)
                        except Exception as e:
                            result = {"error": str(e)}

                        # 提取卡片
                        cards = _extract_cards(tool_name, result)
                        all_cards.extend(cards)

                        # 发送卡片 chunk
                        for card in cards:
                            card_chunk = json.dumps({
                                "type": "card",
                                "card": card,
                            }, ensure_ascii=False)
                            yield f"data: {card_chunk}\n\n"

                        # 构建工具响应消息
                        from langchain_core.messages import ToolMessage
                        tool_messages.append(
                            ToolMessage(
                                content=json.dumps(result, ensure_ascii=False),
                                tool_call_id=tool_call["id"],
                            )
                        )

                # 第二轮：LLM 基于工具结果生成最终回答
                messages.extend(tool_messages)
                async for chunk in llm.astream(messages):
                    if chunk.content:
                        full_content += chunk.content
                        token_chunk = json.dumps({
                            "type": "token",
                            "content": chunk.content,
                        }, ensure_ascii=False)
                        yield f"data: {token_chunk}\n\n"

            else:
                # 无工具调用，直接流式输出
                async for chunk in llm_with_tools.astream(messages):
                    if chunk.content:
                        full_content += chunk.content
                        token_chunk = json.dumps({
                            "type": "token",
                            "content": chunk.content,
                        }, ensure_ascii=False)
                        yield f"data: {token_chunk}\n\n"

        except Exception as e:
            error_msg = f"抱歉，处理您的请求时遇到了问题：{str(e)}"
            full_content = error_msg
            error_chunk = json.dumps({
                "type": "error",
                "content": error_msg,
            }, ensure_ascii=False)
            yield f"data: {error_chunk}\n\n"

    # 7. 保存助手消息
    db.save_message(
        conversation_id,
        "assistant",
        full_content,
        cards=[c for c in all_cards] if all_cards else None,
    )

    # 8. 更新会话标题（首次对话）
    if len(history) <= 1:
        db.update_conversation_title(conversation_id, _generate_title(user_msg))

    # 9. 发送完成 chunk
    done_chunk = json.dumps({
        "type": "done",
        "conversation_id": conversation_id,
        "message_id": message_id,
    }, ensure_ascii=False)
    yield f"data: {done_chunk}\n\n"
