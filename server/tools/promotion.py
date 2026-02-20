"""宣推建议服务 — 推歌建议、投放计划、投后复盘

MVP 阶段使用 Mock 数据模拟宣推系统。
"""

from __future__ import annotations

import random
from langchain_core.tools import tool

# ── Mock 数据 ─────────────────────────────────────────

_MOCK_SONGS = [
    {
        "id": "s001",
        "name": "月光信箱",
        "release_date": "2026-01-15",
        "play_count": 128000,
        "completion_rate": 0.72,
        "replay_rate": 0.35,
        "collection_rate": 0.08,
        "search_play_rate": 0.12,
        "leverage_ratio": 3.2,
        "stage": "潜力期",
        "trend": "上升",
    },
    {
        "id": "s002",
        "name": "城市候鸟",
        "release_date": "2025-11-20",
        "play_count": 356000,
        "completion_rate": 0.65,
        "replay_rate": 0.22,
        "collection_rate": 0.05,
        "search_play_rate": 0.08,
        "leverage_ratio": 1.8,
        "stage": "成熟期",
        "trend": "平稳",
    },
    {
        "id": "s003",
        "name": "海边的风",
        "release_date": "2026-02-01",
        "play_count": 45000,
        "completion_rate": 0.78,
        "replay_rate": 0.42,
        "collection_rate": 0.11,
        "search_play_rate": 0.15,
        "leverage_ratio": 5.1,
        "stage": "冷启动",
        "trend": "飙升",
    },
    {
        "id": "s004",
        "name": "褪色的照片",
        "release_date": "2025-08-10",
        "play_count": 890000,
        "completion_rate": 0.58,
        "replay_rate": 0.18,
        "collection_rate": 0.04,
        "search_play_rate": 0.06,
        "leverage_ratio": 1.2,
        "stage": "衰退期",
        "trend": "下降",
    },
    {
        "id": "s005",
        "name": "凌晨三点半",
        "release_date": "2026-02-10",
        "play_count": 22000,
        "completion_rate": 0.81,
        "replay_rate": 0.48,
        "collection_rate": 0.13,
        "search_play_rate": 0.18,
        "leverage_ratio": 6.8,
        "stage": "冷启动",
        "trend": "飙升",
    },
]


@tool
def recommend_songs_to_promote(budget: float = 1000.0, goal: str = "播放量增长") -> dict:
    """基于歌曲数据指标推荐最值得宣推的歌曲，并给出可解释的理由。

    参数:
        budget: 可用宣推预算（元）
        goal: 宣推目标，可选 '播放量增长' / '涨粉' / '上榜' / '收入提升'
    """
    # 按杠杆率排序（投入产出比最高的优先）
    ranked = sorted(_MOCK_SONGS, key=lambda s: s["leverage_ratio"], reverse=True)
    top3 = ranked[:3]

    recommendations = []
    for i, song in enumerate(top3):
        reasons = []
        if song["completion_rate"] >= 0.75:
            reasons.append(f"完播率 {song['completion_rate']:.0%}，高于平均水平")
        if song["replay_rate"] >= 0.35:
            reasons.append(f"复播率 {song['replay_rate']:.0%}，用户粘性强")
        if song["search_play_rate"] >= 0.10:
            reasons.append(f"搜播率 {song['search_play_rate']:.0%}，自来水效应明显")
        if song["leverage_ratio"] >= 3.0:
            reasons.append(f"杠杆率 {song['leverage_ratio']:.1f}x，投入产出比高")
        if song["trend"] == "飙升":
            reasons.append("当前处于飙升趋势，适合趁势追投")

        recommendations.append({
            "rank": i + 1,
            "song": song,
            "reasons": reasons or ["综合指标表现良好"],
            "suggested_budget": round(budget * [0.5, 0.3, 0.2][i], 0),
        })

    return {
        "goal": goal,
        "total_budget": budget,
        "recommendations": recommendations,
        "diagnosis": f"在你的 {len(_MOCK_SONGS)} 首歌中，有 "
                     f"{sum(1 for s in _MOCK_SONGS if s['leverage_ratio'] >= 3.0)} 首歌的杠杆率 ≥ 3.0，"
                     f"建议优先投放这些高潜力歌曲",
    }


@tool
def generate_promotion_plan(
    song_name: str,
    budget: float = 500.0,
    target: str = "播放量增长",
    duration_days: int = 7,
) -> dict:
    """为指定歌曲生成详细的投放计划。

    参数:
        song_name: 歌曲名称
        budget: 投放预算（元）
        target: 投放目标
        duration_days: 投放周期（天）
    """
    daily_budget = round(budget / duration_days, 0)

    return {
        "song_name": song_name,
        "plan": {
            "total_budget": budget,
            "duration": f"{duration_days} 天",
            "daily_budget": daily_budget,
            "targeting": {
                "age": "18-30 岁",
                "gender": "不限",
                "interest": ["音乐", "情感", "生活记录"],
                "region": "一二线城市优先，逐步放开",
            },
            "channel_allocation": {
                "站内推荐": f"{budget * 0.4:.0f} 元 (40%)",
                "短视频投放": f"{budget * 0.35:.0f} 元 (35%)",
                "搜索优化": f"{budget * 0.15:.0f} 元 (15%)",
                "社交传播": f"{budget * 0.1:.0f} 元 (10%)",
            },
            "timeline": [
                {"phase": "预热期 (Day 1-2)", "action": "发布预告短视频，积累初始互动"},
                {"phase": "冲量期 (Day 3-5)", "action": "加大投放力度，冲击推荐池"},
                {"phase": "收尾期 (Day 6-7)", "action": "降低出价，优化 ROI，沉淀长尾"},
            ],
        },
        "expected_results": {
            "estimated_plays": f"{int(budget * random.uniform(80, 150)):,}",
            "estimated_new_fans": f"{int(budget * random.uniform(0.5, 2)):,}",
            "estimated_collections": f"{int(budget * random.uniform(3, 8)):,}",
        },
        "tips": "建议在投放第 3 天检查完播率，若低于 60% 可考虑更换投放素材",
    }


@tool
def get_promotion_report(song_name: str = "月光信箱") -> dict:
    """获取歌曲宣推效果复盘报告。

    参数:
        song_name: 歌曲名称
    """
    return {
        "song_name": song_name,
        "period": "2026-02-01 ~ 2026-02-14",
        "summary": {
            "total_spend": "¥1,200",
            "total_plays": "186,500",
            "new_fans": "1,230",
            "collections": "5,680",
            "roi": "155.4 播放/元",
        },
        "daily_trend": [
            {"day": f"02-{d:02d}", "plays": random.randint(8000, 25000), "spend": random.randint(60, 120)}
            for d in range(1, 15)
        ],
        "audience_insight": {
            "top_age": "22-28 岁 (占比 45%)",
            "top_region": "广东、浙江、北京",
            "top_source": "推荐页 (62%) > 搜索 (18%) > 分享 (12%)",
        },
        "next_steps": [
            "杠杆率 5.1x，超出均值，建议追加 ¥500 预算延续热度",
            "搜播率持续上升，可投放搜索关键词广告",
            "收藏率 11% 较高，适合引导粉丝关注",
        ],
    }
