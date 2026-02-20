import { useState, useEffect, useCallback } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatPage } from './pages/ChatPage';
import './index.css';

const API_BASE = '/api';

interface Conversation {
  id: string;
  title: string;
  updated_at: string;
  message_count: number;
}

function App() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const loadConversations = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/conversations`);
      if (res.ok) {
        const data = await res.json();
        setConversations(data);
      }
    } catch {
      // 后端未启动时静默处理
    }
  }, []);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  const handleNewChat = () => {
    setActiveConvId(null);
    setIsSidebarOpen(false);
  };

  const handleSelectConversation = (id: string) => {
    setActiveConvId(id);
    setIsSidebarOpen(false); // 手机端点选后自动收起
  };

  const handleDeleteConversation = async (id: string) => {
    try {
      await fetch(`${API_BASE}/conversations/${id}`, { method: 'DELETE' });
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (activeConvId === id) {
        setActiveConvId(null);
      }
    } catch {
      // ignore
    }
  };

  const handleConversationCreated = (id: string) => {
    setActiveConvId(id);
    // 刷新列表
    loadConversations();
  };

  return (
    <div className="app-layout">
      <Sidebar
        conversations={conversations}
        activeId={activeConvId}
        isOpen={isSidebarOpen}
        onSelect={handleSelectConversation}
        onNew={handleNewChat}
        onDelete={handleDeleteConversation}
        onClose={() => setIsSidebarOpen(false)}
      />
      {/* 移动端遮罩 */}
      {isSidebarOpen && (
        <div
          className="sidebar-backdrop"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}
      <ChatPage
        conversationId={activeConvId}
        onConversationCreated={handleConversationCreated}
        onMenuClick={() => setIsSidebarOpen(true)}
      />
    </div>
  );
}

export default App;
