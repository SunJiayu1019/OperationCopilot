# OperationCopilot

面向内容运营人员的商品与营销素材分析助手。当前完成 Milestone 3：以“小红书 × 零食”为范围，提供 MiniMind-V、Qwen、RAG 和有界 ReAct Agent 组成的图片到文案闭环，并在 React 工作台展示工具状态与多版本文案。

## 当前能力

- 上传 PNG/JPEG/WebP 商品图片，最大 10 MB。
- 提交小红书零食内容任务。
- 展示“素材分析 → 文案生成 → 内容审核 → 自动改写”四个阶段。
- 展示模拟的商品摘要、三版文案、风险提示和自动改写稿。
- MiniMind-V 封装本地权重，对商品图、详情页截图和竞品图进行视觉描述与结构化提取。
- Qwen 封装商品总结、三版小红书文案生成、内容审核。
- 四类演示知识库（商品、品牌、平台、案例），Markdown 切分、TF-IDF 向量化与检索，RAG 问答验证接口。
- ReAct Agent：图片分析、知识检索、文案生成、内容审核、文案改写五类注册工具。
- 对话任务 API：后台执行、状态轮询、结构化观察结果和失败状态。
- 前端对话工作台：Agent 执行状态、三版文案对比和审核结果展示。

## 项目结构

```text
backend/       FastAPI 服务与接口测试
frontend/      React + TypeScript 工作台
docs/          需求、架构、UML、数据结构和 API 设计
minimind-v/    用户提供的第三方 MiniMind-V 源码和本地权重
```

## 本地启动

### 后端

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DASHSCOPE_API_KEY="你的密钥"
# 可选：$env:QWEN_MODEL="qwen-plus"
# 可选：$env:QWEN_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
# 可选：$env:MINIMIND_DEVICE="cuda"  （默认 cpu）
uvicorn app.main:app --reload --port 8000
```

也可以在 `backend/.env` 中设置 `DASHSCOPE_API_KEY=...`，然后用 `uvicorn app.main:app --reload --env-file .env --port 8000` 启动；不要提交 `.env` 或把密钥写进前端。适配器严格读取 `DASHSCOPE_API_KEY`，不会自动把 `LLM_API_KEY` 当作 DashScope 密钥。

### 前端

```powershell
cd frontend
npm install
npm run dev
```

浏览器打开 `http://localhost:5173`。前端默认请求 `http://localhost:8000`，可通过 `VITE_API_BASE_URL` 覆盖。

MiniMind-V 需要 `minimind-v/model/siglip2-base-p32-256-ve/`、`minimind-v/model/tokenizer.json`、`minimind-v/out/sft_vlm_768.pth`。首次视觉请求加载模型，CPU 推理可能较慢；模型可能给出自然语言而非严格 JSON，此时使用 Qwen 整理为结构化结果。当前知识库内容均为明确标注的虚构演示样例，不是官方规则或真实商品资料，发布前须核实。不要将密钥写入仓库。

### Milestone 2 快速验证

启动后端后调用 `POST http://localhost:8000/api/rag/index`（无请求体），再通过 `/docs` 中的 `POST /api/rag/query` 提交（无需 Qwen 密钥）：

```json
{"question":"小红书零食文案需要避免什么表达？","collection":"platform","top_k":3}
```

`/api/rag/query` 返回匹配文本、来源和相似度；配置密钥后可用相同请求体调用 `/api/rag/ask` 验证检索增强问答。文本模型接口 `/api/text/generate` 可选择 `summary`、`copy`、`review`。视觉接口需先上传真实图片到 `/api/uploads`，再将返回的 `asset_id` 提交到 `/api/analysis/visual`。详细请求和响应见 [API 约定](docs/api.md)。未配置 Qwen 密钥时模型调用返回 `503`，RAG 索引与直接检索仍可使用。

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
- [Milestone 2 设计说明](docs/superpowers/specs/2026-10-18-milestone-2-design.md)
- [Milestone 2 UML](docs/milestone-2-uml.md)
- [Prompt 设计](docs/prompts.md)
- [RAG 知识库](docs/rag-knowledge-base.md)
- [Milestone 3 设计说明](docs/superpowers/specs/2026-10-18-milestone-3-design.md)
- [Milestone 3 实现计划](docs/superpowers/plans/2026-10-18-milestone-3.md)
- [Milestone 3 UML](docs/milestone-3-uml.md)
