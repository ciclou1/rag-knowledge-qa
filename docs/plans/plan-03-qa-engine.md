# Plan-03：问答引擎模块

> 关联：[Plan-01 项目总览](./plan-01-overview.md) | PRD §2.2

---

## 1. 模块职责

接收用户问题，检索知识库 → Rerank → 组装 Prompt → LLM 生成回答。

---

## 2. 检索流程（含 Rerank）

```
用户问题 (q)
    │
    ▼
DeepSeek Embedding → query_vector
    │
    ▼
pgvector 余弦检索 → Top-N 候选 (N=20, 粗排)
    │
    ▼
DeepSeek Rerank API → 重排序
    │
    ▼
Top-K 精选片段 (K=5, 精排)
    │
    ▼
组装 Prompt（System + Context + Question）
    │
    ▼
DeepSeek Chat API → 生成回答
    │
    ▼
返回 { answer, sources[] }
```

---

## 3. 检索参数（可配置）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `retrieval_top_n` | 20 | 初检返回候选数 |
| `rerank_top_k` | 5 | 精排后保留数 |
| `similarity_threshold` | 0.7 | 初检最低余弦相似度 |
| `rerank_score_threshold` | 0.3 | Rerank 最低分数，低于则触发 fallback |
| `max_tokens` | 2048 | 生成回答最大 token 数 |
| `temperature` | 0.3 | 生成温度，低值保证回答稳定 |

---

## 4. Rerank 机制

### 为什么需要 Rerank

- 向量检索基于语义相似度，对关键词匹配不够精确
- 初检放宽 Top-N（20 条），提高召回率
- Rerank 模型对 question-passage 关系做更精细的语义匹配，选出真正相关的 Top-K（5 条）
- 减少无关片段进入 Prompt，提升答案质量并节省 token

### Rerank 策略：主备双通道

采用**提供商标识 + 自动降级**的模式，优先调用 DeepSeek，不可用时自动切换通义千问。

```
尝试 DeepSeek Rerank API
    ├── 可用 → 使用 deepseek-rerank
    └── 不可用 → 降级到通义千问 qwen3-rerank
```

### 通道 1：DeepSeek Rerank（主）

```python
# DeepSeek Rerank API（OpenAI 兼容，接口待确认）
# 若 DeepSeek 后续提供 Rerank 端点，优先使用
POST https://api.deepseek.com/v1/rerank
Authorization: Bearer sk-...
Content-Type: application/json

{
  "model": "deepseek-rerank",
  "query": "什么是 RAG？",
  "documents": ["文档1", "文档2", ...],
  "top_n": 5
}
```

**状态**：截至 2026-06，DeepSeek 尚未公开独立的 Rerank API 端点。若后续上线，优先使用本通道。

### 通道 2：通义千问 Rerank（备用，当前实际使用）

| 项 | 说明 |
|----|------|
| 模型 | `qwen3-rerank` |
| 端点 | `https://dashscope.aliyuncs.com/compatible-api/v1/reranks` |
| 最大文档数 | 500 |
| 单条最大 Token | 4,000 |
| 支持语种 | 100+（含中英文） |
| 认证 | `Authorization: Bearer $DASHSCOPE_API_KEY` |

```bash
curl -X POST \
  "https://dashscope.aliyuncs.com/compatible-api/v1/reranks" \
  -H "Authorization: Bearer $DASHSCOPE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-rerank",
    "query": "什么是 RAG？",
    "documents": ["文档1", "文档2", "文档3"],
    "top_n": 5,
    "instruct": "Given a web search query, retrieve relevant passages that answer the query."
  }'
```

> 注：`gte-rerank-v2` 于 2026-05-30 下线，官方推荐迁移至 `qwen3-rerank`。

**响应格式**：
```json
{
  "results": [
    { "index": 0, "relevance_score": 0.93345 },
    { "index": 2, "relevance_score": 0.34100 }
  ],
  "usage": { "total_tokens": 79 }
}
```

### 统一 Rerank 抽象层

