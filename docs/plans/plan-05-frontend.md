# Plan-05：前端模块

> 关联：[Plan-01 项目总览](./plan-01-overview.md) | PRD §2.2, §2.3

---

## 1. 模块职责

React SPA，包含两个独立区域：**问答页面**（公开）+ **管理后台**（Admin Key 保护）。

---

## 2. 技术选型

| 项 | 选型 | 说明 |
|----|------|------|
| 框架 | React 18 + TypeScript | SPA |
| 构建 | Vite | 快速构建 |
| 路由 | React Router v6 | 问答页 + 管理后台路由 |
| HTTP | Axios / fetch | API 调用 |
| UI 组件 | Ant Design 或 shadcn/ui | 开箱即用 |
| 状态管理 | React Context + useReducer | MVP 阶段够用，不需要 Redux |
| 样式 | CSS Modules 或 Tailwind | 按 UI 库配合决定 |

---

## 3. 路由设计

```
/                          → 问答主页（公开）
/admin                     → 重定向到 /admin/login
/admin/login               → Admin Key 输入页
/admin/dashboard           → 知识库管理主页
/admin/kb/:id              → 知识库详情 + 文档管理
/admin/settings            → 系统配置（Phase 2）
```

---

## 4. 页面设计

### 4.1 问答主页 `/`

```
┌─────────────────────────────────────────────────────┐
│  🧠 RAG 知识问答                         [管理后台]  │
├─────────────────────────────────────────────────────┤
│                                                     │
│    选择一个知识库开始提问                              │
│                                                     │
│  ┌─ 知识库卡片列表（多选）─────────────────────────┐  │
│  │ [✓ 技术笔记] [✓ 产品文档] [  法律知识] ...      │  │
│  └─────────────────────────────────────────────────┘  │
│                                                     │
│  ┌─────────────────────────────────────────────────┐  │
│  │  输入你的问题...                        [发送]  │  │
│  └─────────────────────────────────────────────────┘  │
│                                                     │
│  ┌─ 回答区域 ──────────────────────────────────────┐  │
│  │                                                 │  │
│  │  RAG（检索增强生成）是一种将信息检索与大语言模型  │  │
│  │  结合的技术...                                   │  │
│  │                                                 │  │
│  │  📎 来源：                                      │  │
│  │  · RAG入门指南.pdf  相关性: 92%                  │  │
│  │  · AI技术综述.md    相关性: 85%                  │  │
│  │                                                 │  │
│  └─────────────────────────────────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 4.2 管理后台 `/admin/login`

```
┌────────────────────────────────────────┐
│                                        │
│         🔐 管理后台登录                  │
│                                        │
│  ┌──────────────────────────────────┐  │
│  │  Admin Key                       │  │
│  └──────────────────────────────────┘  │
│                                        │
│  [登录]                                │
│                                        │
└────────────────────────────────────────┘
```

### 4.3 管理后台 `/admin/dashboard`

```
┌─────────────────────────────────────────────────────┐
│  📋 知识库管理                          [⚙ 设置]    │
├─────────────────────────────────────────────────────┤
│  [+ 新建知识库]                                     │
│                                                     │
│  ┌──────────────────┐ ┌──────────────────┐          │
│  │ 📘 技术笔记       │ │ 📗 产品文档       │          │
│  │ 公开 · 42篇文档   │ │ 私有 · 15篇文档   │          │
│  │ [编辑] [删除]     │ │ [编辑] [删除]     │          │
│  └──────────────────┘ └──────────────────┘          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 4.4 管理后台 `/admin/kb/:id`

```
┌─────────────────────────────────────────────────────┐
│  ← 返回   知识库：技术笔记              [编辑信息]   │
├─────────────────────────────────────────────────────┤
│  [📤 上传文档]  [🔗 导入URL]              搜索...   │
│                                                     │
│  ┌─────────────┬──────────┬────────┬──────────────┐ │
│  │ 文档名       │ 分块数    │ 上传时间 │ 操作          │ │
│  ├─────────────┼──────────┼────────┼──────────────┤ │
│  │ Python笔记.md│ 38       │ 06-26  │ [查看] [删除] │ │
│  │ RAG入门.pdf │ 120      │ 06-25  │ [查看] [删除] │ │
│  └─────────────┴──────────┴────────┴──────────────┘ │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 5. 组件树

```
App
├── QAPage                          # 问答主页
│   ├── Header (Logo + 管理后台链接)
│   ├── KnowledgeBaseSelector       # 知识库多选
│   │   └── KBCard[]                # 知识库卡片
│   ├── QuestionInput               # 问题输入框 + 发送按钮
│   └── AnswerPanel                 # 回答展示
│       ├── AnswerContent           # 回答正文（Markdown 渲染）
│       └── SourceList              # 来源引用列表
│           └── SourceItem[]        # 单条引用
│
├── AdminLayout                     # 管理后台布局
│   ├── AdminLogin                  # Admin Key 输入
│   ├── AdminDashboard              # 知识库列表
│   │   ├── CreateKBDialog          # 新建知识库弹窗
│   │   └── KBCard[]                # 知识库卡片
│   ├── AdminKBDetail               # 知识库详情
│   │   ├── EditKBInfo              # 编辑知识库信息
│   │   ├── UploadDocument          # 上传文档（拖拽区域）
│   │   ├── ImportURL               # URL 导入（Phase 2）
│   │   └── DocumentTable           # 文档列表表格
│   │       └── DocumentRow[]       # 文档行
│   └── AdminSettings               # 系统配置（Phase 2）
│
└── ErrorPage (404)
```

---

## 6. 状态管理

```ts
// 问答页状态
interface QAState {
  selectedKBIds: string[];      // 已选知识库
  question: string;              // 当前问题
  loading: boolean;              // 加载中
  answer: AnswerResult | null;   // 回答结果
  error: string | null;          // 错误信息
}

// 管理后台状态
interface AdminState {
  isAuthenticated: boolean;      // Admin Key 已验证
  adminKey: string;              // 缓存的 Key（sessionStorage）
}
```

---

## 7. API 调用封装

```ts
// api/client.ts
const API_BASE = import.meta.env.VITE_API_BASE || '/api';

export async function apiGet<T>(path: string, adminKey?: string): Promise<T>
export async function apiPost<T>(path: string, body: any, adminKey?: string): Promise<T>
export async function apiUpload<T>(path: string, file: File, adminKey: string): Promise<T>
export async function apiDelete<T>(path: string, adminKey: string): Promise<T>
```

---

## 8. 待实现 Checklist

- [ ] Vite + React + TypeScript 项目脚手架
- [ ] React Router 路由搭建
- [ ] 问答主页 — 知识库选择器
- [ ] 问答主页 — 问题输入 + 回答展示
- [ ] 管理后台 — Admin Key 登录页
- [ ] 管理后台 — 知识库列表 + 新建/编辑/删除
- [ ] 管理后台 — 文档上传 + 列表 + 删除
- [ ] API Client 封装
- [ ] 响应式适配
- [ ] URL 导入页面（Phase 2）
- [ ] 批量上传（Phase 2）
- [ ] 系统配置页面（Phase 2）
