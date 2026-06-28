# Plan-02：文档处理模块

> 关联：[Plan-01 项目总览](./plan-01-overview.md) | PRD §2.1

---

## 1. 模块职责

接收用户上传的文档，完成解析 → 分块 → 向量化 → 存储的全自动流水线。

---

## 2. 处理流水线

```
文档上传 (COS)
    │
    ▼
┌──────────┐    ┌──────────┐    ┌──────────────┐    ┌──────────────┐
│ 格式解析  │ → │ 文本分块  │ → │ Embedding   │ → │ pgvector 存储 │
│ Loader   │    │ Splitter │    │ DeepSeek     │    │ Supabase      │
└──────────┘    └──────────┘    └──────────────┘    └──────────────┘
```

### 2.1 格式解析（LangChain Document Loaders）

| 格式 | Loader | 说明 |
|------|--------|------|
| PDF | `PyPDFLoader` | 提取文本，含页数元数据 |
| Word (.docx) | `Docx2txtLoader` | 提取纯文本 |
| Markdown (.md) | `UnstructuredMarkdownLoader` | 保留标题层级 |
| TXT | `TextLoader` | 直接读取 |
| URL (Phase 2) | `WebBaseLoader` | 抓取网页文本 |

### 2.2 文本分块（Text Splitter）

选用 `RecursiveCharacterTextSplitter`，默认参数（可配置）：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `chunk_size` | 500 | 每块最大字符数 |
| `chunk_overlap` | 50 | 块间重叠字符数 |
| `separators` | `["\n\n", "\n", "。", "."]` | 优先按段落/句子切分 |

### 2.3 Embedding（向量化）

- **API**：DeepSeek Embedding API（OpenAI 兼容接口）
- **模型**：`deepseek-embedding`（具体 model id 待 DeepSeek 文档确认）
- **维度**：待确认（参考值 1536 或 1024）

```python
from langchain_community.embeddings import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(
    model="deepseek-embedding",
    openai_api_base="https://api.deepseek.com/v1",
    openai_api_key=DEEPSEEK_API_KEY,
)
```

### 2.4 向量存储（Supabase pgvector）

```python
from langchain_community.vectorstores import SupabaseVectorStore

vectorstore = SupabaseVectorStore(
    embedding=embeddings,
    client=supabase_client,
    table_name="documents",
    query_name="match_documents",
)
```

**Supabase 表结构**（pgvector）：

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_base_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    doc_name TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding VECTOR(1536),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

---

## 3. API 设计

### `POST /api/admin/knowledge-bases/{kb_id}/documents`

上传文档到指定知识库。

**Request**：`multipart/form-data`
| 字段 | 类型 | 说明 |
|------|------|------|
| `file` | File | PDF/Word/MD/TXT，最大 20MB |
| `folder` | string (可选) | 文件夹/分类 |
| `tags` | string[] (可选) | 标签列表 |

**Response**：
```json
{
  "doc_id": "uuid",
  "name": "xxx.pdf",
  "chunks": 42,
  "status": "completed"
}
```

### `DELETE /api/admin/documents/{doc_id}`

删除文档及关联向量数据。

### `GET /api/admin/knowledge-bases/{kb_id}/documents`

文档列表，支持 `?search=keyword&folder=x&page=1&size=20`。

### `POST /api/admin/knowledge-bases/{kb_id}/import-url`（Phase 2）

URL 导入。

**Request**：`{"url": "https://..."}`

---

## 4. LangChain Pipeline 伪代码

```python
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import SupabaseVectorStore

async def process_document(file_path: str, kb_id: str, filename: str):
    # 1. 选择 Loader
    loader = get_loader(file_path)  # 根据扩展名

    # 2. 加载文档
    docs = loader.load()

    # 3. 分块
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=50
    )
    chunks = splitter.split_documents(docs)

    # 4. 注入元数据
    for chunk in chunks:
        chunk.metadata["kb_id"] = kb_id
        chunk.metadata["doc_name"] = filename

    # 5. 向量化 + 存储
    vectorstore = SupabaseVectorStore(...)
    vectorstore.add_documents(chunks)

    return len(chunks)
```

---

## 5. 待实现 Checklist

- [ ] 文件上传到 COS（SDK：`cos-python-sdk-v5`）
- [ ] 格式检测与 Loader 路由
- [ ] RecursiveCharacterTextSplitter 参数配置
- [ ] DeepSeek Embedding 接口对接
- [ ] Supabase pgvector 表创建与查询函数
- [ ] 文档删除（级联删除向量）
- [ ] 上传进度反馈
- [ ] URL 导入（Phase 2）
- [ ] 批量上传（Phase 2）
