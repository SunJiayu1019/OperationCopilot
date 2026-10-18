# OperationCopilot

面向内容运营人员的商品与营销素材分析助手。当前完成 Milestone 1：以“小红书 × 零食”为边界，搭建商品图片上传、任务提交、工作流状态和结果展示的基础闭环。

## 当前能力

- 上传 PNG/JPEG/WebP 商品图片，最大 10 MB。
- 提交小红书零食内容任务。
- 展示“素材分析 → 文案生成 → 内容审核 → 自动改写”四个阶段。
- 展示模拟的商品摘要、三版文案、风险提示和自动改写稿。
- 真实 MiniMind-V、Qwen、RAG、ReAct Agent 与平台发布属于后续 Milestone。

## 项目结构

```text
backend/       FastAPI 服务与接口测试
frontend/      React + TypeScript 工作台
docs/          需求、架构、UML、数据结构和 API 设计
```

## 本地启动

### 后端

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 前端

```powershell
cd frontend
npm install
npm run dev
```

浏览器打开 `http://localhost:5173`。前端默认请求 `http://localhost:8000`，可通过 `VITE_API_BASE_URL` 覆盖。

## 测试与构建

```powershell
py -m pytest backend/tests -q
cd frontend
npm test -- --run
npm run build
```

## 文档索引

- [需求说明](docs/requirements.md)
- [系统架构](docs/system-architecture.md)
- [用户流程与 Agent 工作流](docs/user-flow.md)
- [数据结构](docs/data-model.md)
- [Agent 边界设计](docs/agent-workflow.md)
- [API 约定](docs/api.md)
- [Milestone 1 实现计划](docs/superpowers/plans/2026-10-18-milestone-1.md)
