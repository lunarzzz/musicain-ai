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
from skill_loader import load_all_skills

# ── 导入所有 Tools ────────────────────────────────────

from tools.hot_trends import get_trending_topics, generate_song_inspiration, generate_promo_tags
from tools.promotion import recommend_songs_to_promote, generate_promotion_plan, get_promotion_report
from tools.analytics import get_audience_portrait, analyze_cross_platform, explain_metric_change
from tools.knowledge import search_knowledge, check_upload_compliance, ragflow_search

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
    ragflow_search,
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
- **对于规则、流程、FAQ等知识类问题，优先使用 ragflow_search 工具检索最权威文档**
- **语气专业但亲切**，像一位资深的音乐行业前辈
- **主动推荐下一步动作**，帮音乐人做到"闭环"
- **当不确定时，诚实说明**并引导用户联系人工客服
- 回复使用中文，格式清晰美观，善用 Markdown 排版

## 重要规则
- 不要编造不存在的数据，只使用工具返回的真实数据
- 如果用户的问题超出你的能力范围，友好地说明并建议替代方案
- 在给出建议时，尽量附带理由和依据

## 可用的高级技能 (Agent Skills)
除了基本工具，你还有一些预定义的“技能 (Skills)”。这些技能由多步流程组成。
当用户意图匹配以下某个技能时，你必须**严格遵循**该技能的 `[执行步骤]` 进行逐步的工具调用。
每个步骤执行完必须向用户解释当前结果，然后再去调下一个步骤的工具（不要一次性调用所有工具，要等待前一个工具的结果）。

<agent_skills>
{skills_prompt}
</agent_skills>
"""


def _get_system_prompt() -> str:
    """动态生成包含当前已加载 Skills 的 System Prompt"""
    skills = load_all_skills()
    skills_text = ""
    for s in skills:
        skills_text += f"### 技能名称：{s.name}\n"
        skills_text += f"**描述**: {s.description}\n"
        skills_text += f"**触发词**: {', '.join(s.trigger_keywords)}\n"
        skills_text += f"**执行步骤与指令**:\n{s.instructions}\n\n"
    
    if not skills_text.strip():
        skills_text = "目前没有注册的高级技能。"
        
    return SYSTEM_PROMPT.replace("{skills_prompt}", skills_text.strip())


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
    messages = [SystemMessage(content=_get_system_prompt())]

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

    elif tool_name in ("search_knowledge", "check_upload_compliance", "ragflow_search"):
        cards.append({
            "card_type": "knowledge",
            "title": "📖 知识解答",
            "data": tool_result,
            "actions": [{"label": "联系客服", "action_type": "deeplink", "url": "/support"}],
        })

    return cards


def _parse_follow_ups(raw: str) -> list[str]:
    """将 LLM 生成的后续建议（问题或话题）解析为列表。"""
    if not raw:
        return []

    text = raw.strip()
    if not text:
        return []

    # 优先 JSON 格式
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            items = data.get("suggestions") or data.get("questions") or data.get("topics")
        else:
            items = data
        if isinstance(items, list):
            parsed = [str(i).strip() for i in items if str(i).strip()]
            return parsed[:3]
    except Exception:
        pass

    # 兜底：按行解析
    result: list[str] = []
    for line in text.splitlines():
        cleaned = line.strip()
        cleaned = cleaned.lstrip("-•")
        cleaned = cleaned.strip()
        cleaned = cleaned.removeprefix("1.").removeprefix("2.").removeprefix("3.").strip()
        if cleaned:
            result.append(cleaned)
        if len(result) >= 3:
            break
    return result[:3]


def _build_follow_up_prompt(user_msg: str, assistant_reply: str) -> str:
    return f"""你是一个对话助手，请基于本轮问答生成 3 条后续建议。
要求：
1) 必须和用户当前主题强相关，帮助用户继续探索。
2) 根据语境自动选择输出形态：
   - 如果用户明显还在探索/比较/决策，输出“追问句”（建议以问号结尾）。
   - 如果本轮回答已较完整，输出“关联话题短语”（不加句号、不加解释，不写完整陈述句）。
