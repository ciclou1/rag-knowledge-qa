# Plan-06：部署与运维

> 关联：[Plan-01 项目总览](./plan-01-overview.md) | PRD §6

---

## 1. 部署架构

EdgeOne **仅负责静态前端托管 + CDN + 域名**，不参与后端运行时。应用代码对 EdgeOne 零依赖。

```
GitHub (源码)
    │
    ├── git push → EdgeOne Pages（导入仓库，自动构建）
    │                  │
    │                  └── 托管 /web/dist → React SPA（静态）
    │
    └── ssh deploy → 腾讯云 Lighthouse
                       │
                       └── Docker 运行 FastAPI（/api/*）
                              │
                              ├──→ Supabase (pgvector)
                              ├──→ DeepSeek API (Chat + Embedding)
                              ├──→ 通义千问 API (Rerank)
                              └──→ 腾讯云 COS (文档存储)
```

**核心原则**：

| 组件 | 部署位置 | 应用依赖 |
|------|----------|----------|
| React SPA | **EdgeOne Pages**（纯静态托管） | 无 EdgeOne SDK |
| FastAPI | **Lighthouse**（Docker 容器） | 无 EdgeOne SDK |
| DNS + CDN | EdgeOne（域名 + SSL + 加速） | 无 EdgeOne SDK |

> 整个代码仓库中没有任何 EdgeOne 相关的 SDK 依赖。EdgeOne 只是 Git 导入 → 自动 `npm run build` → 托管静态产物。

---

## 2. 依赖服务

### 2.1 DeepSeek API

| 项 | 说明 |
|----|------|
| 官网 | https://platform.deepseek.com |
| 用途 | Chat API（问答生成）、Embedding API（向量化）、Rerank API（重排序） |
| 配置 | `DEEPSEEK_API_KEY` 环境变量 |
| 预算 | ¥50-200/月（低日活） |

### 2.2 Supabase

| 项 | 说明 |
|----|------|
| 官网 | https://supabase.com |
| 用途 | PostgreSQL + pgvector 向量存储 |
| 配置 | `SUPABASE_URL`、`SUPABASE_SERVICE_ROLE_KEY` |
| 推荐 Region | Asia Pacific — 靠近腾讯云 |

**需要创建的表**：
- `knowledge_bases` — 知识库元数据
- `documents` — 文档分块 + 向量

### 2.3 腾讯云 COS

| 项 | 说明 |
|----|------|
| 用途 | 原始上传文档存储 |
| 配置 | `COS_SECRET_ID`、`COS_SECRET_KEY`、`COS_REGION`、`COS_BUCKET` |
| 预算 | ¥5-20/月 |

---

## 3. 环境变量清单

以下环境变量分为两类：前端构建时变量（EdgeOne 后台设置）和后端运行时变量（Lighthouse `.env` 文件）。所有密钥类变量禁止写入代码仓库。

### 3.1 前端环境变量（EdgeOne Pages 后台配置）

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `VITE_API_BASE` | FastAPI 后端地址 | `https://api.your-domain.com` |

### 3.2 后端环境变量（Lighthouse `.env` / Docker `--env-file`）

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥（Chat + Embedding） | `sk-...` |
| `DASHSCOPE_API_KEY` | 通义千问 DashScope API Key（Rerank） | `sk-...` |
| `RERANK_PROVIDER` | Rerank 优先级：`deepseek` / `qwen` / `auto` | `auto`（默认） |
| `SUPABASE_URL` | Supabase 项目 URL | `https://xxx.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase Service Role | `eyJ...` |
| `ADMIN_KEY` | 管理后台认证密钥 | `自定义复杂字符串` |
| `COS_SECRET_ID` | 腾讯云 COS SecretId | `AKID...` |
| `COS_SECRET_KEY` | 腾讯云 COS SecretKey | `...` |
| `COS_REGION` | COS 区域 | `ap-guangzhou` |
| `COS_BUCKET` | COS 存储桶名称 | `rag-docs-xxx` |

---

## 4. EdgeOne 部署步骤

### 4.1 前置准备

1. 代码推送至 GitHub 仓库（public 或 private）
2. EdgeOne Pages 授权访问 GitHub

### 4.2 创建 EdgeOne Pages 项目

1. EdgeOne 控制台 → Pages → 新建项目
2. 选择「导入 Git 仓库」
3. 授权并选择 GitHub 仓库
4. 配置：

| 配置项 | 值 |
|--------|-----|
| **根目录** | `/` |
| **构建命令** | `cd web && npm install && npm run build` |
| **输出目录** | `web/dist` |
| **框架** | React (Vite) |

### 4.3 配置环境变量

将所有环境变量（见 §3）填入 EdgeOne Pages 的环境变量设置。

### 4.4 后端部署（Lighthouse）

FastAPI 通过 Docker 部署至腾讯云 Lighthouse。

```dockerfile
# Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY api/ ./api/
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**部署步骤**：
1. Lighthouse 安装 Docker
2. 上传代码 + `docker build -t rag-api .`
3. `docker run -d -p 8000:8000 --env-file .env rag-api`
4. EdgeOne CDN 配置回源至 Lighthouse IP:8000，路径 `/api/*`
5. （可选）配置 HTTPS + 自定义域名

### 4.5 上线

1. 推送代码到 GitHub → 自动触发 EdgeOne 构建
2. 绑定自定义域名（可选）
3. 配置 DNS（Cloudflare / 腾讯云 DNSPod）
4. 配置 SSL 证书（EdgeOne 自动提供）

---

## 5. CI/CD（GitHub Actions）

```yaml
name: Deploy to EdgeOne
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Trigger EdgeOne Deploy
        run: |
          curl -X POST "${{ secrets.EDGEONE_DEPLOY_HOOK }}"
```

---

## 6. 成本估算

| 资源 | 月费（初期） | 月费（增长后） |
|------|-------------|---------------|
| DeepSeek API（Chat+Embedding） | ¥50 | ¥200 |
| 通义千问 Rerank API | ¥10 | ¥50 |
| Supabase | ¥0（免费层） | ¥180（Pro） |
| Lighthouse 2C2G | ¥52 | ¥52 |
| EdgeOne Pages（静态托管） | ¥0（免费层） | ¥50 |
| COS | ¥5 | ¥20 |
| **合计** | **¥120-170** | **¥550-700** |

---

## 7. 运维 Checklist

- [ ] 创建 GitHub 仓库，推送初始代码
- [ ] 注册 DeepSeek API 并获取 Key
- [ ] 注册通义千问 DashScope 并获取 Key
- [ ] 创建 Supabase 项目，启用 pgvector 扩展，建表
- [ ] 创建 COS Bucket，配置访问密钥
- [ ] 购买 Lighthouse 实例（2C2G），安装 Docker
- [ ] 构建 FastAPI Docker 镜像，`docker run` 部署
- [ ] EdgeOne Pages 导入 GitHub 仓库，配置构建命令
- [ ] EdgeOne Pages 填写环境变量 `VITE_API_BASE`
- [ ] EdgeOne CDN 配置 `/api/*` 回源至 Lighthouse
- [ ] 绑定域名 + SSL（EdgeOne 自动）
- [ ] 编写 README.md（项目说明 + 本地开发指南）
