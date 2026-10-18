# Milestone 1 API 约定

## `POST /api/uploads`

`multipart/form-data`，字段 `file`。允许 `image/png`、`image/jpeg`、`image/webp`，大小不超过 10 MB。

响应：`{ "asset_id": "asset_xxx", "filename": "snack.jpg" }`

## `POST /api/tasks`

```json
{"asset_id":"asset_xxx","platform":"xiaohongshu","category":"snack","brief":"突出下午茶和便携"}
```

响应：完整任务快照，包含 `id`、`status`、`stages`、`result`。

## `GET /api/tasks/{task_id}`

响应：与创建任务相同的任务快照。未知任务返回 `404` 和 `{ "detail": "Task not found" }`。

## 错误处理

校验错误使用 FastAPI 标准 `422`；文件类型或大小错误使用 `400`；任务不存在使用 `404`。错误消息面向用户，前端在关联控件附近展示恢复建议。

## Milestone 2 验证接口

以下接口独立于 Milestone 1 的模拟任务流程。它们用于分别验证视觉模型、文本模型和 RAG；完整 Agent 编排属于 Milestone 3。

### `POST /api/analysis/visual`

```json
{"asset_id":"asset_xxx","material_type":"product"}
```

`material_type` 可选 `product`、`detail`、`competitor`。先通过 `/api/uploads` 获取 `asset_id`。返回 `material_type` 和 `analysis`，后者包含 `product_name`、`category`、`colors`、`materials`、`scene`、`selling_points`、`visible_text`、`risks`、`page_layout`、`visual_style`、`raw_description`。模型首次调用会加载本地权重；CPU 可能较慢。模型输出不成结构时用 Qwen 整理，未配置密钥返回 `503`。

### `POST /api/text/generate`

```json
{"task":"copy","content":"海盐坚果脆，突出下午茶场景","context":"品牌规范：避免绝对化表述"}
```

`task` 为 `summary`、`copy` 或 `review`；分别返回 `summary/evidence`、三版 `copy_variants`、`risks`。Qwen 经 DashScope OpenAI 兼容接口调用，需配置 `DASHSCOPE_API_KEY`。

### `POST /api/rag/index`

无需请求体。重新读取 `backend/knowledge/` 四个集合并构建进程内 TF-IDF 索引；响应包含每个集合和总切片数。重建会替换旧索引，服务重启后需再次调用。

### `POST /api/rag/ask`

```json
{"question":"小红书零食文案应避免哪些表达？","collection":"platform","top_k":3}
```

`collection` 可省略，范围为 `product/brand/platform/cases`；`top_k` 范围 1-10。返回 `answer` 和 `evidence`，每条证据包含 `text/source/collection/score/heading`。无匹配时返回空证据、`answer: null`，不会调用 Qwen。若有匹配则需密钥才能验证问答。

### `POST /api/rag/query`

请求体与 `/api/rag/ask` 相同，返回 `{ "hits": [...] }`。只执行本地向量检索，不调用 Qwen；用于验证四类知识库的切分、命中、来源和相似度。先调用 `/api/rag/index`。

### 错误码

参数校验 `422`，未知素材 `404`，非法图像 `400`，模型未配置 `503`，模型结构化输出不合契约 `502`。

