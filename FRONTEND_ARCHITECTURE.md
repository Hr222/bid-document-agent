# Frontend Architecture

## 1. 文档定位

本文档描述项目独立前端应用的工程结构、技术选型、页面边界、请求规范和演进方向。

本文档与根目录的 `ARCHITECTURE.md` 对齐，前端作为独立的应用层存在，通过稳定的 HTTP API 与后端交互。

前端不直接依赖 GLM、LangChain 或 LangGraph 的具体实现，只依赖后端提供的业务接口。

## 2. 前端职责

| 职责 | 说明 |
|---|---|
| Agent 工作台 | 提供 Agent 选择、任务创建、任务状态和结果展示 |
| 知识库界面 | 管理知识库、上传文档、查看处理状态和执行检索 |
| Tender Agent | 提供投标书相关任务入口和结果预览 |
| 用户交互 | 处理上传、表单、进度、错误、重试和下载 |
| API 调用 | 通过统一 Axios 客户端访问后端 |
| 状态管理 | 管理页面状态、服务端状态和异步任务状态 |
| 类型约束 | 使用 TypeScript 保证前后端数据结构清晰 |

前端不负责：

| 不负责内容 | 归属 |
|---|---|
| GLM 调用 | 后端 LLM 层 |
| LangChain 组装 | 后端应用或编排层 |
| LangGraph 编排 | 后续后端 Agent 编排层 |
| 文档解析和向量化 | 后端知识库能力 |
| 投标书业务规则 | 后端 Tender Agent |
| 数据库访问 | 后端基础设施层 |

## 3. 技术选型

| 层级 | 选型 | 约束 |
|---|---|---|
| 框架 | React 18 | 复用现有工程 |
| 开发语言 | TypeScript | `strict: true` |
| 构建工具 | Vite | 复用现有 Vite 工程 |
| JavaScript 标准 | ES2022 | 使用现代 ES8+ 语法 |
| UI 组件库 | Ant Design 5 | 支持企业级工作台和文档管理 |
| 图标 | lucide-react | 保持现代、简洁的视觉风格 |
| 路由 | React Router | 管理 Agent、知识库和任务页面 |
| HTTP 客户端 | Axios | 统一请求、错误、超时和上传进度 |
| 服务端状态 | TanStack React Query | 缓存、轮询、重试和请求状态 |
| 表单校验 | Ant Design Form + Zod | 兼顾交互和运行时校验 |
| 样式 | Ant Design Token + CSS Modules | 支持主题定制和局部隔离 |
| 单元测试 | Vitest + React Testing Library | 测试组件和业务交互 |
| 端到端测试 | Playwright | 测试上传、任务和下载链路 |

不使用原生 `fetch` 作为项目请求入口，也不再额外封装 Fetch。

## 4. 工程边界

项目已经存在 `frontend` 前端工程，后续只在该工程内进行改造。

| 约束 | 要求 |
|---|---|
| 前端工程 | 继续使用现有 `frontend` |
| 包管理 | 不新建第二套前端包 |
| 配置文件 | 在现有 Vite、TypeScript 配置基础上调整 |
| 依赖管理 | 只允许修改现有 `frontend/package.json` |
| 现有组件 | 逐步重构和复用，不直接废弃 |
| 后端接口 | 保持现有接口能力，新增功能需先明确契约 |
| UI 改造 | 采用渐进式改造，避免一次性重写 |

## 5. 前端分层结构

```text
frontend/
└── src/
    ├── app/
    │   ├── router.tsx
    │   ├── providers.tsx
    │   └── appConfig.ts
    ├── layouts/
    │   └── AgentWorkspaceLayout.tsx
    ├── features/
    │   ├── knowledge-base/
    │   │   ├── pages/
    │   │   ├── components/
    │   │   ├── hooks/
    │   │   ├── api/
    │   │   └── types.ts
    │   └── agent/
    │       └── tender/
    │           ├── pages/
    │           ├── components/
    │           ├── hooks/
    │           ├── api/
    │           └── types.ts
    ├── services/
    │   └── http/
    │       ├── axiosClient.ts
    │       ├── errorHandler.ts
    │       └── requestTypes.ts
    ├── shared/
    │   ├── components/
    │   ├── constants/
    │   ├── types/
    │   └── utils/
    ├── styles/
    │   ├── theme.ts
    │   └── global.css
    └── main.tsx
```

