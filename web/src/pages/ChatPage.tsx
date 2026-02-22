import React, { useState, useRef, useEffect, useCallback } from 'react';
import { MessageBubble, TypingIndicator } from '../components/MessageBubble';
import { QuickActions } from '../components/QuickActions';

const API_BASE = '/api';

interface Message {
    id: string;
    role: string;
    content: string;
    follow_ups?: string[];
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

interface QuickAction {
    id: string;
    icon: string;
    label: string;
    prompt: string;
}

interface ChatPageProps {
    conversationId: string | null;
    onConversationCreated: (id: string) => void;
    onMenuClick: () => void;
}

export const ChatPage: React.FC<ChatPageProps> = ({ conversationId, onConversationCreated, onMenuClick }) => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [quickActions, setQuickActions] = useState<QuickAction[]>([]);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // 加载快捷操作
    useEffect(() => {
        fetch(`${API_BASE}/quick-actions`)
            .then((r) => r.json())
            .then(setQuickActions)
            .catch(() => { });
    }, []);

    // 加载会话消息
    useEffect(() => {
        if (conversationId) {
            fetch(`${API_BASE}/conversations/${conversationId}/messages`)
                .then((r) => r.json())
                .then((msgs) => {
                    setMessages(
                        msgs.map((m: Record<string, unknown>) => ({
                            id: m.id as string,
                            role: m.role as string,
                            content: m.content as string,
                            cards: m.cards as Message['cards'],
                            follow_ups: m.follow_ups as string[] | undefined,
                        }))
                    );
                })
                .catch(() => { });
        } else {
            setMessages([]);
        }
    }, [conversationId]);

    // 自动滚动
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isLoading]);

    // 自动调整输入框高度
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
        }
    }, [input]);

    const sendMessage = useCallback(
        async (text: string) => {
            if (!text.trim() || isLoading) return;

            const userMsg: Message = {
                id: `u-${Date.now()}`,
                role: 'user',
                content: text.trim(),
            };

            setMessages((prev) => [...prev, userMsg]);
            setInput('');
            setIsLoading(true);

            // SSE 流式请求
            try {
                const response = await fetch(`${API_BASE}/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: text.trim(),
                        conversation_id: conversationId,
                    }),
                });

                if (!response.ok) throw new Error('请求失败');

                const reader = response.body?.getReader();
                const decoder = new TextDecoder();

                let assistantContent = '';
                let assistantCards: Message['cards'] = [];
                let assistantFollowUps: string[] = [];
                const assistantId = `a-${Date.now()}`;

                // 立即添加一个空的 assistant 消息
                setMessages((prev) => [
                    ...prev,
                    { id: assistantId, role: 'assistant', content: '', cards: [], follow_ups: [] },
                ]);

                let buffer = '';

                while (reader) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });

                    // 处理 SSE 数据
                    const lines = buffer.split('\n');
                    buffer = lines.pop() || ''; // 保留未完成的行

                    for (const line of lines) {
                        if (!line.startsWith('data: ')) continue;
                        const jsonStr = line.slice(6).trim();
                        if (!jsonStr) continue;

                        try {
                            const chunk = JSON.parse(jsonStr);

                            switch (chunk.type) {
                                case 'token':
                                    assistantContent += chunk.content;
                                    setMessages((prev) =>
                                        prev.map((m) =>
                                            m.id === assistantId
                                                ? { ...m, content: assistantContent }
                                                : m
                                        )
                                    );
                                    break;

                                case 'card':
                                    assistantCards = [...(assistantCards || []), chunk.card];
                                    setMessages((prev) =>
                                        prev.map((m) =>
                                            m.id === assistantId
                                                ? { ...m, cards: assistantCards }
                                                : m
                                        )
                                    );
                                    break;

                                case 'follow_ups':
                                    assistantFollowUps = Array.isArray(chunk.questions) ? chunk.questions : [];
                                    setMessages((prev) =>
                                        prev.map((m) =>
                                            m.id === assistantId
                                                ? { ...m, follow_ups: assistantFollowUps }
                                                : m
                                        )
                                    );
                                    break;

                                case 'done':
                                    if (chunk.conversation_id && !conversationId) {
                                        onConversationCreated(chunk.conversation_id);
                                    }
                                    break;

                                case 'error':
                                    assistantContent += chunk.content || '出错了';
                                    setMessages((prev) =>
                                        prev.map((m) =>
                                            m.id === assistantId
                                                ? { ...m, content: assistantContent }
                                                : m
                                        )
                                    );
                                    break;
                            }
                        } catch {
                            // 忽略无法解析的行
                        }
                    }
                }
            } catch (err) {
                setMessages((prev) => [
                    ...prev.filter((m) => m.id !== `a-${Date.now()}`),
                    {
                        id: `e-${Date.now()}`,
                        role: 'assistant',
                        content: `⚠️ 网络错误，请检查后端服务是否启动。\n\n错误信息：${err}`,
                    },
                ]);
            } finally {
                setIsLoading(false);
            }
        },
        [conversationId, isLoading, onConversationCreated]
    );

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage(input);
        }
    };

    const showWelcome = messages.length === 0 && !conversationId;

    return (
        <div className="main-content">
            {/* 移动端顶部导航栏 */}
            <div className="mobile-header">
                <button className="mobile-menu-btn" onClick={onMenuClick} aria-label="打开侧边栏">
                    ☰
                </button>
                <span className="mobile-header-title">
                    {conversationId ? '聊天对话' : '✨ 新对话'}
                </span>
            </div>

            {showWelcome ? (
                <div className="welcome-container">
                    <QuickActions actions={quickActions} onSelect={sendMessage} />
                    <div className="input-area">
                        <div className="input-container">
                            <textarea
                                ref={textareaRef}
                                className="input-box"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="输入你的问题，如：最近有什么热点可以写歌？"
                                rows={1}
                                disabled={isLoading}
                            />
                            <button
                                className="send-btn"
                                onClick={() => sendMessage(input)}
                                disabled={!input.trim() || isLoading}
                            >
                                ↑
                            </button>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="chat-container">
                    <div className="messages-container">
                        <div className="messages-list">
                            {messages.map((msg) => (
                                <MessageBubble
                                    key={msg.id}
                                    message={msg}
                                    onCardAction={(action) => sendMessage(action)}
                                />
                            ))}
                            {isLoading && messages[messages.length - 1]?.role === 'user' && (
                                <TypingIndicator />
                            )}
                            <div ref={messagesEndRef} />
                        </div>
                    </div>
                    <div className="input-area">
                        <div className="input-container">
                            <textarea
                                ref={textareaRef}
                                className="input-box"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="继续对话..."
                                rows={1}
                                disabled={isLoading}
                            />
                            <button
                                className="send-btn"
                                onClick={() => sendMessage(input)}
                                disabled={!input.trim() || isLoading}
                            >
                                ↑
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
