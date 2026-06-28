"""
自定义 Embedding 服务：通义千问 DashScope text-embedding-v3。
DeepSeek 当前无 Embedding API，因此使用 DashScope 替代。
"""
from typing import List
import httpx
from langchain_core.embeddings import Embeddings
from app.config import settings


class DashScopeEmbeddings(Embeddings):
    """通义千问 DashScope text-embedding-v3 封装，兼容 LangChain Embeddings 接口。"""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "text-embedding-v3",
        dimensions: int = 1536,
    ):
        self.api_key = api_key or settings.DASHSCOPE_API_KEY
        self.model = model
        self.dimensions = dimensions
        self.endpoint = (
            "https://dashscope.aliyuncs.com/api/v1/services/embeddings/"
            "text-embedding/text-embedding"
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量 Embedding（同步）。"""
        embeddings = []
        # DashScope API 单次最多 25 条
        batch_size = 25
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self._call_api(batch)
            embeddings.extend(batch_embeddings)
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """单条查询 Embedding。"""
        return self._call_api([text])[0]

    def _call_api(self, texts: List[str]) -> List[List[float]]:
        """调用 DashScope Embedding API。"""
        resp = httpx.post(
            self.endpoint,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "input": {"texts": texts},
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return [item["embedding"] for item in data["output"]["embeddings"]]
