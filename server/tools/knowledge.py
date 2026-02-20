"""问答指南 & 客服服务 — RAG 知识检索、上传预检

MVP 使用 FAISS 内存向量库 + Markdown 知识文档。
"""

from __future__ import annotations

import os
from pathlib import Path

from langchain_core.tools import tool

# ── 知识库数据 (内联 Mock，替代 FAISS 向量检索) ──────────

_KNOWLEDGE_BASE: dict[str, list[dict]] = {
    "入驻": [
        {
            "q": "如何成为腾讯音乐人？",
            "a": "1. 访问音乐人开放平台官网或小程序\n"
                 "2. 选择身份类型（原创音乐人 / 翻唱歌手 / 制作人 / 厂牌）\n"
                 "3. 填写基本信息并上传身份证明\n"
                 "4. 提交至少 1 首原创作品\n"
                 "5. 等待审核（通常 3-5 个工作日）",
            "source": "入驻指南",
        },
        {
            "q": "入驻需要什么条件？",
            "a": "个人入驻需要：\n"
                 "- 年满 18 岁（未满 18 需监护人签字）\n"
                 "- 有效身份证件\n"
                 "- 至少 1 首完整原创音乐作品\n"
                 "- 作品不含侵权内容\n\n"
                 "机构入驻额外需要：\n"
                 "- 营业执照\n"
                 "- 法人授权书\n"
                 "- 音乐版权证明材料",
            "source": "入驻指南",
        },
    ],
    "上传": [
        {
            "q": "上传歌曲需要什么格式？",
            "a": "音频格式要求：\n"
                 "- 格式：WAV / FLAC / MP3（推荐 WAV 或 FLAC）\n"
                 "- 采样率：≥ 44.1kHz\n"
                 "- 位深：≥ 16bit\n"
                 "- 码率：MP3 ≥ 320kbps\n\n"
                 "封面要求：\n"
                 "- 尺寸：≥ 3000×3000 px\n"
                 "- 格式：JPG / PNG\n"
                 "- 大小：≤ 10MB\n"
                 "- 不含二维码、水印、联系方式",
            "source": "上传规范",
        },
        {
            "q": "歌词格式要求是什么？",
            "a": "歌词格式要求：\n"
                 "- 支持 LRC 和纯文本格式\n"
                 "- LRC 需要时间标签精确到毫秒\n"
                 "- 纯文本需要按段落分行\n"
                 "- 不含其他平台的水印或标识\n"
                 "- 包含翻译歌词时需标注语种",
            "source": "上传规范",
        },
    ],
    "审核": [
        {
            "q": "审核一般需要多久？",
            "a": "审核时效：\n"
                 "- 常规审核：1-3 个工作日\n"
                 "- 节假日期间可能延长至 5 个工作日\n"
                 "- 紧急发行可申请加急审核（需提前报备）\n\n"
                 "常见驳回原因：\n"
                 "1. 封面不合规（含二维码/水印/侵权图片）\n"
                 "2. 音频质量不达标（底噪过大/削波失真）\n"
                 "3. 元数据不完整（缺少作者/作曲/编曲信息）\n"
                 "4. 疑似侵权（曲调/歌词与已有作品高度相似）",
            "source": "审核规则",
        },
    ],
    "结算": [
        {
            "q": "结算规则是怎样的？",
            "a": "结算周期与规则：\n"
                 "- 结算周期：月度结算，次月 15 日生成账单\n"
                 "- 提现门槛：满 100 元可提现\n"
                 "- 到账时间：提现后 3-5 个工作日\n"
                 "- 分成比例：根据合约类型不同，一般为 50%-70%\n\n"
                 "结算收入来源：\n"
                 "1. 播放分成（按有效播放量）\n"
                 "2. 会员专享分成（VIP 用户播放加权）\n"
                 "3. 数字专辑/单曲销售分成\n"
                 "4. 彩铃/BGM 授权收益",
            "source": "结算说明",
        },
        {
            "q": "为什么我的收入变少了？",
            "a": "收入变化常见原因：\n"
                 "1. **结算歌曲数变化**：部分歌曲授权到期或下架\n"
                 "2. **播放量波动**：自然衰减或推荐位调整\n"
                 "3. **平台单价调整**：季度性 CPM 浮动\n"
                 "4. **新歌结算延迟**：当月发布的歌通常下月才开始结算\n"
                 "5. **扣税/手续费**：个税代扣比例变化\n\n"
                 "如有异常，可通过 AI 助手使用「结算变化分析」功能查看详细归因。",
            "source": "结算 FAQ",
        },
    ],
    "版权": [
        {
            "q": "如何保护我的歌曲版权？",
            "a": "版权保护建议：\n"
                 "1. **创作留痕**：保存创作过程记录（demo、手稿、时间戳）\n"
                 "2. **版权登记**：通过中国版权保护中心或省级版权局登记\n"
                 "3. **平台维权**：发现侵权可在平台「维权中心」提交投诉\n"
                 "4. **证据保全**：使用可信时间戳或区块链存证\n\n"
                 "平台侧保护措施：\n"
                 "- 音频指纹检测（上传时自动比对）\n"
                 "- 侵权举报通道（7×24 小时受理）\n"
                 "- 维权结果跟踪（处理时效 ≤ 15 个工作日）",
            "source": "版权保护指南",
        },
    ],
    "活动": [
        {
            "q": "最近有什么音乐人活动？",
            "a": "当前进行中的活动：\n\n"
                 "🎵 **春日创作大赛**\n"
                 "- 时间：2026-02-15 ~ 2026-03-31\n"
                 "- 主题：以「春天」为灵感创作原创歌曲\n"
                 "- 奖励：一等奖 ¥10,000 + 首页推荐位 7 天\n\n"
                 "🎤 **新人扶持计划 S3**\n"
                 "- 时间：常年有效\n"
                 "- 对象：入驻 ≤ 6 个月的新音乐人\n"
                 "- 权益：免费推荐位 + 1v1 运营指导\n\n"
                 "📢 **短视频宣推补贴**\n"
                 "- 时间：2026-02-01 ~ 2026-04-30\n"
                 "- 内容：使用平台歌曲制作短视频，播放量 ≥ 10,000 可获补贴",
            "source": "活动中心",
        },
    ],
}


