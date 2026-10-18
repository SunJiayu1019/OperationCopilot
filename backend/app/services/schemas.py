from typing import Literal

from pydantic import BaseModel, Field


class VisualAnalysis(BaseModel):
    product_name: str
    category: str
    colors: list[str]
    materials: list[str]
    scene: str
    selling_points: list[str]
    visible_text: list[str]
    risks: list[str]
    page_layout: str = "unknown"
    visual_style: str = "unknown"


class SummaryResult(BaseModel):
    summary: str
    evidence: list[str]


class CopyItem(BaseModel):
    title: str
    body: str
    tags: list[str]


class CopyResult(BaseModel):
    copy_variants: list[CopyItem] = Field(min_length=3, max_length=3)


class ReviewItem(BaseModel):
    phrase: str
    level: Literal["low", "medium", "high"]
    reason: str
    suggestion: str


class ReviewResult(BaseModel):
    risks: list[ReviewItem]


class RewriteResult(BaseModel):
    title: str = Field(min_length=1)
    body: str = Field(min_length=1)
