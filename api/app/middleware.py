"""
认证中间件：Admin Key 校验。
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings

security = HTTPBearer(auto_error=False)


async def verify_admin_key(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> None:
    """校验 Admin Key。所有 /api/admin/* 路由依赖此函数。"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing admin key. Use Bearer <ADMIN_KEY> in Authorization header.",
        )
    if credentials.credentials != settings.ADMIN_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin key.",
        )
