"""热点创作服务 — 获取热点、生成灵感、生成宣推标签

MVP 阶段使用 Mock 数据，后续替换为真实热榜 API。
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from langchain_core.tools import tool

# ── Mock 数据 ─────────────────────────────────────────

_PLATFORMS = ["抖音", "快手", "B站", "微博", "小红书"]

_TRENDING_TOPICS = [
    {
        "id": "t001",
        "title": "春天的第一缕阳光",
        "platform": "抖音",
        "heat_score": 9800,
        "category": "情感",
        "trend": "rising",
        "related_tags": ["春日絮语", "治愈系", "暖阳"],
        "music_angle": "适合创作温暖治愈风格的轻民谣，副歌可以用'阳光'意象",
    },
    {
        "id": "t002",
        "title": "深夜emo文学",
        "platform": "小红书",
        "heat_score": 8500,
        "category": "情感",
        "trend": "stable",
        "related_tags": ["深夜情感", "emo", "失眠"],
        "music_angle": "适合创作慢节奏 R&B 或 Lo-fi，带独白式歌词",
    },
    {
        "id": "t003",
        "title": "打工人的早八战歌",
        "platform": "B站",
        "heat_score": 7600,
        "category": "搞笑/生活",
        "trend": "rising",
        "related_tags": ["打工人", "上班", "早八"],
        "music_angle": "适合创作节奏感强的电子/说唱，歌词可以走幽默路线",
    },
    {
        "id": "t004",
        "title": "一个人的旅行",
        "platform": "抖音",
        "heat_score": 9200,
        "category": "旅行",
        "trend": "rising",
        "related_tags": ["独旅", "说走就走", "风景"],
        "music_angle": "适合创作清新吉他民谣或 Indie Pop，旋律明亮自由",
    },
    {
        "id": "t005",
        "title": "国风新潮",
        "platform": "快手",
        "heat_score": 8800,
        "category": "国风",
        "trend": "hot",
        "related_tags": ["国风", "古典", "新中式"],
        "music_angle": "适合融合古风与电子/嘻哈元素，加入传统乐器采样",
    },
    {
        "id": "t006",
        "title": "暗恋的100种表达",
        "platform": "微博",
        "heat_score": 7200,
        "category": "情感",
        "trend": "stable",
        "related_tags": ["暗恋", "青春", "心动"],
        "music_angle": "适合创作甜系 Pop 或轻快 R&B，副歌突出心跳加速感",
    },
]

_SONG_NAME_IDEAS = [
    "《{keyword}的温度》", "《给{keyword}的信》", "《最后一个{keyword}》",
    "《{keyword}碎片》", "《如果{keyword}会说话》", "《{keyword}博物馆》",
    "《偷走{keyword}》", "《{keyword}陷阱》", "《{keyword}的另一面》",
    "《和{keyword}说再见》",
]


# ── Tools ─────────────────────────────────────────────

@tool
def get_trending_topics(platform: str = "all", category: str = "all", limit: int = 5) -> dict:
    """获取当前热门话题和趋势。

    参数:
        platform: 平台筛选，可选 '抖音' / '快手' / 'B站' / '微博' / '小红书' / 'all'
        category: 类别筛选，可选 '情感' / '搞笑/生活' / '旅行' / '国风' / 'all'
        limit: 返回数量上限
    """
    topics = list(_TRENDING_TOPICS)
    if platform != "all":
        topics = [t for t in topics if t["platform"] == platform]
    if category != "all":
        topics = [t for t in topics if t["category"] == category]
    topics = sorted(topics, key=lambda x: x["heat_score"], reverse=True)[:limit]

    return {
        "topics": topics,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total_count": len(topics),
    }


@tool
def generate_song_inspiration(topic: str, style: str = "流行", mood: str = "温暖") -> dict:
    """基于热点话题生成歌曲创作灵感，包括歌名建议、Hook 文案和创作方向。

    参数:
        topic: 热点话题关键词
        style: 期望的音乐风格，如 '流行' / '民谣' / 'R&B' / '电子' / '说唱' / '国风'
        mood: 期望的情绪氛围，如 '温暖' / '伤感' / '欢快' / '激昂' / '治愈'
    """
    names = random.sample(_SONG_NAME_IDEAS, min(5, len(_SONG_NAME_IDEAS)))
    formatted_names = [n.format(keyword=topic) for n in names]

    return {
        "topic": topic,
        "style": style,
        "mood": mood,
        "song_names": formatted_names,
        "hook_ideas": [
            f"如果{topic}有颜色，那一定是你眼中的光",
            f"在{topic}的尽头，我找到了答案",
            f"每一个关于{topic}的梦，都值得被唱成歌",
        ],
        "structure_suggestion": f"建议采用 Verse-PreChorus-Chorus 结构，Verse 用叙事铺陈'{topic}'场景，"
                                f"PreChorus 情绪递进，Chorus 用{mood}的旋律释放情感，"
                                f"风格偏{style}，BPM 建议 {'85-95' if mood in ('伤感', '治愈') else '110-128'}",
        "reference_artists": _get_reference_artists(style),
    }


def _get_reference_artists(style: str) -> list[str]:
    mapping = {
        "流行": ["周杰伦", "林俊杰", "薛之谦"],
        "民谣": ["陈鸿宇", "房东的猫", "花粥"],
        "R&B": ["方大同", "陶喆", "袁娅维"],
        "电子": ["Anti-General", "Carta", "Howie Lee"],
        "说唱": ["GAI", "万妮达", "马思唯"],
        "国风": ["银临", "Winky诗", "河图"],
    }
    return mapping.get(style, ["毛不易", "赵雷", "李荣浩"])


@tool
def generate_promo_tags(song_name: str, platform: str = "抖音") -> dict:
    """为歌曲生成站外宣推标签和话题建议。

    参数:
        song_name: 歌曲名称
        platform: 目标发布平台，如 '抖音' / '快手' / 'B站' / '小红书'
    """
    base_tags = [f"#{song_name}", "#新歌推荐", "#音乐人", "#原创音乐"]

    platform_tags = {
        "抖音": ["#抖音音乐", "#热门BGM", "#听歌识曲", f"#{song_name}挑战"],
        "快手": ["#快手音乐人", "#原创歌手", "#好歌推荐"],
        "B站": ["#B站音乐", "#翻唱原创", "#音乐分享", f"#{song_name}全曲首发"],
        "小红书": ["#歌单推荐", "#宝藏歌曲", "#耳朵怀孕", f"#{song_name}循环中"],
    }

    return {
        "song_name": song_name,
        "platform": platform,
        "recommended_tags": base_tags + platform_tags.get(platform, []),
        "title_suggestions": [
            f"听完这首《{song_name}》，我破防了…",
            f"凌晨三点单曲循环的《{song_name}》",
            f"被《{song_name}》治愈的第 {random.randint(50, 200)} 天",
        ],
        "best_post_time": _get_best_time(platform),
        "content_tips": f"在{platform}发布时，建议用 15-30 秒副歌片段作为视频 BGM，"
                        f"搭配歌词字幕卡点，开头 3 秒设置悬念或情感钩子",
    }


def _get_best_time(platform: str) -> str:
    times = {
        "抖音": "12:00-13:00 / 18:00-20:00 / 21:00-23:00",
        "快手": "11:00-13:00 / 17:00-19:00 / 20:00-22:00",
        "B站": "18:00-20:00 / 21:00-23:00",
        "小红书": "12:00-14:00 / 19:00-21:00 / 22:00-23:30",
    }
    return times.get(platform, "19:00-22:00")
