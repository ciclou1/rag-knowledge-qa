"""
文档处理流水线：解析 → 分块 → Embedding → pgvector 存储。
支持从内存内容直接解析（TXT/MD）和从文件路径解析（PDF/DOCX）。
"""
import tempfile
import os
from pathlib import Path
from typing import Optional

from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import SupabaseVectorStore

from app.config import settings
from app.db import get_supabase
from app.services.embeddings import DashScopeEmbeddings


# 需要文件路径的二进制格式
BINARY_LOADERS = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".doc": Docx2txtLoader,
}

# 纯文本格式，直接从内存解析
TEXT_EXTENSIONS = {".txt", ".md", ".markdown"}


def get_embeddings() -> DashScopeEmbeddings:
    """获取 DashScope Embedding 实例。"""
    return DashScopeEmbeddings(
        model=settings.EMBED_MODEL,
        dimensions=settings.EMBED_DIMENSIONS,
    )


def get_splitter() -> RecursiveCharacterTextSplitter:
    """获取文本分块器。"""
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", ".", " "],
    )


def _decode_text(raw: bytes, filename: str) -> str:
    """多编码尝试解码文本内容。"""
    # 编码尝试顺序：UTF-8 → UTF-8-BOM → GBK → GB2312 → Latin-1（兜底）
    for enc in ["utf-8-sig", "utf-8", "gbk", "gb2312", "latin-1"]:
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace")


async def process_document(
    file_path: str,
    kb_id: str,
    filename: str,
    folder: str = "",
    tags: list[str] | None = None,
) -> int:
    """
    处理单个文档：解析、分块、向量化、存储。

    - 纯文本（.txt/.md）：直接从文件读取内容，避免 loader 兼容性问题
    - 二进制（.pdf/.docx）：使用对应的 LangChain Loader

    返回分块数量。
    """
    ext = Path(filename).suffix.lower()

    # 1. 加载文档
    if ext in TEXT_EXTENSIONS:
        # 纯文本：先读原始字节，再尝试多种编码解析
        with open(file_path, "rb") as f:
            raw = f.read()
        content = _decode_text(raw, filename)
        docs = [Document(page_content=content, metadata={"source": filename})]
    elif ext in BINARY_LOADERS:
        loader_cls = BINARY_LOADERS[ext]
        loader = loader_cls(file_path)
        docs = loader.load()
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    # 2. 分块
    splitter = get_splitter()
    chunks = splitter.split_documents(docs)

    # 3. 注入元数据
    for i, chunk in enumerate(chunks):
        chunk.metadata["kb_id"] = kb_id
        chunk.metadata["doc_name"] = filename
        chunk.metadata["folder"] = folder
        chunk.metadata["tags"] = tags or []
        chunk.metadata["chunk_index"] = i

    # 4. Embedding + 写入 pgvector
    embeddings = get_embeddings()
    supabase = get_supabase()

    vectorstore = SupabaseVectorStore(
        embedding=embeddings,
        client=supabase,
        table_name="documents",
        query_name="match_documents",
    )
    vectorstore.add_documents(chunks)

    return len(chunks)


async def delete_document_vectors(doc_name: str, kb_id: str) -> int:
    """删除指定文档的所有向量数据。返回删除行数。"""
    supabase = get_supabase()
    result = (
        supabase.table("documents")
        .delete()
        .eq("doc_name", doc_name)
        .eq("knowledge_base_id", kb_id)
        .execute()
    )
    return len(result.data) if result.data else 0
