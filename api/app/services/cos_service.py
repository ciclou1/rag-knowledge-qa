"""
腾讯云 COS 文件存储服务。
"""
import uuid
from pathlib import Path

from app.config import settings


class COSService:
    """简化版 COS 服务，生产环境使用 cos-python-sdk-v5。"""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None and settings.COS_SECRET_ID:
            from qcloud_cos import CosConfig, CosS3Client

            config = CosConfig(
                Region=settings.COS_REGION,
                SecretId=settings.COS_SECRET_ID,
                SecretKey=settings.COS_SECRET_KEY,
            )
            self._client = CosS3Client(config)
        return self._client

    def upload_document(self, file_path: str, kb_id: str, original_name: str) -> str:
        """
        上传文档到 COS。
        返回 COS 对象键（key）。
        """
        doc_id = str(uuid.uuid4())
        ext = Path(original_name).suffix
        key = f"documents/{kb_id}/{doc_id}{ext}"

        if self.client:
            self.client.upload_file(
                Bucket=settings.COS_BUCKET,
                Key=key,
                LocalFilePath=file_path,
            )
        else:
            # 本地开发模式：直接返回本地路径
            key = file_path

        return key

    def delete_document(self, key: str) -> None:
        """从 COS 删除文档。"""
        if self.client and key.startswith("documents/"):
            self.client.delete_object(
                Bucket=settings.COS_BUCKET,
                Key=key,
            )


# 单例
cos_service = COSService()
