# 🎵 音乐人 AI 助手 MVP

基于 AI Agent + Function Calling 架构的音乐人工作流 Copilot，集成热点创作、宣推建议、智能分析、问答指南四大能力。

## 技术栈

| 层级 | 技术 |
|---|---|
| 后端 | Python + FastAPI + LangChain |
| 前端 | Vite + React + TypeScript |
| LLM | OpenAI 兼容接口（混元 / DeepSeek / GPT） |
| 存储 | SQLite |

## 快速开始

### 1. 后端

```bash
cd server

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置 LLM API Key
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key 和模型配置

# 启动
python main.py
```

后端运行在 `http://localhost:8000`

### 2. 前端

```bash
cd web
npm install
npm run dev
```

前端运行在 `http://localhost:5173`，自动代理 `/api` 到后端。

### 3. 使用

打开 `http://localhost:5173`，试试这些对话：

- 🔥 "最近有什么热点可以用来创作？"
- 🚀 "帮我分析一下我该推哪首歌"
- 👥 "看看我的听众画像"
- 📊 "最近播放量有什么变化？"
- 📤 "上传歌曲需要什么格式？"
- 🎉 "最近有什么音乐人活动？"

## 项目结构

```
├── server/              # Python 后端
│   ├── main.py          # FastAPI 入口 (SSE 流式接口)
│   ├── agent.py         # Agent 编排 (LangChain + Function Calling)
│   ├── tools/           # 4 组业务 Tools (11 个工具函数)
│   │   ├── hot_trends   # 热点创作 (热点/灵感/标签)
│   │   ├── promotion    # 宣推建议 (推歌/投放/复盘)
│   │   ├── analytics    # 智能分析 (画像/跨平台/归因)
│   │   └── knowledge    # 问答指南 (FAQ/上传预检)
│   ├── models.py        # Pydantic 数据模型
│   ├── database.py      # SQLite 对话持久化
│   └── config.py        # 环境变量配置
├── web/                 # React 前端
│   └── src/
│       ├── App.tsx              # 主应用
│       ├── pages/ChatPage.tsx   # 对话页 (SSE 流式)
│       └── components/
│           ├── ToolCard.tsx      # 工具结果卡片 (7 种)
│           ├── MessageBubble.tsx # 消息气泡 (Markdown)
│           ├── Sidebar.tsx       # 会话侧边栏
│           └── QuickActions.tsx  # 快捷操作
└── docs/
    └── technical-architecture.md  # 技术架构方案
```

## LLM 配置示例

编辑 `server/.env`，支持多种 LLM 提供商：

```bash
# DeepSeek (推荐，性价比高)
LLM_API_KEY=sk-xxx
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat

# OpenAI
LLM_API_KEY=sk-xxx
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini

# 混元
LLM_API_KEY=xxx
LLM_BASE_URL=https://api.hunyuan.cloud.tencent.com/v1
LLM_MODEL=hunyuan-pro
```
