"""
FastAPI 应用入口。
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import admin, qa

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
)

# CORS：允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境改为具体域名
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(qa.router, prefix="/api/qa", tags=["QA"])


@app.get("/api/health")
async def health_check():
    """健康检查端点。"""
    return {"status": "ok", "version": settings.APP_VERSION}
