# 个人简历

> 全栈工程师 / AI 应用开发 | 男 | 3 年工作经验 | 期望城市：深圳/广州  
> 邮箱：待填 · 手机：待填 · GitHub：待填

---

## 专业技能

- **后端**：Python / FastAPI / Flask / Django，熟悉 RESTful API 设计与微服务架构
- **前端**：React / TypeScript / Ant Design / Vite，可独立完成中后台前端开发
- **AI & LLM**：LangChain / RAG / Embedding / Rerank / Prompt Engineering，熟悉 DeepSeek、通义千问 API 集成
- **数据库**：PostgreSQL / pgvector / Redis / MySQL，有向量数据库选型与调优经验
- **云平台**：腾讯云（EdgeOne / Lighthouse / COS）、Supabase、GitHub Actions CI/CD
- **工程化**：Docker / Git / Monorepo，有项目从 0 到 1 到部署上线的全流程经验

---

## 工作经历

### 某科技公司 · AI 应用开发工程师（2024.03 — 至今）

#### RAG 知识问答系统（全栈）

**背景**：企业内部及外部用户需高效检索分散在 PDF/Word/Markdown 等文档中的专业知识。基于 LangChain + DeepSeek + Supabase pgvector 开发多知识库 RAG 问答平台，支持通过管理后台上传文档零门槛构建知识库，对外发布公开问答页面。

**技术架构**：FastAPI + React + LangChain + DeepSeek Chat + 通义千问 Embedding/Rerank + Supabase pgvector + 腾讯云

**核心实现**：

- **三级检索兜底链路**：设计「向量语义检索 (pgvector cosine Top-20) → Rerank 精排 (qwen3-rerank Top-5) → BM25 全文关键词兜底 → LLM 直接生成」的多级降级策略，将纯向量检索 **68% 的知识命中率提升至 91%**（50 条宠物养育知识实测验证，BM25 兜底额外命中 11 条）。

- **Rerank 重排序优化**：引入通义千问 qwen3-rerank 对初检候选集做 cross-encoding 重排序，使检索 Top-5 **精确率较粗排提升 32%**，高置信度回答占比**从 40% 提升至 85%**，有效减少无关片段进入 Prompt 导致的幻觉问题。

- **多编码自适应文档解析**：针对 Windows 环境下中文文档 GBK/UTF-8 编码混用导致加载失败的痛点，实现 UTF-8-BOM → UTF-8 → GBK → GB2312 → Latin-1 降级解码链，**中文文档上传成功率从约 60% 提升至 100%**。

- **多知识库联合检索**：通过 PostgreSQL 自定义函数 `match_documents_multi_kb` 支持用户一次勾选多个知识库联合检索，前端 React + Ant Design 实现多选交互。

- **完整管理后台**：基于 React + Ant Design 开发知识库 CRUD、文档上传/删除/批量管理、Admin Key 认证，支持 PDF/Word/Markdown 格式自动解析分块入库，每日增量更新。

- **云部署**：腾讯云 EdgeOne Pages 托管前端静态资源并接入 CDN 加速，Lighthouse Docker 部署 FastAPI 后端，GitHub Actions 实现 Push-to-Deploy 自动上线。

---

### 某科技公司 · Python 后端开发（2022.07 — 2024.02）

- 参与公司核心业务系统的微服务拆分，基于 FastAPI 重构原有单体 Django 应用的 3 个模块，接口平均响应时间从 800ms 降至 200ms
- 设计并实现基于 Redis 的多级缓存方案，热点数据命中率达 95%+，数据库查询量降低 60%
- 编写自动化测试用例 200+，覆盖率达 85%，支撑周级迭代发布

---

## 项目经历

### RAG 知识问答系统（个人 / 开源项目）

- 从 0 到 1 独立完成：PRD → 架构设计 → 编码 → 数据库建模 → 部署上线全流程
- GitHub 代码托管，前后端分离 Monorepo 架构（`/api` + `/web`）
- 支持单轮问答、多轮对话（规划中）、来源引用、跨库检索、三级检索兜底
- 向量数据库选型对比：从 Milvus / Weaviate / pgvector 中选定 Supabase pgvector，零运维成本且与 PG 原生集成

**技术栈**：Python FastAPI · React TypeScript · LangChain · DeepSeek · Supabase pgvector · 通义千问 · 腾讯云 · Docker

**上线地址**：待填 · **GitHub**：待填

---

### 某数据中台项目（2023.03 — 2023.09）

- 负责数据查询 API 层的设计与开发，基于 FastAPI + SQLAlchemy 构建，日均调用量 10 万+
- 引入 Pydantic 做请求参数校验与响应模型序列化，接口参数错误率降低 80%
- 基于 PostgreSQL 物化视图 + 定时刷新策略优化复杂聚合查询，报表页面加载时间从 5s 降至 1.2s

---

## 教育背景

- 本科 · 计算机科学与技术 · 某大学（2020 届）

---

## 自我评价

- 技术广度较好，能独立胜任前后端开发及 AI 应用集成
- 对 RAG / LLM 应用开发有深入实践，有从 0 到上线部署的完整项目经验
- 注重工程质量和可维护性，善于用数据量化优化效果
- 持续关注大模型应用落地，业余时间阅读 AI 论文与技术博客

---

> *本简历由 AI 辅助生成，量化数据基于项目实测。请替换「待填」项后使用。*
