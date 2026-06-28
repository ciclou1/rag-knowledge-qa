# RAG 知识问答系统

基于 RAG（检索增强生成）的知识问答系统，支持个人/团队知识管理与对外知识服务。

> 📄 完整 PRD：[PRD.md](./PRD.md)
> 📋 子模块 Plan：[docs/plans/](./docs/plans/)

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | React 18 + TypeScript + Ant Design + Vite |
| 后端 | Python FastAPI + LangChain |
| LLM | DeepSeek (Chat + Embedding) |
| Rerank | 通义千问 qwen3-rerank（主），DeepSeek Rerank（备） |
| 向量库 | Supabase pgvector |
| 文件存储 | 腾讯云 COS |
| 部署 | EdgeOne Pages（前端） + Lighthouse Docker（后端） |

## 项目结构

```
├── api/                    # FastAPI 后端
│   ├── app/
│   │   ├── main.py         # 入口
│   │   ├── config.py       # 配置管理
│   │   ├── db.py           # Supabase 客户端
│   │   ├── middleware.py    # Admin Key 认证
│   │   ├── routers/
│   │   │   ├── admin.py    # 管理后台 API
│   │   │   └── qa.py       # 问答 API
│   │   ├── services/
│   │   │   ├── document_processor.py  # 文档流水线
│   │   │   ├── qa_engine.py          # 问答引擎
│   │   │   ├── cos_service.py        # COS 存储
│   │   │   └── reranker/provider.py  # Rerank 抽象层
│   │   └── models/schemas.py         # Pydantic 模型
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
│
├── web/                    # React 前端
│   ├── src/
│   │   ├── App.tsx         # 路由
│   │   ├── main.tsx
│   │   ├── api/client.ts   # API 封装
│   │   └── pages/          # 页面组件
│   ├── package.json
│   ├── vite.config.ts
│   └── .env.example
│
├── supabase/
│   └── migrations/001_init.sql  # 建表脚本
│
├── docker-compose.yml
└── docs/plans/             # 详细 Plan 文档
```

## 快速开始

### 1. 环境准备

- Python 3.12+
- Node.js 20+
- Supabase 项目（启用 pgvector 扩展）
- DeepSeek API Key
- 通义千问 DashScope API Key（Rerank）

### 2. 初始化数据库

在 Supabase SQL Editor 中执行 `supabase/migrations/001_init.sql`。

### 3. 启动后端

```bash
cd api
cp .env.example .env        # 编辑 .env，填写实际的 API Key
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 4. 启动前端

```bash
cd web
cp .env.example .env        # 本地开发无需修改
npm install
npm run dev
```

访问 http://localhost:5173

### 5. Docker 部署

```bash
cp api/.env.example api/.env  # 编辑填写真实 Key
docker-compose up -d
```

## 部署到腾讯云

前端 → EdgeOne Pages（导入 GitHub 仓库，自动构建 React）
后端 → Lighthouse（Docker 部署 FastAPI）

详见 [plan-06-deployment.md](./docs/plans/plan-06-deployment.md)

## API 概览

| 端点 | 认证 | 说明 |
|------|------|------|
| `GET /api/health` | 无 | 健康检查 |
| `GET /api/qa/knowledge-bases` | 无 | 公开知识库列表 |
| `POST /api/qa/ask` | 无 | 问答 |
| `GET/POST/PUT/DELETE /api/admin/knowledge-bases/*` | Admin Key | 知识库 CRUD |
| `POST /api/admin/knowledge-bases/{id}/documents` | Admin Key | 上传文档 |
| `DELETE /api/admin/documents/{name}` | Admin Key | 删除文档 |

## License

MIT
