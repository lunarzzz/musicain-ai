"""FastAPI 入口 — 注册路由、CORS、SSE 流式接口"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from config import settings
import database as db
from agent import chat

# ── App ───────────────────────────────────────────────

app = FastAPI(
    title="音乐人 AI 助手",
    description="腾讯音乐人 AI 助手 MVP — 工作流 Copilot",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 生命周期 ──────────────────────────────────────────

@app.on_event("startup")
async def startup():
    db.init_db()


# ── 请求模型 ──────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


# ── 路由：对话 ─────────────────────────────────────────

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """流式对话接口 (SSE)"""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")

    return StreamingResponse(
        chat(req.message, req.conversation_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── 路由：会话管理 ─────────────────────────────────────

@app.get("/api/conversations")
async def list_conversations():
    """获取会话列表"""
    return db.list_conversations()


@app.get("/api/conversations/{conv_id}")
async def get_conversation(conv_id: str):
    """获取会话详情"""
    conv = db.get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    return conv


@app.get("/api/conversations/{conv_id}/messages")
async def get_messages(conv_id: str):
    """获取会话消息列表"""
    conv = db.get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    return db.get_messages(conv_id)


@app.delete("/api/conversations/{conv_id}")
async def delete_conversation(conv_id: str):
    """删除会话"""
    conv = db.get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    db.delete_conversation(conv_id)
    return {"status": "ok"}


# ── 路由：系统 ─────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/quick-actions")
async def quick_actions():
    """获取首页快捷操作"""
    return [
        {"id": "trends", "icon": "🔥", "label": "热点趋势", "prompt": "最近有什么热点可以用来创作？"},
        {"id": "promote", "icon": "🚀", "label": "推歌建议", "prompt": "帮我分析一下我该推哪首歌"},
        {"id": "portrait", "icon": "👥", "label": "听众画像", "prompt": "帮我看看我的听众画像"},
        {"id": "data", "icon": "📊", "label": "数据分析", "prompt": "最近播放量有什么变化？"},
        {"id": "creation_flow", "icon": "✨", "label": "全流程创作", "prompt": "帮我从热点到创作一条龙完成"},
        {"id": "promo_flow", "icon": "📋", "label": "全链路宣推", "prompt": "帮我做一套完整宣推方案"},
    ]


@app.get("/api/skills")
async def list_skills():
    """获取可用的 Skills 列表"""
    from skill_loader import load_all_skills
    skills = load_all_skills()
    return [
        {
            "name": s.name,
            "description": s.description,
            "trigger_keywords": s.trigger_keywords,
        }
        for s in skills
    ]


# ── 启动 ──────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
