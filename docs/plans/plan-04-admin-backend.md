# Plan-04：管理后台模块

> 关联：[Plan-01 项目总览](./plan-01-overview.md) | PRD §2.1, §2.3, §2.4

---

## 1. 模块职责

提供知识库和文档的 CRUD 管理能力，通过 Admin Key 认证。

---

## 2. 认证方案

### Admin Key 认证

- 无需账号密码，管理后台仅凭 Admin Key 访问
- Admin Key 通过 **环境变量 `ADMIN_KEY`** 设置
- 所有 `/api/admin/*` 请求需携带 `Authorization: Bearer <ADMIN_KEY>` 头
- 中间件校验，不匹配返回 401

```python
# FastAPI 中间件
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

def verify_admin(credentials = Depends(security)):
    if credentials.credentials != settings.ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True
```

---

## 3. 数据模型

### 3.1 知识库表（knowledge_bases）

```sql
CREATE TABLE knowledge_bases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT DEFAULT '',
    is_public BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.2 文档表（documents）

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_base_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    doc_name VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    folder VARCHAR(255) DEFAULT '',
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    embedding VECTOR(1536),
    chunk_index INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 4. API 设计

### 4.1 知识库 CRUD

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/admin/knowledge-bases` | 创建知识库 |
| `GET` | `/api/admin/knowledge-bases` | 知识库列表 |
| `GET` | `/api/admin/knowledge-bases/{kb_id}` | 知识库详情 |
| `PUT` | `/api/admin/knowledge-bases/{kb_id}` | 编辑知识库 |
| `DELETE` | `/api/admin/knowledge-bases/{kb_id}` | 删除知识库（级联删除文档+向量） |

**创建请求**：
```json
{
  "name": "我的技术笔记",
  "description": "关于 Python 和 AI 的学习笔记",
  "is_public": true
}
```

### 4.2 文档 CRUD

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/admin/knowledge-bases/{kb_id}/documents` | 上传文档 |
| `GET` | `/api/admin/knowledge-bases/{kb_id}/documents` | 文档列表 |
| `DELETE` | `/api/admin/documents/{doc_id}` | 删除文档+向量 |
| `POST` | `/api/admin/knowledge-bases/{kb_id}/batch-import` | 批量上传（Phase 2） |
| `POST` | `/api/admin/knowledge-bases/{kb_id}/import-url` | URL 导入（Phase 2） |

### 4.3 系统配置（Phase 2）

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/admin/settings` | 获取系统配置 |
| `PUT` | `/api/admin/settings` | 更新分块参数/Top-K/阈值 |

---

## 5. COS 文件存储

原始上传文档存入腾讯云 COS，路径规则：

```
/{bucket}/documents/{kb_id}/{doc_id}_{original_filename}
```

- Supabase 存元数据 + 向量，COS 存原始文件
- 删除文档时同时删除 COS 对象
- 预留后续重新处理的能力（分块参数变更后可从 COS 重取原文）

```python
from qcloud_cos import CosConfig, CosS3Client

cos_client = CosS3Client(CosConfig(
    Region=settings.COS_REGION,
    SecretId=settings.COS_SECRET_ID,
    SecretKey=settings.COS_SECRET_KEY,
))
```

---

## 6. 管理后台页面结构

```
/admin
├── /login                 → Admin Key 输入页
├── /dashboard             → 知识库管理主页
│   ├── 知识库列表          → 卡片/表格展示
│   └── 创建知识库按钮       → 弹窗表单
├── /kb/:id                → 知识库详情
│   ├── 知识库信息编辑       →
│   ├── 文档列表            → 表格，支持搜索
│   ├── 上传文档按钮         → 拖拽上传区域
│   └── 删除文档按钮         → 确认弹窗
└── /settings              → 系统配置（Phase 2）
```

---

## 7. 待实现 Checklist

- [ ] Supabase 表建模（knowledge_bases、documents）
- [ ] Admin Key 认证中间件
- [ ] 知识库 CRUD API
- [ ] 文档上传 API（COS + 触发处理流水线）
- [ ] 文档列表/搜索 API
- [ ] 文档删除 API（COS + pgvector 级联）
- [ ] COS SDK 集成
- [ ] URL 导入（Phase 2）
- [ ] 批量上传（Phase 2）
- [ ] 分块参数配置（Phase 2）