```python
# reranker/provider.py
from abc import ABC, abstractmethod
from enum import Enum

class RerankProvider(str, Enum):
    DEEPSEEK = "deepseek"
    QWEN = "qwen"

class BaseReranker(ABC):
    @abstractmethod
    async def rerank(self, query: str, documents: list[str], top_k: int = 5) -> list[dict]:
        """返回 [{index, relevance_score}, ...]"""
        ...

class QwenReranker(BaseReranker):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.endpoint = "https://dashscope.aliyuncs.com/compatible-api/v1/reranks"
        self.model = "qwen3-rerank"

    async def rerank(self, query: str, documents: list[str], top_k: int = 5):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.endpoint,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "query": query,
                    "documents": documents,
                    "top_n": top_k,
                    "instruct": "Given a web search query, retrieve relevant passages that answer the query.",
                },
            )
            return resp.json()["results"]

class DeepSeekReranker(BaseReranker):
    # 占位 — DeepSeek 上线 Rerank API 后实现
    ...

# 工厂：自动检测可用 Provider
def get_reranker() -> BaseReranker:
    if settings.DASHSCOPE_API_KEY:
        logger.info("Rerank provider: qwen3-rerank")
        return QwenReranker(settings.DASHSCOPE_API_KEY)
    # DeepSeek Rerank 可用时在此判断优先
    raise ValueError("No rerank provider available. Set DASHSCOPE_API_KEY.")
```

### 新增环境变量

| 变量 | 说明 |
|------|------|
| `DASHSCOPE_API_KEY` | 通义千问 DashScope API Key（Rerank 使用） |
| `RERANK_PROVIDER` | 强制指定 provider：`qwen` / `deepseek` / `auto`（默认 auto） |

---

## 5. Prompt 模板

```
System:
你是一个专业的知识问答助手。请严格根据以下提供的知识库内容回答问题。
如果知识库内容不足以回答问题，请明确回复「根据现有知识，我无法回答这个问题」，
不要编造或猜测。

Context（来自知识库检索结果）：
{context}

Instructions:
- 优先使用 Context 中的信息回答
- 回答末尾附上引用来源（文档名 + 片段摘要）
- 回答简洁准确，避免冗余
- 如果 Context 不包含答案，明确说明

User Question:
{question}
```

---

## 6. 跨库联合检索

**Phase 2 实现**。用户勾选多个知识库时：

1. 分别对每个知识库执行 pgvector 检索（各取 Top-N）
2. 合并所有候选片段
3. 统一送入 Rerank 排序（跨库全局重排）
4. 取全局 Top-K 进入 Prompt

```python
async def multi_kb_search(query: str, kb_ids: list[str]):
    all_candidates = []
    for kb_id in kb_ids:
        candidates = await vectorstore.similarity_search_with_score(
            query,
            k=20,
            filter={"kb_id": kb_id},
        )
        all_candidates.extend(candidates)
    
    # 合并后统一 Rerank
    reranked = await rerank(query, all_candidates, top_k=5)
    return reranked
```

---

## 7. Fallback 策略

| 场景 | 行为 |
|------|------|
| 初检所有结果相似度 < 0.7 | 直接返回「未找到相关知识」 |
| Rerank 最高分 < 0.3 | 返回「未找到相关知识」 |
| LLM 生成结果为空 | 返回「抱歉，生成回答时出现问题」 |
| 知识库为空 | 返回「该知识库暂无内容」 |

---

## 8. API 设计

### `POST /api/qa/ask`

**Request**：
```json
{
  "question": "什么是 RAG？",
  "kb_ids": ["uuid-1", "uuid-2"],
  "options": {
    "top_k": 5
  }
}
```

**Response**：
```json
{
  "answer": "RAG（检索增强生成）是一种...",
  "sources": [
    {
      "doc_name": "RAG入门指南.pdf",
      "content_snippet": "RAG 是一种将检索与生成结合的技术...",
      "relevance_score": 0.92
    }
  ],
  "confidence": "high"
}
```

### `GET /api/qa/knowledge-bases`

返回所有公开知识库列表，供问答页面展示和选择。

---

## 9. 待实现 Checklist

- [ ] LangChain RetrievalQA Chain 搭建
- [ ] pgvector 相似度检索函数
- [ ] DeepSeek Rerank API 对接
- [ ] ContextualCompressionRetriever 集成
- [ ] Prompt 模板管理与组装
- [ ] Fallback 逻辑
- [ ] 来源引用拼接
- [ ] 跨库联合检索（Phase 2）
