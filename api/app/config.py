"""
应用配置管理。所有密钥类配置从环境变量加载，禁止硬编码。
"""
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    # ── Supabase ──
    SUPABASE_URL: str = field(default_factory=lambda: os.getenv("SUPABASE_URL", ""))
    SUPABASE_SERVICE_ROLE_KEY: str = field(
        default_factory=lambda: os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    )

    # ── DeepSeek API ──
    DEEPSEEK_API_KEY: str = field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", ""))
    DEEPSEEK_BASE_URL: str = field(
        default_factory=lambda: os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    )
    DEEPSEEK_CHAT_MODEL: str = field(
        default_factory=lambda: os.getenv("DEEPSEEK_CHAT_MODEL", "deepseek-chat")
    )
    DEEPSEEK_CHAT_MODEL: str = field(
        default_factory=lambda: os.getenv("DEEPSEEK_CHAT_MODEL", "deepseek-chat")
    )

    # ── Embedding（通义千问 DashScope）──
    EMBED_MODEL: str = field(
        default_factory=lambda: os.getenv("EMBED_MODEL", "text-embedding-v3")
    )
    EMBED_DIMENSIONS: int = 1024  # text-embedding-v3 输出 1024 维

    # ── Rerank ──
    RERANK_PROVIDER: str = field(
        default_factory=lambda: os.getenv("RERANK_PROVIDER", "qwen")  # auto / deepseek / qwen
    )
    DASHSCOPE_API_KEY: str = field(default_factory=lambda: os.getenv("DASHSCOPE_API_KEY", ""))

    # ── Admin ──
    ADMIN_KEY: str = field(default_factory=lambda: os.getenv("ADMIN_KEY", "admin-secret-change-me"))

    # ── COS ──
    COS_SECRET_ID: str = field(default_factory=lambda: os.getenv("COS_SECRET_ID", ""))
    COS_SECRET_KEY: str = field(default_factory=lambda: os.getenv("COS_SECRET_KEY", ""))
    COS_REGION: str = field(default_factory=lambda: os.getenv("COS_REGION", "ap-guangzhou"))
    COS_BUCKET: str = field(default_factory=lambda: os.getenv("COS_BUCKET", ""))

    # ── Retrieval config ──
    RETRIEVAL_TOP_N: int = 20
    RERANK_TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.4  # 向量检索最低相似度
    RERANK_SCORE_THRESHOLD: float = 0.3
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # ── App ──
    APP_TITLE: str = "RAG Knowledge QA"
    APP_VERSION: str = "0.1.0"
    UPLOAD_MAX_SIZE_MB: int = 20


settings = Settings()
