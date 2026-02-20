"""Pydantic 数据模型 — 请求 / 响应 / 卡片 / 证据链"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── 枚举 ──────────────────────────────────────────────

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class CardType(str, Enum):
    HOT_TREND = "hot_trend"
    SONG_RECOMMEND = "song_recommend"
    PROMOTION_PLAN = "promotion_plan"
    DATA_REPORT = "data_report"
    AUDIENCE_PORTRAIT = "audience_portrait"
    KNOWLEDGE = "knowledge"
    QUICK_ACTIONS = "quick_actions"


# ── 请求 ──────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: str | None = None


# ── 卡片 ──────────────────────────────────────────────

class CardData(BaseModel):
    card_type: CardType
    title: str
    data: dict[str, Any] = {}
    actions: list[CardAction] = []


class CardAction(BaseModel):
    label: str
    action_type: str = "link"  # link / callback / deeplink
    url: str | None = None
    payload: dict[str, Any] | None = None


# ── 证据链 ────────────────────────────────────────────

class Evidence(BaseModel):
    source: str  # 数据来源
    metric: str | None = None  # 指标名
    value: str | None = None  # 指标值
    description: str | None = None


# ── 响应 ──────────────────────────────────────────────

class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    content: str
    cards: list[CardData] = []
    evidence: list[Evidence] = []
    created_at: datetime = Field(default_factory=datetime.now)


class StreamChunk(BaseModel):
    """SSE 流式响应 chunk"""
    type: str  # "token" | "card" | "evidence" | "done" | "error"
    content: str | None = None
    card: CardData | None = None
    evidence: list[Evidence] | None = None
    conversation_id: str | None = None
    message_id: str | None = None


# ── 会话 ──────────────────────────────────────────────

class ConversationSummary(BaseModel):
    id: str
    title: str
    updated_at: datetime
    message_count: int = 0
