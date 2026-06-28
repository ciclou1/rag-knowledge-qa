# RAG 知识问答系统 — 产品需求文档 (PRD)

> 版本：v1.0 | 日期：2026-06-28 | 状态：待评审

---

## 1. 产品概述

### 1.1 产品定位

基于 RAG（检索增强生成）技术的知识问答系统，同时服务于两类场景：

| 场景 | 描述 |
|------|------|
| **个人/团队知识管理** | 管理员上传文档、管理知识库，通过问答界面快速检索和获取知识 |
| **对外知识服务** | 将知识库发布为公开问答页面，供外部用户自助查询 |

### 1.2 核心价值

- 文档上传即可问答，零门槛构建知识库
- DeepSeek + Supabase pgvector，低成本高性能
- 知识库公开/私有属性灵活切换，一套系统覆盖内外场景

### 1.3 目标用户

| 角色 | 描述 | 规模 |
|------|------|------|
| **管理员** | 上传文档、管理知识库、配置问答参数 | 1-5 人 |
| **普通用户** | 选择知识库进行问答 | 低日活（初期 < 100 DAU） |

### 1.4 产品形态

- Web 网页（桌面端 + 移动端响应式）
- 管理后台独立于问答界面

---

## 2. 功能需求

### 2.1 知识管理模块（管理后台）

#### 2.1.1 知识库管理

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 创建知识库 | 名称、描述、公开/私有属性 | P0 |
| 编辑知识库 | 修改名称、描述、可见性 | P0 |
| 删除知识库 | 删除知识库及其所有文档和向量数据 | P0 |
| 知识库列表 | 展示所有知识库，支持搜索和筛选 | P0 |

#### 2.1.2 文档管理

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 文档上传 | 支持 PDF / Word (.docx) / Markdown / TXT | P0 |
| 批量上传 | 一次上传多个文档 | P1 |
| URL 导入 | 输入 URL 自动抓取网页内容入库 | P1 |
| 文档分类 | 按文件夹/标签组织文档 | P1 |
| 文档删除 | 删除文档及其对应向量数据 | P0 |
| 文档列表 | 展示知识库内所有文档，支持搜索 | P0 |
| 上传状态 | 显示文档解析/分块/向量化进度 | P1 |

#### 2.1.3 文档处理流程

```
文档上传 → 格式解析 → 文本分块 → 向量化(Embedding) → 存入 Supabase pgvector
```

- **解析**：自动识别 PDF/Word/Markdown/HTML，提取纯文本
- **分块**：基于语义分块（LangChain Text Splitters），可配置块大小和重叠度
- **向量化**：调用 DeepSeek Embedding API 生成向量
- **存储**：Supabase pgvector 存储文本块 + 向量 + 元数据
- **增量更新**：每日增量同步，新增/删除文档自动更新向量库

#### 2.1.4 问答检索流程（含 Rerank）

```
用户问题 → Embedding 向量化 → pgvector 初检 Top-N（粗排）
         → Rerank 模型重排序 → 取 Top-K（精排）
         → 组装 Prompt → DeepSeek Chat 生成回答
```

- **初检（粗排）**：pgvector 余弦相似度检索，返回 Top-N 个候选片段（N 可配置，默认 N=20）
- **Rerank（精排）**：使用 DeepSeek Rerank API 对候选片段重新排序，精确选出最相关的 Top-K（K 可配置，默认 K=5）
- **优势**：相比纯向量检索，rerank 对语义匹配更准确，减少无关片段混入 Prompt，提升回答质量
- **Fallback**：相似度或 rerank 分数低于阈值时触发「不知道」回复

### 2.2 问答模块（公开页面）

#### 2.2.1 问答交互

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 知识库选择 | 用户从公开知识库列表中选择一个或多个进行问答 | P0 |
| 跨库检索 | 允许同时勾选多个知识库联合检索 | P1 |
| 单轮问答 | 用户输入问题，系统检索 + 生成回答 | P0 |
| 来源引用 | 回答附带引用文档名和原文片段 | P1 |
| 空答案处理 | 知识库无匹配内容时明确回复「未找到相关知识」 | P0 |
| 相似问题推荐 | 展示与用户问题相关的推荐问题 | P2 |

#### 2.2.2 检索策略（LangChain 实现）

```
用户问题 → Embedding 向量化 → pgvector 初检 → Top-N 候选 → 
DeepSeek Rerank API → Top-K 精选片段 → 组装 Prompt → DeepSeek Chat 生成回答
```

