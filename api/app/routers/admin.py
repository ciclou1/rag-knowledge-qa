"""
管理后台 API：知识库 CRUD、文档管理。
"""
import os
import tempfile
import traceback
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status

logger = logging.getLogger(__name__)

from app.config import settings
from app.db import get_supabase
from app.middleware import verify_admin_key
from app.models.schemas import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseOut,
    DocumentOut,
    DocumentUploadResult,
)
from app.services.document_processor import process_document, delete_document_vectors
from app.services.cos_service import cos_service

router = APIRouter(dependencies=[Depends(verify_admin_key)])


# ═══════════════════════════════════════════
# 知识库 CRUD
# ═══════════════════════════════════════════

@router.post("/knowledge-bases", status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(body: KnowledgeBaseCreate):
    """创建知识库。"""
    supabase = get_supabase()
    now = datetime.now(timezone.utc).isoformat()
    result = (
        supabase.table("knowledge_bases")
        .insert({
            "name": body.name,
            "description": body.description,
            "is_public": body.is_public,
            "created_at": now,
            "updated_at": now,
        })
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create knowledge base")
    return result.data[0]


@router.get("/knowledge-bases")
async def list_knowledge_bases():
    """获取所有知识库列表（含文档数量）。"""
    supabase = get_supabase()
    result = supabase.table("knowledge_bases").select("*").execute()

    kbs = []
    for row in (result.data or []):
        # 统计文档数量
        count_result = (
            supabase.table("documents")
            .select("id", count="exact")
            .eq("knowledge_base_id", row["id"])
            .execute()
        )
        row["document_count"] = count_result.count if count_result.count else 0
        kbs.append(row)

    return kbs


@router.get("/knowledge-bases/{kb_id}")
async def get_knowledge_base(kb_id: str):
    """获取单个知识库详情。"""
    supabase = get_supabase()
    result = supabase.table("knowledge_bases").select("*").eq("id", kb_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    row = result.data[0]
    count_result = (
        supabase.table("documents")
        .select("id", count="exact")
        .eq("knowledge_base_id", kb_id)
        .execute()
    )
    row["document_count"] = count_result.count if count_result.count else 0
    return row


@router.put("/knowledge-bases/{kb_id}")
async def update_knowledge_base(kb_id: str, body: KnowledgeBaseUpdate):
    """编辑知识库。"""
    supabase = get_supabase()
    updates = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if body.name is not None:
        updates["name"] = body.name
    if body.description is not None:
        updates["description"] = body.description
    if body.is_public is not None:
        updates["is_public"] = body.is_public

    result = (
        supabase.table("knowledge_bases")
        .update(updates)
        .eq("id", kb_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return result.data[0]


@router.delete("/knowledge-bases/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(kb_id: str):
    """删除知识库（级联删除所有文档和向量）。"""
    supabase = get_supabase()
    supabase.table("knowledge_bases").delete().eq("id", kb_id).execute()


# ═══════════════════════════════════════════
# 文档管理
# ═══════════════════════════════════════════

@router.post("/knowledge-bases/{kb_id}/documents")
async def upload_document(
    kb_id: str,
    file: UploadFile = File(...),
    folder: str = Form(default=""),
    tags: str = Form(default=""),
):
    """上传文档并触发处理流水线。"""
    # 校验文件大小
    if file.size and file.size > settings.UPLOAD_MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max {settings.UPLOAD_MAX_SIZE_MB}MB",
        )

    # 校验知识库存在
    supabase = get_supabase()
    kb = supabase.table("knowledge_bases").select("id").eq("id", kb_id).execute()
    if not kb.data:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    # 保存到临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # 上传到 COS（或本地）
        cos_service.upload_document(tmp_path, kb_id, file.filename or "unknown")

        # 文档处理流水线
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        chunks = await process_document(
            file_path=tmp_path,
            kb_id=kb_id,
            filename=file.filename or "unknown",
            folder=folder,
            tags=tag_list,
        )

        return DocumentUploadResult(
            doc_id=kb_id,
            name=file.filename or "unknown",
            chunks=chunks,
            status="completed",
        )
    except Exception as e:
        logger.error(f"Document processing failed: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Document processing failed: {str(e)}",
        )
    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.get("/knowledge-bases/{kb_id}/documents")
async def list_documents(kb_id: str, search: str = "", page: int = 1, size: int = 20):
    """文档列表。按文档名去重聚合，统计分块数。"""
    supabase = get_supabase()

    # 全量查询，在 Python 中按 kb_id 过滤（kb_id 存在 metadata JSONB 中）
    result = (
        supabase.table("documents")
        .select("id,doc_name,metadata,folder,tags,created_at")
        .order("created_at", desc=True)
        .execute()
    )

    # 按 kb_id 过滤 + 搜索过滤
    rows = result.data or []
    rows = [
        r for r in rows
        if (r.get("metadata") or {}).get("kb_id") == kb_id
    ]
    if search:
        rows = [
            r for r in rows
            if search.lower() in (r.get("doc_name") or r.get("metadata", {}).get("doc_name", "") or "").lower()
        ]

    # 分页
    total = len(rows)
    offset = (page - 1) * size
    rows = rows[offset:offset + size]

    # 聚合：按 doc_name 合并，计算 chunks（从 metadata 中取 doc_name 作为备用）
    docs = {}
    for row in rows:
        name = row.get("doc_name") or (row.get("metadata") or {}).get("doc_name") or "未知文档"
        if name not in docs:
            row["doc_name"] = name
            row["chunks"] = 1
            docs[name] = row
        else:
            docs[name]["chunks"] += 1

    return {
        "items": list(docs.values()),
        "total": total,
        "page": page,
        "size": size,
    }


@router.delete("/documents/{doc_name:path}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(doc_name: str, kb_id: str = ""):
    """删除指定文档（所有分块+向量）。"""
    supabase = get_supabase()
    query = supabase.table("documents").delete().eq("doc_name", doc_name)
    if kb_id:
        query = query.eq("knowledge_base_id", kb_id)

    result = query.execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Document not found")
