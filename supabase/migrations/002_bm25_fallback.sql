-- 002_bm25_fallback.sql: BM25 全文检索兜底机制
-- 在 Supabase SQL Editor 中执行此脚本

-- 1. 添加 tsvector 列（中文使用 simple 配置，支持中英文混合）
ALTER TABLE documents ADD COLUMN IF NOT EXISTS tsv TSVECTOR;

-- 2. 创建 GIN 索引加速全文搜索
CREATE INDEX IF NOT EXISTS idx_documents_tsv
    ON documents USING GIN (tsv);

-- 3. 更新现有数据：为已有文档生成 tsvector
UPDATE documents
SET tsv = to_tsvector('simple', COALESCE(content, ''))
WHERE tsv IS NULL;

-- 4. 创建自动更新 tsvector 的触发器函数
CREATE OR REPLACE FUNCTION documents_tsv_trigger() RETURNS TRIGGER AS $$
BEGIN
    NEW.tsv = to_tsvector('simple', COALESCE(NEW.content, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 5. 创建触发器（先删除再创建，避免重复）
DROP TRIGGER IF EXISTS trg_documents_tsv ON documents;
CREATE TRIGGER trg_documents_tsv
    BEFORE INSERT OR UPDATE OF content ON documents
    FOR EACH ROW
    EXECUTE FUNCTION documents_tsv_trigger();

-- 6. BM25-like 全文检索函数
CREATE OR REPLACE FUNCTION match_documents_bm25(
    query_text TEXT,
    match_count INT DEFAULT 20,
    filter_kb_id UUID DEFAULT NULL
)
RETURNS TABLE (
    id UUID, knowledge_base_id UUID, doc_name VARCHAR, content TEXT,
    metadata JSONB, similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT d.id,
           (d.metadata->>'kb_id')::UUID,
           COALESCE(d.metadata->>'doc_name', '')::VARCHAR,
           d.content, d.metadata,
           ts_rank(d.tsv, plainto_tsquery('simple', query_text))::FLOAT AS similarity
    FROM documents d
    WHERE (filter_kb_id IS NULL OR d.metadata->>'kb_id' = filter_kb_id::TEXT)
        AND d.tsv @@ plainto_tsquery('simple', query_text)
    ORDER BY ts_rank(d.tsv, plainto_tsquery('simple', query_text)) DESC
    LIMIT match_count;
END;
$$;

-- 7. BM25 多知识库联合检索函数
CREATE OR REPLACE FUNCTION match_documents_bm25_multi_kb(
    query_text TEXT,
    match_count INT DEFAULT 20,
    filter_kb_ids UUID[] DEFAULT NULL
)
RETURNS TABLE (
    id UUID, knowledge_base_id UUID, doc_name VARCHAR, content TEXT,
    metadata JSONB, similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT d.id,
           (d.metadata->>'kb_id')::UUID,
           COALESCE(d.metadata->>'doc_name', '')::VARCHAR,
           d.content, d.metadata,
           ts_rank(d.tsv, plainto_tsquery('simple', query_text))::FLOAT AS similarity
    FROM documents d
    WHERE (filter_kb_ids IS NULL OR (d.metadata->>'kb_id')::UUID = ANY(filter_kb_ids))
        AND d.tsv @@ plainto_tsquery('simple', query_text)
    ORDER BY ts_rank(d.tsv, plainto_tsquery('simple', query_text)) DESC
    LIMIT match_count;
END;
$$;
