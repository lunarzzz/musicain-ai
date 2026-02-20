import React from 'react';

interface Conversation {
    id: string;
    title: string;
    updated_at: string;
    message_count: number;
}

interface SidebarProps {
    conversations: Conversation[];
    activeId: string | null;
    isOpen: boolean;
    onSelect: (id: string) => void;
    onNew: () => void;
    onDelete: (id: string) => void;
    onClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
    conversations,
    activeId,
    isOpen,
    onSelect,
    onNew,
    onDelete,
    onClose,
}) => {
    return (
        <div className={`sidebar ${isOpen ? 'open' : ''}`}>
            <div className="sidebar-header">
                <div className="sidebar-logo">
                    <div className="sidebar-logo-icon">🎵</div>
                    <div>
                        <div className="sidebar-logo-text">音乐人 AI 助手</div>
                        <div className="sidebar-logo-sub">Musician Copilot</div>
                    </div>
                </div>
                <button className="mobile-close-btn" onClick={onClose} aria-label="关闭侧边栏">
                    ×
                </button>
            </div>

            <div className="sidebar-actions">
                <button className="new-chat-btn" onClick={onNew}>
                    <span>✨</span> 新对话
                </button>
            </div>

            <div className="sidebar-conversations">
                {conversations.length === 0 && (
                    <div style={{
                        padding: '20px 14px',
                        textAlign: 'center',
                        fontSize: 13,
                        color: 'var(--text-tertiary)',
                    }}>
                        暂无对话记录
                    </div>
                )}
                {conversations.map((conv) => (
                    <div
                        key={conv.id}
                        className={`conv-item ${activeId === conv.id ? 'active' : ''}`}
                        onClick={() => onSelect(conv.id)}
                    >
                        <span className="conv-item-title">{conv.title}</span>
                        <button
                            className="conv-item-delete"
                            onClick={(e) => {
                                e.stopPropagation();
                                onDelete(conv.id);
                            }}
                            title="删除对话"
                        >
                            ×
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
};
