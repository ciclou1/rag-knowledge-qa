"""
Supabase 客户端封装。Service Role Key 用于服务端操作。
"""
from supabase import create_client, Client

from app.config import settings

_supabase: Client | None = None


def get_supabase() -> Client:
    """获取 Supabase 客户端（单例）。"""
    global _supabase
    if _supabase is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        _supabase = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
        )
    return _supabase