- **初检方式**：pgvector 余弦相似度检索，返回 Top-N 候选（默认 N=20）
- **Rerank**：DeepSeek Rerank API 对 N 个候选重新排序，输出 Top-K（默认 K=5）
- **Prompt 模板**：包含系统指令 + 精选上下文 + 用户问题
- **Fallback**：rerank 最高分低于阈值时触发「不知道」回复

### 2.3 管理后台

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 仪表盘 | 知识库数量、文档数量、问答次数统计 | P2 |
| 问答日志 | 查看历史问答记录，用于优化知识库 | P2 |
| 系统配置 | 分块参数、检索 Top-K、相似度阈值等 | P1 |
| API Key 管理 | 管理 DeepSeek API Key 等配置 | P0 |

### 2.4 权限模型

- **无需登录**：公开知识库对所有访客可见，选择即可问答
- **管理后台**：通过独立路径访问，使用管理密钥（Admin Key）认证
- **知识库可见性**：
  - 公开知识库 → 出现在问答页面的知识库列表中
  - 私有知识库 → 仅管理后台可见，不对外暴露

---

## 3. 技术架构

### 3.1 技术栈

| 层次 | 技术选型 | 说明 |
|------|----------|------|
| **前端** | React + TypeScript | 问答界面 + 管理后台 |
| **前端框架** | 待定（Ant Design / shadcn/ui） | UI 组件库 |
| **后端** | Python FastAPI | RESTful API |
| **LLM 编排** | LangChain | 文档加载、分块、Embedding、QA Chain |
| **LLM** | DeepSeek API | Chat（问答生成）+ Embedding（向量化） |
| **向量数据库** | Supabase (pgvector) | 向量存储 + 元数据存储 |
| **对象存储** | 腾讯云 COS | 上传文档存储 |
| **部署** | 腾讯云 EdgeOne | 边缘计算 + CDN + 静态托管 |
| **代码托管** | GitHub | 源码管理、CI/CD |

### 3.2 架构图（逻辑）

```
┌─────────────────────────────────────────────────────────┐
│                      用户浏览器                           │
│  ┌──────────────────┐  ┌──────────────────────────┐     │
│  │   问答界面 (React) │  │  管理后台 (React)         │     │
│  └────────┬─────────┘  └────────────┬─────────────┘     │
└───────────┼─────────────────────────┼───────────────────┘
            │                         │
      ┌─────▼─────┐            ┌─────▼─────┐
      │ FastAPI    │            │ FastAPI    │
      │ /api/qa    │            │ /api/admin │
      └─────┬─────┘            └─────┬─────┘
            │                        │
     ┌──────▼──────┐          ┌──────▼──────┐
     │  LangChain  │          │  文档处理    │
     │  QA Chain   │          │  Pipeline   │
     └──────┬──────┘          └──────┬──────┘
            │                        │
     ┌──────▼────────────────────────▼──────┐
     │            Supabase                   │
     │  ┌──────────────────────────────┐    │
     │  │ pgvector (向量 + 元数据)      │    │
     │  └──────────────────────────────┘    │
     └──────────────────────────────────────┘
            │
     ┌──────▼──────┐
     │ DeepSeek API │
     │ Chat + Embed │
     └─────────────┘
```

### 3.3 数据流

#### 文档入库流程
```
1. 管理员上传文档 → COS 存储原始文件
2. FastAPI 触发文档处理 Pipeline：
   a. LangChain Document Loader 解析文档
   b. Text Splitter 分块
   c. DeepSeek Embedding API 向量化
   d. 写入 Supabase pgvector
3. 返回处理结果（成功/失败/分块数量）
```

#### 问答流程（含 Rerank）
```
1. 用户选择知识库 + 输入问题
2. 问题 → DeepSeek Embedding → 查询向量
3. pgvector 余弦相似度检索 → Top-N 候选片段（粗排，N=20）
4. DeepSeek Rerank API 重排序 → Top-K 精选片段（精排，K=5）
5. 组装 Prompt（系统指令 + 精选上下文 + 用户问题）
6. DeepSeek Chat API 生成回答
7. 返回答案 + 引用来源
```

---

## 4. 非功能需求

### 4.1 性能

| 指标 | 目标值 |
|------|--------|
| 问答响应时间 | P95 < 5 秒 |
| 文档处理延迟 | 单文档 < 30 秒 |
| 并发问答 | 支持 10 QPS |

### 4.2 安全