@tool
def search_knowledge(query: str, category: str = "all") -> dict:
    """在知识库中搜索音乐人相关规则和指南。涵盖入驻、上传、审核、结算、版权、活动等常见问题。

    参数:
        query: 用户的问题
        category: 分类筛选，可选 '入驻' / '上传' / '审核' / '结算' / '版权' / '活动' / 'all'
    """
    results = []

    if category != "all" and category in _KNOWLEDGE_BASE:
        search_items = [(category, items) for items in [_KNOWLEDGE_BASE[category]]]
    else:
        search_items = list(_KNOWLEDGE_BASE.items())

    query_lower = query.lower()

    for cat, items in search_items:
        for item in items:
            # 简单关键词匹配 (MVP 阶段，后续替换为向量检索)
            q_text = item["q"].lower()
            a_text = item["a"].lower()
            if any(kw in q_text or kw in a_text for kw in _extract_keywords(query_lower)):
                results.append({
                    "category": cat,
                    "question": item["q"],
                    "answer": item["a"],
                    "source": item["source"],
                    "relevance": "high",
                })

    # 如果没有精确匹配，返回最相关的分类
    if not results:
        best_cat = _guess_category(query_lower)
        if best_cat and best_cat in _KNOWLEDGE_BASE:
            for item in _KNOWLEDGE_BASE[best_cat][:2]:
                results.append({
                    "category": best_cat,
                    "question": item["q"],
                    "answer": item["a"],
                    "source": item["source"],
                    "relevance": "medium",
                })

    return {
        "query": query,
        "results": results[:3],
        "total_found": len(results),
        "note": "以上信息来自平台规则文档，如需人工客服请点击「联系客服」",
    }


