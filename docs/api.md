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

