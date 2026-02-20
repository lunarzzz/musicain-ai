import React, { useState } from 'react';

/**
 * 工具调用结果卡片组件 — 根据 card_type 渲染不同的数据展示
 */

interface CardAction {
    label: string;
    action_type: string;
    url?: string;
    payload?: Record<string, unknown>;
}

interface ToolCardProps {
    card: {
        card_type: string;
        title: string;
        data: Record<string, unknown>;
        actions?: CardAction[];
    };
    onAction?: (prompt: string) => void;
}

export const ToolCard: React.FC<ToolCardProps> = ({ card, onAction }) => {
    const renderBody = () => {
        switch (card.card_type) {
            case 'hot_trend':
                return <HotTrendCard data={card.data} />;
            case 'song_recommend':
                return <SongRecommendCard data={card.data} />;
            case 'promotion_plan':
                return <PromotionPlanCard data={card.data} />;
            case 'data_report':
                return <DataReportCard data={card.data} />;
            case 'audience_portrait':
                return <AudiencePortraitCard data={card.data} />;
            case 'knowledge':
                return <KnowledgeCard data={card.data} />;
            default:
                return <GenericCard data={card.data} />;
        }
    };

    return (
        <div className="tool-card">
            <div className="tool-card-header">{card.title}</div>
            <div className="tool-card-body">{renderBody()}</div>
            {card.actions && card.actions.length > 0 && (
                <div className="tool-card-actions">
                    {card.actions.map((action, i) => (
                        <button
                            key={i}
                            className="card-action-btn"
                            onClick={() => {
                                if (action.action_type === 'callback' && onAction) {
                                    onAction(action.payload?.action as string || action.label);
                                }
                            }}
                        >
                            {action.label}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
};

/* ── 热点卡片 ── */
const HotTrendCard: React.FC<{ data: Record<string, unknown> }> = ({ data }) => {
    const topics = (data.topics as Array<Record<string, unknown>>) || [];
    const songNames = (data.song_names as string[]) || [];

    if (songNames.length > 0) {
        // 创作灵感卡片
        return (
            <div>
                <div style={{ marginBottom: 12 }}>
                    <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 8 }}>
                        🎵 歌名建议
                    </div>
                    {songNames.map((name, i) => (
                        <div key={i} style={{
                            padding: '6px 12px', marginBottom: 4,
                            background: 'var(--bg-card)', borderRadius: 'var(--radius-sm)',
                            fontSize: 14, color: 'var(--text-primary)'
                        }}>
                            {name}
                        </div>
                    ))}
                </div>
                {data.hook_ideas ? (
                    <div>
                        <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 8 }}>
                            🎤 Hook 灵感
                        </div>
                        {(data.hook_ideas as string[]).map((hook, i) => (
                            <div key={i} style={{
                                padding: '6px 12px', marginBottom: 4,
                                background: 'var(--bg-card)', borderRadius: 'var(--radius-sm)',
                                fontSize: 13, color: 'var(--text-secondary)', fontStyle: 'italic'
                            }}>
                                "{hook}"
                            </div>
                        ))}
                    </div>
                ) : null}
            </div>
        );
    }

    // 热点列表
    return (
        <div>
            {topics.map((topic, i) => (
                <div key={i} className="trend-item">
                    <div className={`trend-rank ${i < 1 ? 'top' : ''}`}>{i + 1}</div>
                    <div className="trend-info">
                        <div className="trend-title">{topic.title as string}</div>
                        <div className="trend-meta">
                            <span>{topic.platform as string}</span>
                            <span>🔥 {(topic.heat_score as number)?.toLocaleString()}</span>
                        </div>
                    </div>
                    <span className={`trend-badge ${topic.trend as string}`}>
                        {topic.trend === 'rising' ? '📈 上升' : topic.trend === 'hot' ? '🔥 热门' : '📊 平稳'}
                    </span>
                </div>
            ))}
        </div>
    );
};

/* ── 推歌卡片 ── */
const SongRecommendCard: React.FC<{ data: Record<string, unknown> }> = ({ data }) => {
    const recommendations = (data.recommendations as Array<Record<string, unknown>>) || [];

    return (
        <div>
            {data.diagnosis ? (
                <div style={{
                    padding: '10px 14px', marginBottom: 12,
                    background: 'var(--bg-accent-subtle)', borderRadius: 'var(--radius-sm)',
                    fontSize: 13, color: 'var(--text-accent)', lineHeight: 1.5,
                }}>
                    💡 {String(data.diagnosis)}
                </div>
            ) : null}
            {recommendations.map((rec, i) => {
                const song = rec.song as Record<string, unknown>;
                const reasons = rec.reasons as string[];
                return (
                    <div key={i} className="recommend-item">
                        <div className="recommend-header">
                            <div className="recommend-rank-badge">{rec.rank as number}</div>
                            <div className="recommend-song-name">《{song?.name as string}》</div>
                            <span className="recommend-stage">{song?.stage as string}</span>
                        </div>
                        <div className="recommend-reasons">
                            {reasons?.map((reason, j) => (
                                <div key={j} className="recommend-reason">{reason}</div>
                            ))}
                        </div>
                        {rec.suggested_budget ? (
                            <div className="recommend-budget">
                                建议预算: ¥{Number(rec.suggested_budget).toLocaleString()}
                            </div>
                        ) : null}
                    </div>
                );
            })}
        </div>
    );
};

/* ── 投放计划卡片 ── */
const PromotionPlanCard: React.FC<{ data: Record<string, unknown> }> = ({ data }) => {
    const plan = data.plan as Record<string, unknown>;
    const expected = data.expected_results as Record<string, string>;
    const channels = plan?.channel_allocation as Record<string, string>;
    const timeline = plan?.timeline as Array<Record<string, string>>;

    return (
        <div>
            {expected && (
                <div className="metric-grid">
                    <div className="metric-item">
                        <div className="metric-value">{expected.estimated_plays}</div>
                        <div className="metric-label">预估播放</div>
                    </div>
                    <div className="metric-item">
                        <div className="metric-value">{expected.estimated_new_fans}</div>
                        <div className="metric-label">预估新粉</div>
                    </div>
                    <div className="metric-item">
                        <div className="metric-value">{expected.estimated_collections}</div>
                        <div className="metric-label">预估收藏</div>
                    </div>
                </div>
            )}
            {channels && (
                <div style={{ marginBottom: 12 }}>
                    <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 8 }}>渠道分配</div>
                    {Object.entries(channels).map(([ch, val]) => (
                        <div key={ch} style={{
                            display: 'flex', justifyContent: 'space-between',
                            padding: '5px 0', fontSize: 13,
                            borderBottom: '1px solid var(--border-subtle)'
                        }}>
                            <span style={{ color: 'var(--text-secondary)' }}>{ch}</span>
                            <span style={{ color: 'var(--text-accent)' }}>{val}</span>
                        </div>
                    ))}
                </div>
            )}
            {timeline && (
                <div>
                    <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 8 }}>执行节奏</div>
                    {timeline.map((phase, i) => (
                        <div key={i} style={{
                            padding: '8px 12px', marginBottom: 4,
                            background: 'var(--bg-card)', borderRadius: 'var(--radius-sm)',
                            fontSize: 13
                        }}>
                            <span style={{ color: 'var(--text-accent)', fontWeight: 600 }}>{phase.phase}</span>
                            <br />
                            <span style={{ color: 'var(--text-secondary)' }}>{phase.action}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

/* ── 数据报告卡片 ── */
const DataReportCard: React.FC<{ data: Record<string, unknown> }> = ({ data }) => {
    // 跨平台分析
    if (data.platforms) {
        const platforms = data.platforms as Array<Record<string, unknown>>;
        return (
            <div>
                <div className="metric-grid">
                    {platforms.map((p, i) => (
                        <div key={i} className="metric-item">
                            <div className="metric-value" style={{ fontSize: 16 }}>{(p.plays as number)?.toLocaleString()}</div>
                            <div className="metric-label">{p.name as string}</div>
                            <div className={`metric-change ${(p.growth as string)?.startsWith('+') ? 'up' : 'down'}`}>
                                {p.growth as string}
                            </div>
                        </div>
                    ))}
                </div>
                {data.comparison_insight ? (
                    <div style={{
                        padding: '10px 14px', marginTop: 8,
                        background: 'var(--bg-card)', borderRadius: 'var(--radius-sm)',
                        fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6,
                    }}>
                        {String(data.comparison_insight)}
                    </div>
                ) : null}
            </div>
        );
    }

    // 指标变化归因
    if (data.attribution) {
        const factors = data.attribution as Array<Record<string, string>>;
        return (
            <div>
                <div className="metric-grid" style={{ gridTemplateColumns: 'repeat(2, 1fr)', marginBottom: 14 }}>
                    <div className="metric-item">
                        <div className="metric-label">当前值</div>
                        <div className="metric-value" style={{ fontSize: 18 }}>{data.current_value as string}</div>
                    </div>
                    <div className="metric-item">
                        <div className="metric-label">变化率</div>
                        <div className="metric-value" style={{
                            fontSize: 18,
                            color: (data.direction as string) === '上升' ? 'var(--color-success)' : 'var(--color-error)',
                        }}>
                            {data.change_rate as string}
                        </div>
                    </div>
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 8 }}>变化归因</div>
                {factors.map((f, i) => (
                    <div key={i} style={{
                        padding: '8px 12px', marginBottom: 4,
                        background: 'var(--bg-card)', borderRadius: 'var(--radius-sm)',
                        fontSize: 13,
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                            <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{f.factor}</span>
                            <span style={{
                                color: f.contribution?.startsWith('+') ? 'var(--color-success)' : 'var(--color-error)',
                                fontWeight: 600,
                            }}>
                                {f.contribution}
                            </span>
                        </div>
                        <div style={{ color: 'var(--text-tertiary)', fontSize: 12 }}>{f.detail}</div>
                    </div>
                ))}
            </div>
        );
    }

    // 宣推复盘
    if (data.summary) {
        const summary = data.summary as Record<string, string>;
        return (
            <div>
                <div className="metric-grid">
                    {Object.entries(summary).map(([key, val]) => (
                        <div key={key} className="metric-item">
                            <div className="metric-value" style={{ fontSize: 16 }}>{val}</div>
                            <div className="metric-label">{key}</div>
                        </div>
                    ))}
                </div>
                {data.next_steps ? (
                    <div style={{ marginTop: 8 }}>
                        <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 6 }}>下一步建议</div>
                        {(data.next_steps as string[]).map((step, i) => (
                            <div key={i} className="recommend-reason">{step}</div>
                        ))}
                    </div>
                ) : null}
            </div>
        );
    }

    return <GenericCard data={data} />;
};

/* ── 听众画像卡片 ── */
const AudiencePortraitCard: React.FC<{ data: Record<string, unknown> }> = ({ data }) => {
    const portrait = data.portrait as Record<string, unknown>;
    const ages = portrait?.age_distribution as Array<Record<string, unknown>>;
    const gender = portrait?.gender as Record<string, number>;
    const regions = portrait?.top_regions as Array<Record<string, unknown>>;

    return (
        <div>
            <div className="metric-grid" style={{ gridTemplateColumns: '1fr 1fr', marginBottom: 14 }}>
                <div className="metric-item">
                    <div className="metric-value">{data.total_listeners as string}</div>
                    <div className="metric-label">听众总数（{data.period as string}）</div>
                </div>
                <div className="metric-item">
                    <div className="metric-value" style={{ fontSize: 16 }}>
                        {(portrait?.listening_time as Record<string, string>)?.peak_hours}
                    </div>
                    <div className="metric-label">收听高峰</div>
                </div>
            </div>

            {ages && (
                <div style={{ marginBottom: 14 }}>
                    <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 8 }}>年龄分布</div>
                    {ages.map((age, i) => (
                        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                            <span style={{ fontSize: 12, color: 'var(--text-tertiary)', width: 70 }}>{age.range as string}</span>
                            <div style={{
                                flex: 1, height: 8, background: 'var(--bg-card)', borderRadius: 4, overflow: 'hidden'
                            }}>
                                <div style={{
                                    width: `${age.percent as number}%`, height: '100%',
                                    background: 'var(--bg-accent)', borderRadius: 4
                                }} />
                            </div>
                            <span style={{ fontSize: 12, color: 'var(--text-accent)', width: 35 }}>{age.percent as number}%</span>
                        </div>
                    ))}
                </div>
            )}

            {gender && (
                <div style={{ display: 'flex', gap: 12, marginBottom: 14 }}>
                    <div className="metric-item" style={{ flex: 1 }}>
                        <div className="metric-value" style={{ fontSize: 18 }}>♂ {gender.male}%</div>
                        <div className="metric-label">男性</div>
                    </div>
                    <div className="metric-item" style={{ flex: 1 }}>
                        <div className="metric-value" style={{ fontSize: 18 }}>♀ {gender.female}%</div>
                        <div className="metric-label">女性</div>
                    </div>
                </div>
            )}

            {regions && (
                <div>
                    <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 8 }}>TOP 地域</div>
                    {regions.map((r, i) => (
                        <div key={i} style={{
                            display: 'flex', justifyContent: 'space-between',
                            padding: '4px 0', fontSize: 13,
                            borderBottom: '1px solid var(--border-subtle)'
                        }}>
                            <span style={{ color: 'var(--text-secondary)' }}>{r.region as string}</span>
                            <span style={{ color: 'var(--text-accent)' }}>{r.percent as number}%</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

/* ── 知识卡片 ── */
const KnowledgeCard: React.FC<{ data: Record<string, unknown> }> = ({ data }) => {
    const results = (data.results as Array<Record<string, string>>) || [];

    // 上传预检
    if (data.can_upload !== undefined) {
        const items = [
            ...(data.passed as string[] || []).map(t => ({ text: t, type: 'pass' })),
            ...(data.warnings as string[] || []).map(t => ({ text: t, type: 'warn' })),
            ...(data.issues as string[] || []).map(t => ({ text: t, type: 'fail' })),
        ];
        return (
            <div>
                <div style={{
                    padding: '10px 14px', marginBottom: 12,
                    background: data.can_upload ? 'rgba(52,211,153,0.1)' : 'rgba(248,113,113,0.1)',
                    borderRadius: 'var(--radius-sm)', fontSize: 14, fontWeight: 600,
                    color: data.can_upload ? 'var(--color-success)' : 'var(--color-error)',
                }}>
                    {String(data.summary)}
                </div>
                {items.map((item, i) => (
                    <div key={i} className={`check-item ${item.type}`}>{item.text}</div>
                ))}
            </div>
        );
    }

    // FAQ 结果
    return (
        <div>
            {results.map((r, i) => (
                <div key={i} className="knowledge-result">
                    <div className="knowledge-question">{r.question}</div>
                    <div className="knowledge-answer">{r.answer}</div>
                    <div className="knowledge-source">📎 来源：{r.source}</div>
                </div>
            ))}
            {data.note ? (
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 8 }}>
                    {String(data.note)}
                </div>
            ) : null}
        </div>
    );
};

/* ── 通用卡片 ── */
const GenericCard: React.FC<{ data: Record<string, unknown> }> = ({ data }) => {
    const [expanded, setExpanded] = useState(false);
    const json = JSON.stringify(data, null, 2);
    const preview = json.length > 200 ? json.slice(0, 200) + '...' : json;

    return (
        <div>
            <pre style={{
                fontSize: 12, color: 'var(--text-secondary)',
                background: 'var(--bg-card)', padding: 12,
                borderRadius: 'var(--radius-sm)',
                overflow: 'auto', maxHeight: expanded ? 'none' : 200,
                fontFamily: 'var(--font-mono)',
            }}>
                {expanded ? json : preview}
            </pre>
            {json.length > 200 && (
                <button
                    onClick={() => setExpanded(!expanded)}
                    style={{
                        background: 'none', border: 'none', color: 'var(--text-accent)',
                        fontSize: 12, cursor: 'pointer', marginTop: 6,
                    }}
                >
                    {expanded ? '收起' : '展开全部'}
                </button>
            )}
        </div>
    );
};
