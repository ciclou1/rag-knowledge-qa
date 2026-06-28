"""
问答引擎：向量检索 → BM25 兜底 → LLM 生成。
三级检索策略：
  1. pgvector 语义向量检索
  2. BM25 全文关键词检索（兜底）
  3. 大模型直接生成“未找到”提示（最终兜底）
"""
import logging
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.documents import Document

from app.config import settings
from app.db import get_supabase
from app.services.embeddings import DashScopeEmbeddings
from app.services.reranker.provider import get_reranker, RerankResult

logger = logging.getLogger(__name__)

# ── Prompt 模板 ──

RAG_SYSTEM_PROMPT = """你是一个专业的知识问答助手。请严格根据以下提供的知识库内容回答问题。
如果知识库内容不足以回答问题，请明确回复「根据现有知识，我无法回答这个问题」，不要编造或猜测。

参考知识（来自知识库）：
{context}

指令：
- 优先使用上述参考知识中的信息回答
- 回答末尾附上引用来源（文档名 + 片段摘要）
- 回答简洁准确，避免冗余
- 如果参考知识不包含答案，明确说明
"""

NOT_FOUND_PROMPT = """用户提出了一个问题，但知识库中没有搜索到任何相关知识。

请礼貌地告知用户：知识库中没有搜索到与问题相关的知识内容，建议用户：
1. 检查问题表述是否准确
2. 尝试使用更通用的关键词提问
3. 联系管理员补充相关文档到知识库

用户问题：{question}"""


def _get_embeddings() -> DashScopeEmbeddings:
    return DashScopeEmbeddings(
        model=settings.EMBED_MODEL,
        dimensions=settings.EMBED_DIMENSIONS,
    )


def _get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.DEEPSEEK_CHAT_MODEL,
        openai_api_base=settings.DEEPSEEK_BASE_URL,
        openai_api_key=settings.DEEPSEEK_API_KEY,
        temperature=0.3,
        max_tokens=2048,
    )


def _build_docs_from_rows(rows: list[dict]) -> list[tuple[Document, float]]:
    """将 Supabase 返回的行转为 (Document, score) 列表，低于阈值过滤。"""
    docs_with_scores = []
    for row in rows:
        similarity = row.get("similarity", 0)
        if similarity >= settings.SIMILARITY_THRESHOLD:
            doc = Document(
                page_content=row["content"],
                metadata={
                    "id": row["id"],
                    "kb_id": str(row.get("knowledge_base_id", "")),
                    "doc_name": row.get("doc_name", ""),
                    "similarity": similarity,
                },
            )
            docs_with_scores.append((doc, similarity))
    return docs_with_scores


# ═══════════════════════════════════════════
# 三级检索
# ═══════════════════════════════════════════

async def _vector_search(
    question: str, kb_ids: list[str], top_n: int
) -> Optional[list[tuple[Document, float]]]:
    """一级检索：pgvector 语义向量检索。"""
    embeddings = _get_embeddings()
    supabase = get_supabase()
    query_vector = embeddings.embed_query(question)

    if len(kb_ids) == 1:
        resp = supabase.rpc("match_documents", {
            "query_embedding": query_vector,
            "match_count": top_n,
            "filter_kb_id": kb_ids[0],
        }).execute()
    else:
        resp = supabase.rpc("match_documents_multi_kb", {
            "query_embedding": query_vector,
            "match_count": top_n,
            "filter_kb_ids": kb_ids,
        }).execute()

    rows = resp.data or []
    docs = _build_docs_from_rows(rows)
    if docs:
        logger.info(f"Vector search: {len(docs)} results")
    return docs if docs else None


async def _bm25_search(
    question: str, kb_ids: list[str], top_n: int
) -> Optional[list[tuple[Document, float]]]:
    """二级兜底：BM25 全文关键词检索。"""
    supabase = get_supabase()

    if len(kb_ids) == 1:
        resp = supabase.rpc("match_documents_bm25", {
            "query_text": question,
            "match_count": top_n,
            "filter_kb_id": kb_ids[0],
        }).execute()
    else:
        resp = supabase.rpc("match_documents_bm25_multi_kb", {
            "query_text": question,
            "match_count": top_n,
            "filter_kb_ids": kb_ids,
        }).execute()

    rows = resp.data or []
    docs = _build_docs_from_rows(rows)
    if docs:
        logger.info(f"BM25 search: {len(docs)} results (vector fallback)")
    return docs if docs else None