- Admin Key 认证保护管理后台
- API Key（DeepSeek、Supabase）仅存储在服务端环境变量
- 上传文件类型和大小校验（最大 20MB/文件）
- 文档内容不对外暴露原文，仅通过问答片段引用呈现

### 4.3 可维护性

- 代码托管 GitHub，分支管理（main/dev）
- GitHub Actions CI/CD 自动部署至腾讯云 EdgeOne
- 日志记录问答和文档处理关键节点

### 4.4 成本估算

| 资源 | 预估月费用 | 说明 |
|------|-----------|------|
| DeepSeek API | ¥50-200 | 按 token 计费，低日活下消耗低 |
| Supabase | 免费层 | 2GB 数据库 + 1GB 存储足够初期使用 |
| 腾讯云 EdgeOne | ¥50-200 | 边缘函数 + CDN + 静态托管 |
| 腾讯云 COS | ¥5-20 | 文档存储，初期数据量小 |
| **合计** | **约 ¥100-400/月** | 初期可控制在 ¥200 以内 |

---

## 5. 项目分期与路线图

### Phase 1 — MVP（核心闭环）

| 任务 | 内容 |
|------|------|
| 管理后台基础 | 知识库 CRUD、文档上传/删除、Admin Key 认证 |
| 文档处理 | PDF/Word/MD 解析、分块、DeepSeek Embedding、pgvector 存储 |
| 问答 API | 知识库选择、单轮问答、来源引用、「不知道」处理 |
| 问答页面 | 知识库列表、单轮问答交互 |

### Phase 2 — 增强

| 任务 | 内容 |
|------|------|
| URL 导入 | 输入 URL 抓取网页入库 |
| 批量上传 | 一次上传多个文档 |
| 跨库检索 | 多知识库联合检索 |
| 文档分类 | 文件夹/标签组织 |
| 分块参数配置 | 管理后台可配置分块大小、重叠度、Top-K |

### Phase 3 — 优化

| 任务 | 内容 |
|------|------|
| 仪表盘 | 问答统计图表 |
| 相似问题推荐 | 基于历史问题推荐 |
| 多轮对话 | 上下文记忆的追问能力 |

---

## 6. 已确认决策

| 决策项 | 结论 |
|--------|------|
| 管理后台认证 | Admin Key 纯密钥认证，无需账号密码体系 |
| 问答历史 | 不在 Supabase 持久化存储问答记录，保持轻量 |
| 跨知识库检索 | 允许用户同时勾选多个知识库，联合检索回答 |
| EdgeOne 部署方式 | 导入 Git 仓库（GitHub），配置环境变量，自动构建上线 |

### 6.1 EdgeOne 部署流程

```
GitHub 仓库 → EdgeOne Pages 导入仓库 → 配置环境变量 → 自动构建 → 上线
```

- **环境变量**：DEEPSEEK_API_KEY、SUPABASE_URL、SUPABASE_KEY、ADMIN_KEY、COS_SECRET 等
- **前端**：React SPA 构建后由 EdgeOne Pages 托管静态资源
- **后端**：FastAPI 通过 EdgeOne Functions（边缘函数）运行，或使用 EdgeOne 容器服务

> 注：EdgeOne Functions 对 Python 运行时的支持需进一步验证。若不支持，备选方案为腾讯云 Lighthouse 运行 Docker 容器（FastAPI），EdgeOne 负责前端托管 + CDN + 域名管理。

---

## 7. 附录：关键 LangChain 组件

```python
# 文档加载
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredMarkdownLoader

# 文本分块
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Embedding
from langchain_community.embeddings import DeepSeekEmbeddings  # 或通过 OpenAI 兼容接口

# 向量存储
from langchain_community.vectorstores import SupabaseVectorStore

# Rerank（通过 DeepSeek Rerank API 或 LangChain 内置 Reranker）
from langchain.retrievers import ContextualCompressionRetriever
from langchain_community.document_compressors import DeepSeekRerank  # 或其他兼容 Reranker

# QA Chain
from langchain.chains import RetrievalQA

# 完整检索链（含 Rerank）
# base_retriever = vectorstore.as_retriever(search_kwargs={"k": 20})
# compressor = DeepSeekRerank(top_n=5)
# compression_retriever = ContextualCompressionRetriever(
#     base_compressor=compressor,
#     base_retriever=base_retriever
# )
# qa_chain = RetrievalQA.from_chain_type(
#     llm=llm,
#     retriever=compression_retriever
# )
```
