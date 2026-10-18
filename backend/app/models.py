from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator


StageName = Literal["material_analysis", "copy_generation", "content_review", "auto_rewrite"]
StageStatus = Literal["pending", "running", "completed", "failed"]


class UploadResponse(BaseModel):
    asset_id: str
    filename: str


class TaskCreate(BaseModel):
    asset_id: str = Field(min_length=1)
    platform: Literal["xiaohongshu"]
    category: Literal["snack"]
    brief: str = Field(min_length=1, max_length=500)

    @field_validator("brief")
    @classmethod
    def brief_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("brief must not be blank")
        return value.strip()


class WorkflowStage(BaseModel):
    stage: StageName
    status: StageStatus
    message: str
    started_at: datetime | None = None
    completed_at: datetime | None = None


class ProductSummary(BaseModel):
    name: str
    category: str
    selling_points: list[str]


class CopyVariant(BaseModel):
    title: str
    body: str
    tags: list[str]


class RiskItem(BaseModel):
    level: Literal["low", "medium", "high"]
    phrase: str
    reason: str
    suggestion: str


class RewrittenCopy(BaseModel):
    title: str
    body: str


class AnalysisResult(BaseModel):
    product_summary: ProductSummary
    copy_variants: list[CopyVariant]
    risks: list[RiskItem]
    rewritten: RewrittenCopy


class TaskSnapshot(BaseModel):
    id: str
    platform: str
    category: str
    brief: str
    status: StageStatus
    created_at: datetime
    stages: list[WorkflowStage]
    result: AnalysisResult | None


def now() -> datetime:
    return datetime.now(timezone.utc)
