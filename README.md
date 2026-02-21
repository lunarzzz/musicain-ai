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
    └── multi-agent-architecture.md  # Multi-agent 技术方案
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

# OpenRouter (聚合多模型，推荐)
LLM_API_KEY=sk-or-v1-xxx
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=google/gemini-2.0-flash-001

# 混元
LLM_API_KEY=xxx
LLM_BASE_URL=https://api.hunyuan.cloud.tencent.com/v1
LLM_MODEL=hunyuan-pro
```

## 🚀 线上部署（免费方案）

采用 **Vercel（前端）+ Render（后端）** 组合，均有免费额度。

### 前置：推送代码到 GitHub

```bash
git add .
git commit -m "feat: musician AI assistant MVP"
git remote add origin git@github.com:你的用户名/musicain-ai.git
git push -u origin main
```

### Step 1：部署后端到 Render

1. 打开 [render.com](https://render.com)，用 GitHub 登录
2. 点击 **New → Web Service** → 选择 `musicain-ai` 仓库
3. 填写配置：

| 配置项 | 值 |
|---|---|
| **Name** | `musician-ai-server` |
| **Region** | `Singapore`（离中国最近） |
| **Runtime** | `Python` |
| **Root Directory** | `server` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| **Plan** | `Free` |

4. 在 **Environment Variables** 中添加以下变量：

| 环境变量 | 值 |
|---|---|
| `LLM_API_KEY` | 你的 API Key（如 OpenRouter: `sk-or-v1-xxx`） |
| `LLM_BASE_URL` | `https://openrouter.ai/api/v1` |
| `LLM_MODEL` | `google/gemini-2.0-flash-001` |
| `CORS_ORIGINS` | `https://你的域名.vercel.app,http://localhost:5173` |

5. 点击 **Create Web Service** → 等待构建完成
6. 构建成功后获得后端 URL，如：`https://musician-ai-server.onrender.com`

> 💡 **验证后端**：访问 `https://你的后端URL/api/health`，应返回 `{"status":"ok","version":"0.1.0"}`

### Step 2：更新前端代理地址

编辑 `web/vercel.json`，将 `destination` 改为你的实际 Render URL：

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://你的后端URL.onrender.com/api/:path*"
    }
  ]
}
```

提交并推送：

```bash
git add web/vercel.json
git commit -m "fix: update backend proxy URL"
git push
```

### Step 3：部署前端到 Vercel

1. 打开 [vercel.com](https://vercel.com)，用 GitHub 登录
2. 点击 **New Project** → 导入 `musicain-ai` 仓库
3. 填写配置：

| 配置项 | 值 |
|---|---|
| **Framework Preset** | `Vite` |
| **Root Directory** | `web` |
| 其余 | 保持默认 |

4. 点击 **Deploy** → 约 30 秒完成 🎉
5. 部署成功后获得前端 URL，如：`https://musicain-ai.vercel.app`

### Step 4：更新 Render CORS

回到 Render 控制台 → 你的 Web Service → **Environment** → 修改 `CORS_ORIGINS` 为你的实际 Vercel 域名：

```
https://musicain-ai.vercel.app,http://localhost:5173
```

保存后 Render 会自动重启服务。

### 部署完成 ✅

访问 `https://你的域名.vercel.app` 即可使用。

### ⚠️ 注意事项

| 项目 | 说明 |
|---|---|
| **Render 免费版休眠** | 15 分钟无请求会休眠，首次唤醒约 30~50 秒。可用 [UptimeRobot](https://uptimerobot.com) 免费定时 ping 保活 |
| **SQLite 持久化** | Render 免费版文件系统不持久，重启后对话记录丢失。正式使用建议换 Render 免费 PostgreSQL |
| **LLM 费用** | OpenRouter 按 token 收费，Gemini Flash 约 $0.075/百万 token，日常使用几乎免费 |
| **自定义域名** | Vercel 和 Render 均支持绑定自定义域名（免费） |

