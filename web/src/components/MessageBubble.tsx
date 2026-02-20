import React from 'react';
import { ToolCard } from './ToolCard';

interface Message {
    id: string;
    role: string;
    content: string;
    cards?: Array<{
        card_type: string;
        title: string;
        data: Record<string, unknown>;
        actions?: Array<{
            label: string;
            action_type: string;
            url?: string;
            payload?: Record<string, unknown>;
        }>;
    }>;
}

interface MessageBubbleProps {
    message: Message;
    onCardAction?: (prompt: string) => void;
}

/**
 * 简单的 Markdown 渲染 — 处理 **粗体**, 列表, 代码, 换行
 */
function renderMarkdown(text: string): React.ReactNode[] {
    const lines = text.split('\n');
    const elements: React.ReactNode[] = [];
    let listItems: string[] = [];
    let listType: 'ul' | 'ol' | null = null;

    const flushList = () => {
        if (listItems.length > 0 && listType) {
            const Tag = listType;
            elements.push(
                <Tag key={`list-${elements.length}`}>
                    {listItems.map((item, i) => (
                        <li key={i}>{formatInline(item)}</li>
                    ))}
                </Tag>
            );
            listItems = [];
            listType = null;
        }
    };

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];

        // Unordered list
        if (/^[-*]\s+/.test(line)) {
            if (listType !== 'ul') flushList();
            listType = 'ul';
            listItems.push(line.replace(/^[-*]\s+/, ''));
            continue;
        }

        // Ordered list
        if (/^\d+\.\s+/.test(line)) {
            if (listType !== 'ol') flushList();
            listType = 'ol';
            listItems.push(line.replace(/^\d+\.\s+/, ''));
            continue;
        }

        flushList();

        // Empty line
        if (line.trim() === '') {
            continue;
        }

        // Heading
        if (line.startsWith('### ')) {
            elements.push(
                <h4 key={i} style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-accent)', margin: '12px 0 6px' }}>
                    {formatInline(line.slice(4))}
                </h4>
            );
        } else if (line.startsWith('## ')) {
            elements.push(
                <h3 key={i} style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-accent)', margin: '14px 0 8px' }}>
                    {formatInline(line.slice(3))}
                </h3>
            );
        } else {
            // Regular paragraph
            elements.push(<p key={i}>{formatInline(line)}</p>);
        }
    }

    flushList();
    return elements;
}

function formatInline(text: string): React.ReactNode[] {
    const parts: React.ReactNode[] = [];
    // Match **bold**, `code`, and plain text
    const regex = /(\*\*(.+?)\*\*)|(`(.+?)`)/g;
    let lastIndex = 0;
    let match;

    while ((match = regex.exec(text)) !== null) {
        if (match.index > lastIndex) {
            parts.push(text.slice(lastIndex, match.index));
        }
        if (match[2]) {
            parts.push(<strong key={match.index}>{match[2]}</strong>);
        } else if (match[4]) {
            parts.push(<code key={match.index}>{match[4]}</code>);
        }
        lastIndex = regex.lastIndex;
    }

    if (lastIndex < text.length) {
        parts.push(text.slice(lastIndex));
    }

    return parts.length > 0 ? parts : [text];
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message, onCardAction }) => {
    const isUser = message.role === 'user';

    return (
        <div className={`message-wrapper ${isUser ? 'user' : 'assistant'}`}>
            <div className={`message-bubble ${isUser ? 'user' : 'assistant'}`}>
                {isUser ? (
                    message.content
                ) : (
                    <>
                        {message.cards?.map((card, i) => (
                            <ToolCard key={i} card={card} onAction={onCardAction} />
                        ))}
                        {message.content && renderMarkdown(message.content)}
                    </>
                )}
            </div>
        </div>
    );
};

export const TypingIndicator: React.FC = () => (
    <div className="message-wrapper assistant">
        <div className="typing-indicator">
            <div className="typing-dot" />
            <div className="typing-dot" />
            <div className="typing-dot" />
        </div>
    </div>
);
