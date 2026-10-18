# 系统架构设计

## 1. 架构目标

以最小可运行闭环验证业务流程，同时把模型适配、任务编排和结果结构隔离出来，方便 Milestone 2 接入 MiniMind-V/Qwen/RAG，Milestone 3 接入 ReAct Agent。

## 2. 分层架构

```mermaid
flowchart LR
    U[内容运营人员] --> FE[React 前端工作台]
    FE --> API[FastAPI HTTP API]
    API --> FS[本地临时文件存储]
    API --> TS[任务服务 / 内存仓储]
    TS --> WF[Workflow Adapter 模拟工作流]
    WF -. Milestone 2 .-> V[MiniMind-V 视觉分析]
    WF -. Milestone 2 .-> R[RAG 检索服务]
    WF -. Milestone 2 .-> Q[Qwen 文案与审核]
    WF -. Milestone 3 .-> A[ReAct Agent 编排]
    WF --> DTO[结构化任务结果]
    DTO --> FE
```

## 3. 当前阶段模块职责

| 模块 | 职责 | 当前实现 |
| --- | --- | --- |
| 前端工作台 | 上传、提交、状态与结果展示 | React 单页 |
| HTTP API | 文件与任务接口、参数校验 | FastAPI |
| Task Service | 生成任务、更新阶段、读取结果 | 内存字典 |
| Workflow Adapter | 生成可演示的阶段结果 | Deterministic mock |
| Model/RAG/Agent | 真实智能能力 | 仅保留接口边界 |

## 4. 部署视图

```mermaid
flowchart TB
    Browser[浏览器] --> Frontend[localhost:5173 Vite dev server]
    Frontend --> Backend[localhost:8000 FastAPI]
    Backend --> Uploads[(临时上传目录)]
    Backend --> Memory[(进程内任务仓储)]
```

生产化时需要替换临时目录、内存仓储、CORS 配置和模拟工作流；本阶段刻意不提前引入数据库、消息队列和鉴权。

