# Milestone 3 UML

## Component diagram

```mermaid
flowchart LR
  UI[React 对话工作台] -->|上传/提交/轮询| API[FastAPI Chat API]
  API --> Agent[Bounded ReAct Agent]
  Agent --> Registry[ToolRegistry]
  Registry --> Vision[MiniMind-V 图片分析]
  Registry --> RAG[TF-IDF 知识检索]
  Registry --> Qwen[Qwen 文本模型]
  RAG --> KB[(商品/品牌/平台/案例 Markdown)]
  Agent --> Snapshot[(进程内任务快照)]
  API --> Snapshot
```

## Sequence: full campaign

```mermaid
sequenceDiagram
  actor Operator as 运营人员
  participant UI
  participant API
  participant Agent
  participant Tools
  Operator->>UI: 选择商品图，输入内容目标
  UI->>API: POST /api/uploads
  UI->>API: POST /api/chat/tasks
  API-->>UI: 202 task pending
  API->>Agent: 后台执行
  Agent->>Tools: analyze_image
  Tools-->>Agent: 结构化商品属性
  Agent->>Tools: search_knowledge
  Tools-->>Agent: 证据片段
  Agent->>Tools: generate_copy
  Tools-->>Agent: 三版候选文案
  Agent->>Tools: review_copy
  Tools-->>Agent: 风险项
  Agent->>Tools: rewrite_copy
  Tools-->>Agent: 合规改写稿
  loop 直到完成或失败
    UI->>API: GET /api/chat/tasks/{id}
    API-->>UI: steps + observations + status
  end
  UI-->>Operator: 状态、证据、版本对比和风险
```

## Tool state machine

```mermaid
stateDiagram-v2
  [*] --> pending
  pending --> running: background worker starts
  running --> running: tool completed / next tool
  running --> completed: required sequence done
  running --> failed: invalid selection, config, model or tool error
  completed --> [*]
  failed --> [*]
```

工具顺序由意图决定：campaign = image → search → generate → review → rewrite；knowledge = search；visual = image；review = review → rewrite。Agent 不存储或展示模型内部推理，只返回工具状态和业务观察结果。
