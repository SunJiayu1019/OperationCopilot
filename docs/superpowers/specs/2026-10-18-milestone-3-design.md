# Milestone 3 Design

## Intent and boundary

For Xiaohongshu snack content operators, turn an uploaded image and a short instruction into inspectable product facts, retrieved evidence, three candidate drafts, risk findings and a revised draft. Also support image-only analysis, knowledge questions, and copy review in the same conversation surface. No platform publishing, accounts, deployment or production observability.

## Architecture

`POST /api/chat/tasks` accepts a message and optional uploaded asset id, returns an in-memory task id immediately. A background worker runs an at-most-six-action ReAct loop: Qwen selects an intent and then selects the next registered tool based on prior observations; the controller checks prerequisites, records public tool status, and rejects unknown, repeated or out-of-order actions. `GET /api/chat/tasks/{id}` provides polling snapshots. A failure is terminal and visible; there is no simulated fallback. Tasks and uploaded assets are process-local, so restart loses them.

Registered tools are `analyze_image`, `search_knowledge`, `generate_copy`, `review_copy`, `rewrite_copy`. The image tool uses the existing MiniMind-V adapter with Qwen structuring when needed. Search uses the existing four-collection TF-IDF index, initialized lazily from local Markdown. Text work uses Qwen; evidence and user content are data, not instructions. The rewrite is a separate JSON-validated Qwen call. For a full workflow the action order is image, search, generate, review, rewrite. A knowledge question uses search and a grounded answer call. Review-only uses review and optional rewrite. Image-only analyzes and responds with facts.

## Data and UX

Task snapshot: id, intent, status, message, asset_id, steps (tool/status/message/timestamps), observations (typed tool results), answer, error. The client polls while running, renders tool progress and evidence, and compares the three generated drafts side by side with risk and revised copy. The image is optional for knowledge/review queries and required for image tasks; errors remain visible with a retry path. No model chain-of-thought is stored or displayed; only tool names and brief operational messages.

## Error policy

Invalid requests 422, unknown assets/tasks 404, malformed images 400 before model loading. Missing configuration and unavailable local weights fail the task with a clear message; malformed model JSON fails the task rather than using demo data. Never expose API keys or raw exception traces to the UI. The Qwen key is `DASHSCOPE_API_KEY` in the backend process environment. User-supplied `LLM_API_KEY` is not implicitly treated as DashScope credentials.

## Builder calls

Reuse React/Vite and FastAPI/Pydantic and existing service adapters. Avoid extra orchestration packages and persist nothing beyond the process for this milestone. Use a compact operational layout, preserving the current light green/ink identity rather than adopting the marketing hero recommended by the generic UI search.
