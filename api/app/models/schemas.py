"""
Pydantic 请求/响应模型。
"""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


# ── 知识库 ──

class KnowledgeBaseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    is_public: bool = True


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None


class KnowledgeBaseOut(BaseModel):
    id: str
    name: str
    description: str
    is_public: bool
    created_at: datetime
    updated_at: datetime
    document_count: int = 0


# ── 文档 ──

class DocumentOut(BaseModel):
    id: str
    knowledge_base_id: str
    doc_name: str
    folder: str = ""
    tags: list[str] = []
    chunks: int = 0
    created_at: datetime


class DocumentUploadResult(BaseModel):
    doc_id: str
    name: str
    chunks: int
    status: str


# ── 问答 ──

class Source(BaseModel):
    doc_name: str
    content_snippet: str
    relevance_score: float


class QARequest(BaseModel):
    question: str = Field(..., min_length=1)
    kb_ids: list[str] = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class QAResponse(BaseModel):
    answer: str
    sources: list[Source]
    confidence: str = "medium"  # high / medium / low


# ── 通用 ──

class ErrorResponse(BaseModel):
    detail: str
