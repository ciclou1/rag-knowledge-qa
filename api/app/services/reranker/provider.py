"""
Rerank 抽象层：主备双通道（DeepSeek / 通义千问）。
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

import httpx

from app.config import settings


class RerankProvider(str, Enum):
    DEEPSEEK = "deepseek"
    QWEN = "qwen"


class RerankResult:
    """单条 rerank 结果。"""
    def __init__(self, index: int, relevance_score: float):
        self.index = index
        self.relevance_score = relevance_score


class BaseReranker(ABC):
    @abstractmethod
    async def rerank(
        self, query: str, documents: list[str], top_k: int = 5
    ) -> list[RerankResult]:
        """对文档列表重排序，返回 Top-K 结果。"""
        ...


class QwenReranker(BaseReranker):
    """通义千问 qwen3-rerank 模型。"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.endpoint = "https://dashscope.aliyuncs.com/compatible-api/v1/reranks"
        self.model = "qwen3-rerank"

    async def rerank(
        self, query: str, documents: list[str], top_k: int = 5
    ) -> list[RerankResult]:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                self.endpoint,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "query": query,
                    "documents": documents,
                    "top_n": top_k,
                    "instruct": "Given a web search query, retrieve relevant passages that answer the query.",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return [RerankResult(r["index"], r["relevance_score"]) for r in data["results"]]


class DeepSeekReranker(BaseReranker):
    """
    DeepSeek Rerank — 占位实现。
    DeepSeek 上线 Rerank API 后补全。
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.endpoint = f"{settings.DEEPSEEK_BASE_URL}/rerank"
        self.model = "deepseek-rerank"

    async def rerank(
        self, query: str, documents: list[str], top_k: int = 5
    ) -> list[RerankResult]:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                self.endpoint,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "query": query,
                    "documents": documents,
                    "top_n": top_k,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return [RerankResult(r["index"], r["relevance_score"]) for r in data["results"]]


def get_reranker() -> BaseReranker:
    """
    Reranker 工厂：按优先级选择可用 Provider。

    优先级:
    1. RERANK_PROVIDER=deepseek → DeepSeek
    2. RERANK_PROVIDER=qwen → 通义千问
    3. RERANK_PROVIDER=auto → DeepSeek 优先，不可用时降级 Qwen
    """
    provider = settings.RERANK_PROVIDER

    if provider == "deepseek" and settings.DEEPSEEK_API_KEY:
        return DeepSeekReranker(settings.DEEPSEEK_API_KEY)

    if provider == "qwen" and settings.DASHSCOPE_API_KEY:
        return QwenReranker(settings.DASHSCOPE_API_KEY)

    # auto 模式：优先 DeepSeek
    if provider == "auto":
        if settings.DEEPSEEK_API_KEY:
            return DeepSeekReranker(settings.DEEPSEEK_API_KEY)
        if settings.DASHSCOPE_API_KEY:
            return QwenReranker(settings.DASHSCOPE_API_KEY)

    # 最终 fallback
    if settings.DASHSCOPE_API_KEY:
        return QwenReranker(settings.DASHSCOPE_API_KEY)

    raise RuntimeError(
        "No rerank provider available. Set DASHSCOPE_API_KEY or DEEPSEEK_API_KEY."
    )