现有的上传、检索和结果组件应迁移到对应的业务模块中，而不是继续全部集中在 `App.tsx`。

## 6. 模块关系

```text
Agent Workspace
├── Knowledge Base
│   ├── Knowledge Base List
│   ├── Document Upload
│   ├── Document Processing Status
│   └── Retrieval
└── Agents
    └── Tender Agent
        ├── Task Creation
        ├── Task Status
        ├── Knowledge Base Selection
        └── Tender Skeleton Preview
```

知识库属于平台共享能力，不放入 `tender` 模块内部。

后续扩展财务或风控 Agent 时，保持以下结构：

```text
features/agent/
├── tender/
├── finance/
└── risk/
```

## 7. Axios 请求规范

所有后端请求必须经过统一 Axios Client。

```text
Page Component
    ↓
React Query Hook
    ↓
Business API
    ↓
Axios Client
    ↓
Backend API
```

| 能力 | 统一处理方式 |
|---|---|
| API 前缀 | 统一使用 `/api` |
| 超时 | Axios Client 统一配置 |
| 请求头 | 统一注入 |
| 认证信息 | 由请求拦截器预留 |
| 错误转换 | 响应拦截器转换为统一错误结构 |
| 文件上传 | 使用 Axios 上传进度回调 |
| 请求取消 | 使用 AbortSignal |
| 日志调试 | 在开发环境记录请求方法、路径和耗时 |
| 页面请求 | 不允许组件直接创建 Axios 请求 |

业务 API 只负责描述业务接口，不负责处理页面状态。

## 8. 状态管理规范

| 状态类型 | 管理方式 |
|---|---|
| 输入框、弹窗、Tab | React State |
| 后端数据 | TanStack React Query |
| 上传进度 | Axios 回调结合组件状态 |
| 异步任务状态 | React Query 轮询 |
| 跨页面临时状态 | 必要时使用 Zustand |
| 全局业务状态 | 默认不建立，避免过早引入复杂状态管理 |

前端不使用 Redux 作为默认状态管理方案。

## 9. 页面规划

| 页面 | 路由 | 主要能力 |
|---|---|---|
| Agent 工作台 | `/agents` | 查看 Agent 列表和运行状态 |
| Tender Agent | `/agents/tender` | 创建投标书处理任务 |
| Tender 任务详情 | `/agents/tender/tasks/:taskId` | 查看任务进度和结果 |
| 知识库首页 | `/knowledge-bases` | 查看知识库列表 |
| 知识库详情 | `/knowledge-bases/:id` | 管理知识库文档 |
| 文档上传 | `/knowledge-bases/:id/documents/upload` | 上传和处理文件 |
| 知识库检索 | `/knowledge-bases/:id/search` | 执行检索并查看结果 |
| Workflow | `/workflow` | 预留入口，暂不实现复杂编排 |

## 10. 知识库 UI 改造范围

当前已有知识库入库能力，本阶段重点是把临时界面改造成正式产品页面。

| 功能 | 改造目标 |
|---|---|
| 知识库列表 | 展示名称、描述、文档数量、更新时间和状态 |
| 创建知识库 | 提供正式表单和校验 |
| 文档上传 | 支持拖拽、批量上传和上传进度 |
| 文档列表 | 展示文件名、类型、大小、处理状态和时间 |
| 处理状态 | 展示待处理、处理中、已完成和失败 |
| 失败处理 | 显示错误信息并支持重新处理 |
| 文档删除 | 提供明确确认和结果反馈 |
| 文档详情 | 查看文档元信息和处理状态 |
| 检索页面 | 统一搜索输入、结果卡片和来源文档展示 |
| 空状态 | 为无知识库、无文档、无检索结果提供引导 |

## 11. Tender Agent UI 范围

F1 阶段的 Tender Agent 只实现基础任务闭环。

