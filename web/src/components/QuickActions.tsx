import React from 'react';

interface QuickAction {
    id: string;
    icon: string;
    label: string;
    prompt: string;
}

interface QuickActionsProps {
    actions: QuickAction[];
    onSelect: (prompt: string) => void;
}

export const QuickActions: React.FC<QuickActionsProps> = ({ actions, onSelect }) => {
    return (
        <div className="welcome-page">
            <div className="welcome-icon">🎵</div>
            <h1 className="welcome-title">音乐人 AI 助手</h1>
            <p className="welcome-subtitle">
                我是你的音乐工作流 Copilot，可以帮你追踪热点、分析数据、
                制定宣推策略、解答平台问题。选择下方快捷入口或直接输入你的问题。
            </p>
            <div className="quick-actions-grid">
                {actions.map((action) => (
                    <div
                        key={action.id}
                        className="quick-action-card"
                        onClick={() => onSelect(action.prompt)}
                    >
                        <div className="quick-action-icon">{action.icon}</div>
                        <div className="quick-action-label">{action.label}</div>
                    </div>
                ))}
            </div>
        </div>
    );
};
