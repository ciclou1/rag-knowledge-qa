-- 001_init.sql: 初始化 schema
-- 在 Supabase SQL Editor 中执行此脚本

-- 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- ─────────────────────────────────────
-- 知识库表
-- ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS knowledge_bases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT DEFAULT '',
    is_public BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────
-- 文档分块表（含向量）
-- ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_base_id UUID REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    doc_name VARCHAR(500),
    content TEXT NOT NULL,
    folder VARCHAR(255) DEFAULT '',
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    embedding VECTOR(1536),
    chunk_index INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 余弦相似度检索索引（IVFFlat）
CREATE INDEX IF NOT EXISTS idx_documents_embedding
    ON documents
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- 按知识库查询的普通索引
CREATE INDEX IF NOT EXISTS idx_documents_kb_id
    ON documents (knowledge_base_id);

-- ─────────────────────────────────────
-- 检索匹配函数（供 LangChain 调用）
-- ─────────────────────────────────────
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding VECTOR(1536),
    match_count INT DEFAULT 20,
    filter_kb_id UUID DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    knowledge_base_id UUID,
    doc_name VARCHAR(500),
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.id,
        d.knowledge_base_id,
        d.doc_name,
        d.content,
        d.metadata,
        1 - (d.embedding <=> query_embedding) AS similarity
    FROM documents d
    WHERE
        (filter_kb_id IS NULL OR d.knowledge_base_id = filter_kb_id)
        AND d.embedding IS NOT NULL
    ORDER BY d.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ─────────────────────────────────────
-- 多知识库联合检索函数
-- ─────────────────────────────────────
CREATE OR REPLACE FUNCTION match_documents_multi_kb(
    query_embedding VECTOR(1536),
    match_count INT DEFAULT 20,
    filter_kb_ids UUID[] DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    knowledge_base_id UUID,
    doc_name VARCHAR(500),
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.id,
        d.knowledge_base_id,
        d.doc_name,
        d.content,
        d.metadata,
        1 - (d.embedding <=> query_embedding) AS similarity
    FROM documents d
    WHERE
        (filter_kb_ids IS NULL OR d.knowledge_base_id = ANY(filter_kb_ids))
        AND d.embedding IS NOT NULL
    ORDER BY d.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