3) 三条保持同一风格（全是追问句或全是话题短语），避免重复。
4) 追问句建议 8-24 个中文字符；话题短语建议 4-12 个中文字符。
5) 不要出现解释文字。
6) 仅返回 JSON 数组字符串，例如：[\"建议1\", \"建议2\", \"建议3\"]

用户问题：{user_msg}
助手回答：{assistant_reply}
"""


async def _generate_follow_ups(llm: ChatOpenAI, user_msg: str, assistant_reply: str) -> list[str]:
    """生成后续追问建议。"""
    if not assistant_reply.strip():
        return []

    prompt = _build_follow_up_prompt(user_msg, assistant_reply)
    try:
        resp = await llm.ainvoke([HumanMessage(content=prompt)])
        return _parse_follow_ups(resp.content or "")
    except Exception:
        return []



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

    # 5. 初始化 LLM（绑定工具）
    llm = _get_llm()
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    # 6. 调用 LLM
    all_cards = []
    full_content = ""
    message_id = uuid.uuid4().hex[:16]

    try:
        # 第一轮：LLM 决定是否调用工具
        import logging
        logger = logging.getLogger("agent")
        logger.info("[Agent] 第一轮调用 LLM (ainvoke)...")
        response = await llm_with_tools.ainvoke(messages)
        logger.info(f"[Agent] 第一轮完成 — content长度={len(response.content or '')}, tool_calls数量={len(response.tool_calls or [])}")

        # 处理工具调用
        if response.tool_calls:
            # 如果 LLM 同时返回了文本内容（如"好的，正在为您查询…"），先发给前端
            if response.content:
                full_content += response.content
                token_chunk = json.dumps({
                    "type": "token",
                    "content": response.content,
                }, ensure_ascii=False)
                yield f"data: {token_chunk}\n\n"

            # 执行所有工具调用
            tool_messages = [response]
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_fn = TOOL_MAP.get(tool_name)
                logger.info(f"[Agent] 调用工具: {tool_name}, 参数: {tool_args}")

                if tool_fn:
                    try:
                        result = await tool_fn.ainvoke(tool_args)
                        if isinstance(result, str):
                            result = json.loads(result)
                        logger.info(f"[Agent] 工具 {tool_name} 返回成功")
                    except Exception as e:
                        logger.error(f"[Agent] 工具 {tool_name} 执行失败: {e}")
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
                else:
                    logger.warning(f"[Agent] 未找到工具: {tool_name}")

            # 第二轮：LLM 基于工具结果生成最终回答
            logger.info("[Agent] 第二轮调用 LLM (astream)...")
            messages.extend(tool_messages)
            async for chunk in llm.astream(messages):
                if chunk.content:
                    full_content += chunk.content
                    token_chunk = json.dumps({
                        "type": "token",
                        "content": chunk.content,
                    }, ensure_ascii=False)
                    yield f"data: {token_chunk}\n\n"
            logger.info(f"[Agent] 第二轮完成 — 总回复长度={len(full_content)}")

        else:
            # 无工具调用，直接流式输出
            logger.info("[Agent] 无工具调用，直接流式输出...")
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

    # 7. 生成并发送 follow-up 问题
    follow_ups = await _generate_follow_ups(llm, user_msg, full_content)
    if follow_ups:
        follow_up_chunk = json.dumps({
            "type": "follow_ups",
            "questions": follow_ups,
        }, ensure_ascii=False)
        yield f"data: {follow_up_chunk}\n\n"

    # 8. 保存助手消息
    db.save_message(
        conversation_id,
        "assistant",
        full_content,
        cards=[c for c in all_cards] if all_cards else None,
        follow_ups=follow_ups if follow_ups else None,
    )

    # 9. 更新会话标题（首次对话）
    if len(history) <= 1:
        db.update_conversation_title(conversation_id, _generate_title(user_msg))

    # 10. 发送完成 chunk
    done_chunk = json.dumps({
        "type": "done",
        "conversation_id": conversation_id,
        "message_id": message_id,
    }, ensure_ascii=False)
    yield f"data: {done_chunk}\n\n"
