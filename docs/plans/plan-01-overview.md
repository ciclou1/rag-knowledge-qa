# Plan-01：项目总览与架构

> 关联 PRD：`E:\rag\PRD.md` v1.2 | 日期：2026-06-28

---

## 1. 项目定义

基于 RAG 的知识问答系统，支持个人/团队知识管理与对外知识服务。

### 核心能力

- 文档上传 → 自动解析 → 向量化 → 语义检索 → Rerank → LLM 生成回答
- 公共/私有知识库，无需登录（Admin Key 管理）
- 单轮问答 + 跨库联合检索 + 来源引用 + 「不知道」fallback

### 目标用户

| 角色 | 数量 | 权限 |
|------|------|------|
| 管理员 | 1-5 人 | Admin Key 访问管理后台 |
| 访客 | < 100 DAU | 选择公开知识库提问 |

---

## 2. 技术栈

| 层 | 选型 | 用途 |
|----|------|------|
| 前端 | React + TypeScript | 问答页面 + 管理后台 |
| 后端 | Python FastAPI | RESTful API |
| LLM 编排 | LangChain | 文档加载、分块、Embedding、QA Chain、Rerank |
| LLM | DeepSeek API | Chat（生成）+ Embedding（向量化）+ Rerank（重排序） |
| 向量库 | Supabase pgvector | 文本块 + 向量 + 元数据 |
| 对象存储 | 腾讯云 COS | 原始上传文档 |
| 部署 | 腾讯云 EdgeOne | Git 导入 + 环境变量 + 自动构建 |
| 代码托管 | GitHub | 源码 + CI/CD |

---

## 3. 架构

### 逻辑架构

```
React 前端 (SPA)
    ├── 问答界面  ←→  FastAPI /api/qa
    └── 管理后台  ←→  FastAPI /api/admin
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
         LangChain   Supabase   腾讯云 COS
         (QA/Rerank) (pgvector)  (文档存储)
              │
              ▼
        DeepSeek API
        (Chat / Embedding / Rerank)
```

### 部署架构

```
GitHub 源码
    │
    ├── git push ──→ EdgeOne Pages（React SPA 静态托管 + CDN + 域名）
    │                   （应用代码零 EdgeOne SDK 依赖）
    │
    └── ssh deploy → Lighthouse（Docker 容器）
                        └── FastAPI :8000
                              ├──→ Supabase pgvector
                              ├──→ DeepSeek API (Chat / Embedding)
                              ├──→ 通义千问 API (Rerank)
                              └──→ 腾讯云 COS (文档存储)
```

> EdgeOne 仅做静态托管和 CDN，不参与后端运行时。前端通过 `VITE_API_BASE` 指向 Lighthouse 上的 FastAPI。

---

## 4. 项目分期

| 阶段 | 目标 | 核心交付 |
|------|------|----------|
| **Phase 1 — MVP** | 核心闭环跑通 | 文档上传→问答全链路，管理后台，问答页面 |
| **Phase 2 — 增强** | 功能完善 | URL 导入、批量上传、跨库检索、分块配置 |
| **Phase 3 — 优化** | 体验提升 | 仪表盘、问题推荐、多轮对话 |

---

## 5. 关联 Plan

| Plan | 内容 |
|------|------|
| [plan-02](./plan-02-doc-processing.md) | 文档处理：解析、分块、Embedding、Rerank |
| [plan-03](./plan-03-qa-engine.md) | 问答引擎：检索策略、Prompt、跨库检索 |
| [plan-04](./plan-04-admin-backend.md) | 管理后台：知识库/文档 CRUD、认证 |
| [plan-05](./plan-05-frontend.md) | 前端：页面设计、组件树、路由 |
| [plan-06](./plan-06-deployment.md) | 部署：EdgeOne、Supabase、COS、CI/CD |
