from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    AnalysisResult,
    CopyVariant,
    ProductSummary,
    RewrittenCopy,
    RiskItem,
    TaskCreate,
    TaskSnapshot,
    UploadResponse,
    WorkflowStage,
    now,
)


app = FastAPI(title="OperationCopilot API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "tmp_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED_TYPES = {"image/png", "image/jpeg", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024
assets: dict[str, dict[str, str]] = {}
tasks: dict[str, TaskSnapshot] = {}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/uploads", response_model=UploadResponse)
async def upload_asset(file: UploadFile = File(...)) -> UploadResponse:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only PNG, JPEG, and WebP image files are supported")
    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Image file must be 10 MB or smaller")
    asset_id = f"asset_{uuid4().hex[:10]}"
    filename = Path(file.filename or "upload").name
    (UPLOAD_DIR / asset_id).write_bytes(data)
    assets[asset_id] = {"filename": filename, "content_type": file.content_type}
    return UploadResponse(asset_id=asset_id, filename=filename)


def build_result(brief: str) -> AnalysisResult:
    return AnalysisResult(
        product_summary=ProductSummary(
            name="海盐坚果脆（演示商品）",
            category="零食",
            selling_points=["酥脆口感", "便携包装", "适合办公和下午茶场景"],
        ),
        copy_variants=[
            CopyVariant(title="办公室抽屉里的酥脆补给", body=f"把下午茶的期待，交给这一口轻松的酥脆。{brief}。", tags=["#办公室零食", "#下午茶"]),
            CopyVariant(title="通勤包里的一小袋快乐", body="小包装方便随身带，忙碌间隙也能给自己留一点好吃的时间。", tags=["#通勤好物", "#零食分享"]),
            CopyVariant(title="越嚼越香的日常小确幸", body="咸香坚果搭配轻盈口感，适合和朋友分享，也适合独享。", tags=["#解馋零食", "#日常好物"]),
        ],
        risks=[
            RiskItem(level="medium", phrase="0添加", reason="当前商品资料未提供足够证据支撑绝对化描述", suggestion="改为配料表可核验的具体表述"),
        ],
        rewritten=RewrittenCopy(title="一口酥脆的办公间隙", body="便携小包装，适合放进通勤包或办公抽屉，在下午茶和短暂休息时分享一份咸香酥脆。"),
    )


def build_stages() -> list[WorkflowStage]:
    messages = {
        "material_analysis": "已完成商品图片基础属性识别",
        "copy_generation": "已生成 3 版小红书候选文案",
        "content_review": "已完成平台表达风险检查",
        "auto_rewrite": "已根据风险建议生成合规版本",
    }
    names = ["material_analysis", "copy_generation", "content_review", "auto_rewrite"]
    return [WorkflowStage(stage=name, status="completed", message=messages[name], started_at=now(), completed_at=now()) for name in names]


@app.post("/api/tasks", response_model=TaskSnapshot, status_code=201)
def create_task(payload: TaskCreate) -> TaskSnapshot:
    if payload.asset_id not in assets:
        raise HTTPException(status_code=404, detail="Asset not found")
    task = TaskSnapshot(
        id=f"task_{uuid4().hex[:10]}",
        platform=payload.platform,
        category=payload.category,
        brief=payload.brief,
        status="completed",
        created_at=now(),
        stages=build_stages(),
        result=build_result(payload.brief),
    )
    tasks[task.id] = task
    return task


@app.get("/api/tasks/{task_id}", response_model=TaskSnapshot)
def get_task(task_id: str) -> TaskSnapshot:
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