```text
选择或上传文件
    ↓
创建 Tender 任务
    ↓
查询任务状态
    ↓
生成投标书章节骨架
    ↓
预览章节结构
    ↓
下载骨架文档
```

| 功能 | F1 是否实现 |
|---|---:|
| Tender Agent 入口 | 是 |
| 选择知识库 | 是 |
| 上传招标文件 | 是 |
| 创建异步任务 | 是 |
| 任务状态展示 | 是 |
| 错误和重试 | 是 |
| 投标书章节骨架 | 是 |
| 骨架预览 | 是 |
| 骨架下载 | 是 |
| 完整投标书正文生成 | 否 |
| 多 Agent 协作 | 否 |
| LangGraph Workflow 画布 | 否 |
| 完整 Chat 工作台 | 预留 |

前端只面向任务接口，不直接绑定 GLM、LangChain 或 LangGraph。

## 12. UI 视觉方向

AetherFlow 作为视觉参考，但不直接复制其导出代码。

| 区域 | 设计方向 |
|---|---|
| 侧边栏 | 深色背景，展示 Agent 和平台模块 |
| 顶部导航 | 显示当前工作区、任务状态和用户信息 |
| 主工作区 | 浅色背景，突出任务和文档内容 |
| 卡片 | 圆角、弱边框、清晰层级 |
| 主色 | 蓝色或蓝绿色，用于操作和状态强调 |
| 状态色 | 成功、处理中、失败分别保持明确区分 |
| 文档树 | 使用 Tree 展示章节层级 |
| 响应式 | 优先适配桌面端，保留平板可用性 |
| 可读性 | 深色区域不承载大段正文内容 |

## 13. TypeScript 规范

| 规则 | 要求 |
|---|---|
| 类型检查 | 开启 `strict` |
| `any` | 默认禁止 |
| API 类型 | 请求和响应分别定义 |
| 组件 Props | 所有公共组件必须声明类型 |
| 状态值 | 使用联合类型或明确枚举 |
| 错误对象 | 使用统一错误类型 |
| 文件类型 | 区分浏览器 `File` 和后端文件记录 |
| 命名 | 组件使用 PascalCase，变量使用 camelCase |
| 导入 | 避免跨业务模块直接引用内部文件 |
| 模块边界 | 业务模块通过公共 API 或 shared 层交互 |

## 14. F1 验收标准

| 验收项 | 标准 |
|---|---|
| 工程 | 使用现有 `frontend`，没有新建前端包 |
| 请求 | 所有 API 通过 Axios Client |
| 知识库 | 可以完成创建、查看和管理 |
| 文档 | 可以上传、查看状态、失败重试和删除 |
| 检索 | 可以完成查询并展示来源 |
| Agent | 可以创建 Tender 任务 |
| 任务 | 可以展示处理中、完成和失败状态 |
| 结果 | 可以展示投标书章节骨架 |
| 视觉 | 页面整体统一为 AetherFlow 风格 |
| 代码 | TypeScript 严格检查通过 |
| 兼容性 | 不破坏现有后端接口和已有能力 |

## 15. 非目标

F1 阶段暂不包含以下内容：

| 内容 | 原因 |
|---|---|
| 重做知识库后端 | 当前已有入库能力 |
| 更换 GLM 客户端 | 属于后端 LLM 层 |
| 前端接入 LangChain | LangChain 属于后端调用和编排 |
| LangGraph 编排画布 | 等多 Agent 需求明确 |
| 完整投标书生成 | F1 只验收结构骨架 |
| 移动端专门适配 | 当前以桌面工作台为主 |
| 新建独立前端包 | 项目已有 `frontend` 工程 |

## 16. 实施结论

F1 的前端目标确定为：

> 在现有 `frontend` 工程内，使用 React + TypeScript + Ant Design 5，基于 Axios 和 TanStack Query，完成 AetherFlow 风格的 Agent 工作台、正式知识库 UI，以及 Tender Agent 的基础任务闭环。

前端作为独立应用层存在，知识库作为平台共享能力，Tender 作为 Agent 下的业务模块。前端通过稳定 API 与后端交互，不感知后端具体使用的 LLM、LangChain 或 LangGraph 实现。
