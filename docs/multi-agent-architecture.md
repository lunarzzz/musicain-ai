# Multi-agent 技术方案（音乐人 AI 助手）

## 1. 目标与约束

### 业务目标
- 将“单一 Agent + 工具调用”升级为“多 Agent 协作”，提高复杂任务成功率（如「先找热点 → 选题 → 宣推计划 → 风险检查」）。
- 支持并行处理，降低整体响应时延。
- 让每个 Agent 有明确职责，降低提示词和工具耦合。

### 设计约束
- 兼容现有 FastAPI + SSE 对话接口。
- 工具层尽量复用 `server/tools`，减少重写。
- 默认保留可观测与可回放能力（日志、轨迹、成本）。

## 2. 总体架构

```text
Client (Web)
   │
   ▼
API Gateway (FastAPI /api/chat)
   │
   ▼
Orchestrator Agent（总控）
   ├── Planner（任务拆解）
   ├── Router（按子任务路由）
   ├── Parallel Executor（并发执行）
   ├── Critic/Verifier（结果校验）
   └── Synthesizer（最终汇总）
         │
         ├── Trend Agent（热点与选题）
         ├── Promotion Agent（宣推策略）
         ├── Analytics Agent（数据分析）
         └── Knowledge Agent（规则问答）
                │
                ▼
            Tool Layer + DB + External APIs
```

## 3. Agent 角色设计

### 3.1 Orchestrator（总控）
- 输入：用户问题 + 对话上下文。
- 输出：执行计划（plan）与最终答复。
- 职责：
  - 判断是“单 Agent 直出”还是“多 Agent 协作”。
  - 控制并发和超时。
  - 汇总结构化结果并生成自然语言答案。

### 3.2 Planner（规划）
- 将用户意图拆成若干可执行子任务（Subtask）。
- 产出统一 schema，例如：
  - `id`
  - `goal`
  - `required_capability`
  - `depends_on`
  - `timeout_ms`

### 3.3 Specialist Agents（领域 Agent）
- **Trend Agent**：热点检索、选题生成、标签建议。
- **Promotion Agent**：渠道策略、预算建议、投放节奏。
- **Analytics Agent**：受众画像、指标归因、趋势解释。
- **Knowledge Agent**：平台规则、上传规范、FAQ 解释。

> 每个 Specialist 仅绑定自己的工具白名单，防止越权调用。

### 3.4 Critic / Verifier（校验）
- 对 Specialist 产物做一致性与风险检查：
  - 是否与用户目标一致。
  - 是否存在冲突建议。
  - 是否引用了缺失/不可信数据。

### 3.5 Synthesizer（汇总）
- 将多 Agent 输出聚合为统一结果：
  - 结论（可执行项）
  - 证据（来源/工具结果）
  - 风险与下一步建议

## 4. 编排模式建议

### 模式 A：Plan-and-Execute（默认）
1. Planner 拆解任务。
2. Router 分配给 Specialist。
3. 可并行子任务并发执行。
4. Critic 校验。
5. Synthesizer 汇总。

适用：大多数复杂问答与策略生成任务。

### 模式 B：Debate（可选）
- 两个 Specialist（如 Promotion vs Analytics）独立给方案，再由 Critic 投票。
- 适合高风险决策场景（预算分配、发布时间窗口）。

### 模式 C：Reflection（可选）
- 首轮答案生成后由 Critic 触发反思重试。
- 适合准确性要求高的场景。

## 5. 数据与消息协议（关键）

建议在 Agent 间传递结构化 JSON，避免纯文本漂移。

```json
{
  "trace_id": "uuid",
  "user_query": "string",
  "subtasks": [
    {
      "id": "t1",
      "goal": "分析近期热点",
      "required_capability": "trend",
      "depends_on": [],
      "status": "pending"
    }
  ],
  "agent_outputs": [
    {
      "subtask_id": "t1",
      "agent": "trend",
      "result": {"topics": []},
      "confidence": 0.82,
      "evidence": ["tool:get_hot_topics"]
    }
  ]
}
```

## 6. 在当前仓库的落地路径

### Phase 1（最小可用）
- 新增 `server/multi_agent/` 模块：
  - `orchestrator.py`
  - `planner.py`
  - `router.py`
  - `schemas.py`
- 保留现有工具函数不变，通过适配层复用。
- 增加配置开关：`ENABLE_MULTI_AGENT=true/false`。

### Phase 2（并发与可靠性）
- 使用 `asyncio.gather` 并发运行无依赖子任务。
- 加入超时、重试（指数退避）、熔断。
- 增加“降级策略”：某个 Agent 失败时由单 Agent fallback。

### Phase 3（质量与观测）
- 埋点：每个子任务 token 成本、延迟、成功率。
- 记录完整 trace（入参、工具调用、产出、错误）。
- 建立离线评测集，比较单 Agent 与多 Agent 指标。

## 7. 评估指标（上线前必须）

- **任务成功率**：用户问题是否被完整解决。
- **答案一致性**：是否存在自相矛盾。
- **平均响应时延**：P50 / P95。
- **单位请求成本**：token 与外部 API 调用成本。
- **可解释性**：是否能给出证据链。

## 8. 风险与防护

- 提示注入：
  - 对工具输入做过滤与最小权限白名单。
- 幻觉放大：
  - 关键结论必须附带 evidence，缺失则降级表达。
- 并发失控：
  - 限制并发度与子任务数量上限。
- 成本超预算：
  - 加入预算守卫（max_tokens / max_calls / max_time）。

## 9. 推荐技术选型

- 编排层：
  - 当前继续使用 LangChain（成本最低）；
  - 若后续流程更复杂，可评估 LangGraph。
- 观测：
  - OpenTelemetry + 结构化日志（JSON）。
- 队列（可选）：
  - 复杂异步任务接入 Redis + Celery/RQ。

## 10. 一句话结论

先以 **“Orchestrator + 4 Specialist + Critic”** 的轻量 Plan-and-Execute 架构落地，复用现有工具与 API；待稳定后再逐步增加 Debate/Reflection 与更强观测能力，实现质量、时延、成本三者平衡。