@tool
def check_upload_compliance(
    audio_format: str = "mp3",
    sample_rate: int = 44100,
    cover_size: str = "3000x3000",
    has_lyrics: bool = True,
    has_composer_info: bool = True,
) -> dict:
    """上传前预检，检查音频和元数据是否符合平台要求。

    参数:
        audio_format: 音频格式，如 'wav' / 'flac' / 'mp3'
        sample_rate: 采样率 (Hz)
        cover_size: 封面尺寸，如 '3000x3000'
        has_lyrics: 是否包含歌词
        has_composer_info: 是否包含作曲/作词信息
    """
    issues = []
    warnings = []
    passed = []

    # 检查音频格式
    if audio_format.lower() in ("wav", "flac"):
        passed.append(f"✅ 音频格式 {audio_format.upper()} — 符合要求（推荐格式）")
    elif audio_format.lower() == "mp3":
        warnings.append("⚠️ 音频格式 MP3 — 可接受，但建议使用 WAV 或 FLAC 以获得更好音质")
    else:
        issues.append(f"❌ 音频格式 {audio_format} — 不支持，请转换为 WAV / FLAC / MP3")

    # 检查采样率
    if sample_rate >= 44100:
        passed.append(f"✅ 采样率 {sample_rate}Hz — 符合要求")
    else:
        issues.append(f"❌ 采样率 {sample_rate}Hz — 不足，要求 ≥ 44100Hz")

    # 检查封面
    try:
        w, h = map(int, cover_size.split("x"))
        if w >= 3000 and h >= 3000:
            passed.append(f"✅ 封面尺寸 {cover_size} — 符合要求")
        else:
            issues.append(f"❌ 封面尺寸 {cover_size} — 过小，要求 ≥ 3000×3000 px")
    except (ValueError, AttributeError):
        warnings.append("⚠️ 封面尺寸格式无法解析，请确认 ≥ 3000×3000 px")

    # 检查歌词
    if has_lyrics:
        passed.append("✅ 歌词 — 已提供")
    else:
        warnings.append("⚠️ 缺少歌词 — 非必填但强烈建议提供（影响搜索和推荐）")

    # 检查作曲信息
    if has_composer_info:
        passed.append("✅ 作曲/作词信息 — 已提供")
    else:
        issues.append("❌ 缺少作曲/作词信息 — 必填项，否则将被驳回")

    can_upload = len(issues) == 0

    return {
        "can_upload": can_upload,
        "summary": "✅ 可以上传" if can_upload else f"❌ 存在 {len(issues)} 个问题需要修复",
        "issues": issues,
        "warnings": warnings,
        "passed": passed,
        "tip": "修复所有 ❌ 项后即可上传" if not can_upload else "所有必需项均已通过，可以开始上传",
    }


def _extract_keywords(text: str) -> list[str]:
    """简单关键词提取"""
    keywords = []
    kw_map = {
        "入驻": ["入驻", "注册", "申请", "开通", "成为", "加入"],
        "上传": ["上传", "格式", "音频", "封面", "歌词", "提交"],
        "审核": ["审核", "驳回", "通过", "多久", "时间"],
        "结算": ["结算", "收入", "提现", "分成", "账单", "钱", "收益"],
        "版权": ["版权", "侵权", "维权", "保护", "抄袭"],
        "活动": ["活动", "比赛", "扶持", "补贴", "奖励"],
    }
    for cat, kws in kw_map.items():
        for kw in kws:
            if kw in text:
                keywords.append(kw)
    return keywords or [text[:4]]  # 回退到取前4个字


def _guess_category(text: str) -> str | None:
    """猜测问题所属分类"""
    cat_keywords = {
        "入驻": ["入驻", "注册", "加入", "开通", "条件"],
        "上传": ["上传", "格式", "文件", "提交", "发布"],
        "审核": ["审核", "驳回", "等", "多久"],
        "结算": ["结算", "钱", "收入", "提现"],
        "版权": ["版权", "侵权", "维权"],
        "活动": ["活动", "比赛", "奖"],
    }
    for cat, kws in cat_keywords.items():
        if any(kw in text for kw in kws):
            return cat
    return "入驻"
