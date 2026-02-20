"""智能分析 & 数据叙事服务 — 听众画像、跨平台分析、指标归因

MVP 阶段使用 Mock 数据。
"""

from __future__ import annotations

import random
from langchain_core.tools import tool


@tool
def get_audience_portrait(song_name: str = "全部作品") -> dict:
    """获取听众画像分析，包括年龄、性别、地域、听歌偏好等维度。

    参数:
        song_name: 歌曲名称，默认为全部作品的汇总画像
    """
    return {
        "song_name": song_name,
        "period": "近 30 天",
        "total_listeners": f"{random.randint(15000, 80000):,}",
        "portrait": {
            "age_distribution": [
                {"range": "18 岁以下", "percent": 8},
                {"range": "18-24 岁", "percent": 35},
                {"range": "25-30 岁", "percent": 32},
                {"range": "31-40 岁", "percent": 18},
                {"range": "40 岁以上", "percent": 7},
            ],
            "gender": {"male": 42, "female": 55, "unknown": 3},
            "top_regions": [
                {"region": "广东", "percent": 15.2},
                {"region": "浙江", "percent": 12.8},
                {"region": "北京", "percent": 10.5},
                {"region": "江苏", "percent": 9.3},
                {"region": "上海", "percent": 8.1},
            ],
            "listening_time": {
                "peak_hours": "21:00-23:00",
                "avg_duration": "3 分 42 秒",
                "weekend_vs_weekday": "周末播放量高 23%",
            },
            "taste_tags": ["华语流行", "独立音乐", "治愈", "深夜", "通勤"],
        },
        "insight": "你的核心听众是 18-30 岁的年轻人，女性占比略高（55%），"
                   "主要集中在一线和新一线城市。听歌高峰在晚间 21-23 点，"
                   "建议在这个时段发布新歌或推送互动内容。",
    }


@tool
def analyze_cross_platform(song_name: str = "月光信箱") -> dict:
    """分析歌曲在不同平台的表现差异，并给出归因和策略建议。

    参数:
        song_name: 歌曲名称
    """
    return {
        "song_name": song_name,
        "period": "近 30 天",
        "platforms": [
            {
                "name": "QQ音乐",
                "plays": 85000,
                "growth": "+12%",
                "completion_rate": "72%",
                "highlight": "搜索来源播放占比高 (25%)",
            },
            {
                "name": "酷狗音乐",
                "plays": 62000,
                "growth": "+8%",
                "completion_rate": "68%",
                "highlight": "歌单收录数量最多 (48 个歌单)",
            },
            {
                "name": "酷我音乐",
                "plays": 31000,
                "growth": "+15%",
                "completion_rate": "75%",
                "highlight": "完播率最高，用户粘性好",
            },
        ],
        "comparison_insight": "QQ 音乐搜索播放占比最高，说明你的歌名和 SEO 做得好；"
                              "酷狗歌单收录多但完播率稍低，建议优化歌单推荐封面文案；"
                              "酷我增速最快且完播率最高，可考虑在该平台加大宣推力度",
        "recommendations": [
            "在 QQ 音乐持续优化搜索关键词，保持搜播优势",
            "向酷狗音乐的 UGC 歌单运营者推荐你的新歌",
            "酷我音乐增速快，建议提交该平台的推荐位申请",
        ],
    }


@tool
def explain_metric_change(metric: str = "播放量", period: str = "最近 7 天") -> dict:
    """解释关键指标的变化原因，提供数据归因分析。

    参数:
        metric: 指标名称，如 '播放量' / '粉丝数' / '收入' / '收藏数'
        period: 分析周期，如 '最近 7 天' / '最近 30 天' / '本月'
    """
    changes = {
        "播放量": {
            "current": "128,500",
            "previous": "95,200",
            "change": "+35.0%",
            "direction": "上升",
            "factors": [
                {"factor": "推荐位曝光增加", "contribution": "+22%", "detail": "《海边的风》进入新歌推荐池"},
                {"factor": "站外引流", "contribution": "+8%", "detail": "抖音短视频带来 10,200 次播放"},
                {"factor": "季节性增长", "contribution": "+5%", "detail": "春节后用户活跃度整体回升"},
            ],
        },
        "粉丝数": {
            "current": "12,350",
            "previous": "11,800",
            "change": "+4.7%",
            "direction": "上升",
            "factors": [
                {"factor": "新歌发布", "contribution": "+3.2%", "detail": "《凌晨三点半》带来 320 新粉"},
                {"factor": "评论互动", "contribution": "+1.5%", "detail": "回复评论提升了粉丝转化"},
            ],
        },
        "收入": {
            "current": "¥3,250",
            "previous": "¥3,890",
            "change": "-16.5%",
            "direction": "下降",
            "factors": [
                {"factor": "结算歌曲数减少", "contribution": "-10%", "detail": "2 首歌授权到期，不再产生分成"},
                {"factor": "播放单价波动", "contribution": "-4%", "detail": "平台整体 CPM 季节性调整"},
                {"factor": "新歌尚未进入结算", "contribution": "-2.5%", "detail": "本月新发的歌下月才开始结算"},
            ],
        },
    }

    data = changes.get(metric, changes["播放量"])
    return {
        "metric": metric,
        "period": period,
        "current_value": data["current"],
        "previous_value": data["previous"],
        "change_rate": data["change"],
        "direction": data["direction"],
        "attribution": data["factors"],
        "data_source": "音乐人数据中心（口径：全平台去重播放）",
        "suggestion": "数据仅供参考，如有疑问可联系客服核实"
                      if data["direction"] == "下降"
                      else "保持当前策略，持续关注核心指标变化",
    }