async def _generate_not_found(question: str) -> dict:
    """三级兜底：大模型生成“未找到”提示。"""
    llm = _get_llm()
    prompt = NOT_FOUND_PROMPT.format(question=question)
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": question},
    ]
    response = await llm.ainvoke(messages)
    logger.info("Generated 'not found' response via LLM")
    return {
        "answer": response.content,
        "sources": [],
        "confidence": "low",
    }


# ═══════════════════════════════════════════
# Rerank + 生成
# ═══════════════════════════════════════════

async def _rerank_and_generate(
    question: str,
    docs_with_scores: list[tuple[Document, float]],
    top_k: int,
) -> dict:
    """对检索结果 Rerank 精排后生成回答。"""
    docs = [doc for doc, _ in docs_with_scores]
    doc_texts = [doc.page_content for doc in docs]

    # ── Rerank ──
    try:
        reranker = get_reranker()
        rerank_results = await reranker.rerank(question, doc_texts, top_k=top_k)
        logger.info(f"Rerank: {len(rerank_results)} results")
    except Exception as e:
        logger.warning(f"Rerank failed, using top-K: {e}")
        docs = docs[:top_k]
        rerank_results = [
            RerankResult(i, docs_with_scores[i][1]) for i in range(min(len(docs), top_k))
        ]

    # 过滤低分
    if not rerank_results or rerank_results[0].relevance_score < settings.RERANK_SCORE_THRESHOLD:
        return await _generate_not_found(question)

    # 按 rerank 排序取最终 docs
    reranked_docs = [docs[r.index] for r in rerank_results if r.index < len(docs)]

    # ── 组装 Prompt ──
    context_parts = []
    for i, doc in enumerate(reranked_docs):
        doc_name = doc.metadata.get("doc_name", "未知文档")
        context_parts.append(f"[片段{i+1} | 来源: {doc_name}]\n{doc.page_content}")

    context = "\n\n---\n\n".join(context_parts)
    prompt = RAG_SYSTEM_PROMPT.format(context=context)

    # ── LLM 生成 ──
    llm = _get_llm()
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": question},
    ]
    response = await llm.ainvoke(messages)
    answer = response.content

    # ── 组装来源 ──
    sources = []
    for i, r in enumerate(rerank_results[:top_k]):
        if r.index < len(docs):
            doc = docs[r.index]
            snippet = doc.page_content[:200].replace("\n", " ")
            sources.append({
                "doc_name": doc.metadata.get("doc_name", "未知文档"),
                "content_snippet": snippet + ("..." if len(doc.page_content) > 200 else ""),
                "relevance_score": round(r.relevance_score, 4),
            })

    max_score = rerank_results[0].relevance_score if rerank_results else 0
    if max_score >= 0.7:
        confidence = "high"
    elif max_score >= settings.RERANK_SCORE_THRESHOLD:
        confidence = "medium"
    else:
        confidence = "low"

    return {"answer": answer, "sources": sources, "confidence": confidence}


# ═══════════════════════════════════════════
# 主入口：三级兜底
# ═══════════════════════════════════════════

async def search_and_generate(
    question: str,
    kb_ids: list[str],
    top_k: int = 5,
) -> dict:
    """
    完整问答流程（三级检索兜底）：

    1. 向量检索 → 成功则 Rerank + 生成
    2. BM25 全文检索 → 成功则 Rerank + 生成
    3. 大模型直接生成“知识库中没有搜索到相关知识”提示
    """
    # ── 一级：向量检索 ──
    docs = await _vector_search(question, kb_ids, settings.RETRIEVAL_TOP_N)
    search_method = "vector"

    # ── 二级：BM25 全文兜底 ──
    if not docs:
        docs = await _bm25_search(question, kb_ids, settings.RETRIEVAL_TOP_N)
        search_method = "bm25"

    # ── 三级：大模型兜底 ──
    if not docs:
        logger.info("Both vector and BM25 returned empty, using LLM fallback")
        result = await _generate_not_found(question)
        result["search_method"] = "llm_fallback"
        return result

    # ── Rerank + 生成 ──
    result = await _rerank_and_generate(question, docs, top_k)
    result["search_method"] = search_method
    return result
