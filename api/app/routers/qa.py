"""
问答 API：公开访问，无需认证。
"""
from fastapi import APIRouter, HTTPException

from app.db import get_supabase
from app.models.schemas import QARequest, QAResponse, Source
from app.services.qa_engine import search_and_generate

router = APIRouter()


@router.get("/knowledge-bases")
async def list_public_knowledge_bases():
    """返回所有公开知识库列表，供问答页面选择。"""
    supabase = get_supabase()
    result = (
        supabase.table("knowledge_bases")
        .select("*")
        .eq("is_public", True)
        .execute()
    )
    return result.data or []


@router.post("/ask", response_model=QAResponse)
async def ask_question(body: QARequest):
    """问答接口：检索知识库并生成回答。"""
    try:
        result = await search_and_generate(
            question=body.question,
            kb_ids=body.kb_ids,
            top_k=body.top_k,
        )
        return QAResponse(
            answer=result["answer"],
            sources=[
                Source(
                    doc_name=s["doc_name"],
                    content_snippet=s["content_snippet"],
                    relevance_score=s["relevance_score"],
                )
                for s in result["sources"]
            ],
            confidence=result["confidence"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"QA engine error: {str(e)}",
        )
