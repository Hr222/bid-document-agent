# Bid Document Agent

这是一个围绕招投标与企业资料知识库场景构建的 AI 工程化个人项目。

对我来说，它不只是一个功能型 Demo，更像是我过去一年多学习和实践 AI 工程化的一次阶段性表达：我希望把自己对 RAG、LLM、工作流编排、后端服务、前端管理界面，以及“如何把 AI 真正放进业务流程里”的理解，落成一个持续演进、可以展示、也可以继续做深的项目。

## 我为什么做这个项目

过去一年多里，我持续关注并动手实践了这些方向：

- 大模型应用
- 提示词工程
- RAG 与知识检索
- 文档理解与信息抽取
- 自动化工作流
- 面向真实业务场景的 AI 工具落地

相比“单次调用模型就结束”的演示，我更关心的是：

- 数据怎么进入系统
- 知识怎么被结构化和检索
- 问答结果怎么回溯到原文
- 系统怎么被维护，而不是只靠脚本一次性跑完
- 一个 AI 项目怎么逐步长成真正可用的产品雏形

`Bid Document Agent` 就是在这样的思路下开始的。

## 项目定位

`bid-document-agent` 旨在对我曾经做过的业务, 围绕这些可挖掘的知识点, 业务点作为一个系统的回顾和展示，当前核心定位是：

- 用 RAG 建立可维护的企业知识库
- 用 LLM 进行基于知识库的问答与辅助生成
- 用后端服务把知识库、检索、问答能力产品化
- 用前端管理界面把“数据维护”和“效果验证”可视化

当前整体技术构成定位为：

- RAG
- LLM
- LangGraph / LangChain
- FastAPI
- React
- PostgreSQL + pgvector

## 当前阶段

当前项目的第一阶段，不是追求一个“大而全”的 AI 系统，而是先把 **RAG 的最小闭环** 做扎实。

我当前选择的首批知识库样板是两类资料：

- `公司制度`
- `绩效标准`

这样选择的原因很直接：

- `公司制度` 适合做章节化、条款化、可引用的制度型知识库
- `绩效标准` 适合做第二种资料样板，用来验证不同类型资料也能接入同一套 RAG 流程
- 这两类资料都足够有业务代表性，适合作为 MVP 展示

这里强调一下：当前阶段用到的样板资料只是用于搭建和展示流程，不代表未来知识库范围就只停留在这两类。

## 当前阶段目标

第一阶段目标可以概括为一句话：

**先做出一个“可入库、可检索、可问答、可维护、可验证”的 RAG MVP。**

这个 MVP 重点不是“模型聊得多聪明”，而是把以下链路打通：

1. 文档进入知识库
2. 文本被解析、清洗、切分
3. 索引和向量建立完成
4. 前端可以维护和查看知识库内容
5. 用户可以基于知识库进行问答
6. 答案可以回溯到命中的原文片段
7. 最后对召回效果进行测试和验证

## MVP 范围

当前最小 MVP 的范围是：

### 1. 知识库入库

支持将样板资料接入知识库，至少完成：

- 文档登记
- 版本记录
- 文本抽取
- 章节拆分
- chunk 切分
- embedding 写入

### 2. 检索能力

支持基于用户问题进行检索，并能看到：

- 命中的文档
- 命中的章节或片段
- 相对相关的召回结果

### 3. LLM 问答

支持基于检索结果进行问答，并尽量提供：

- 回答内容
- 引用出处
- 对应原文片段

### 4. 前端维护

支持一个最小知识库管理界面，用来展示和维护：

- 已入库文档列表
- 文档状态
- 文档详情
- 检索测试
- 问答测试

### 5. 效果验证

在 MVP 跑通后，对召回效果做基础测试，例如：

- 预设问题集
- 命中率观察
- 召回片段是否相关
- 是否能支持答案回溯

## 我对这个项目的工程化理解

这不是一个“先接个模型 API，再包一层页面”的项目。

我更希望它体现出我对 AI 工程化的一些真实理解：

### 1. RAG 的核心不只是向量化

真正重要的是：

- 数据怎么进来
- 结构怎么定义
- chunk 怎么切
- 元数据怎么保留
- 命中后怎么回溯
- 效果怎么验证

### 2. 知识库不是一次性脚本

知识库后面一定需要维护，所以前端管理能力不是锦上添花，而是产品化的必要部分。

### 3. LLM 不是替代检索，而是建立在检索之上

先把底层知识库和召回做好，再谈工作流编排、多步推理、复杂 Agent，才更稳。

### 4. 评估必须前置

如果没有召回测试、问题集和基本验证机制，那 RAG 很容易停留在“看起来能跑”，而不是“真的可用”。

## 当前知识库设计方向

当前仓库里的知识库表结构，第一阶段重点服务于制度类知识库，也就是：

- 一项制度对应一条主档
- 一个具体制度文件对应一个版本
- 版本下可以拆章节
- 章节下再切 chunk

当前相关 SQL 设计见：

- [sql/001_kb_policy_schema.sql](D:/workspace/bid-document-agent/sql/001_kb_policy_schema.sql)
- [sql/README-policy-schema.md](D:/workspace/bid-document-agent/sql/README-policy-schema.md)

## 项目路线图

### 阶段一：RAG MVP

目标：

- 用 `公司制度` 和 `收费标准` 做样板知识库
- 打通入库、检索、问答、维护、验证闭环

产出：

- 可运行的知识库后端
- 可查看的前端管理界面
- 可验证的问答与召回流程

### 阶段二：知识库能力增强

目标：

- 优化 chunk 策略
- 优化检索效果
- 完善元数据过滤
- 增强问答引用能力

产出：

- 更稳定的召回质量
- 更可控的答案生成效果

### 阶段三：流程与智能体扩展

目标：

- 在稳定 RAG 基础上引入 LangGraph / LangChain 流程编排
- 扩展到更多业务任务，例如摘要、比对、辅助生成

产出：

- 从单一知识问答逐步演进到更完整的业务型 AI 助手

## 本地运行

安装依赖后，可使用如下方式启动：

```bash
uvicorn app.main:app --reload
```

启动后访问：

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/hello/User`

## Python 依赖安装

考虑到这是个人项目，当前只保留两份依赖文件：

- `requirements-prod.txt`
  - 面向部署和正式运行
- `requirements-dev.txt`
  - 面向本地开发，直接保留全量依赖，并带注释说明

安装生产环境依赖：

```bash
pip install -r requirements-prod.txt
```

安装本地开发全量依赖：

```bash
pip install -r requirements-dev.txt
```

说明：

- `dev` 环境已经包含当前阶段大部分需要的 Python 依赖
- 包括 FastAPI、数据库、pgvector、文档解析、OpenAI、LangChain、LangGraph、OCR、测试和代码检查
- React 前端依赖后续单独放在前端工程中管理，不混在 Python 的 `pip` 文件中

## 本地基础设施

当前推荐使用 Docker 启动本地 PostgreSQL，而不是直接在 Windows 里手动安装数据库。这样更适合作为个人展示项目的可复现开发环境。

### 1. 安装 Docker Desktop

先在 Windows 上安装 Docker Desktop，并确保它可以正常启动。

安装完成后，可以在终端里确认：

```bash
docker --version
docker compose version
```

### 2. 准备环境变量

复制一份环境变量模板：

```bash
copy .env.example .env
```

如果你不是在 Windows CMD 里执行，也可以手动新建 `.env`，内容参考 `.env.example`。

默认配置：

- `POSTGRES_DB=bid_document_agent`
- `POSTGRES_USER=admin`
- `POSTGRES_PASSWORD=123456`
- `POSTGRES_PORT=5432`

### 3. 启动 PostgreSQL + pgvector

项目已经提供 PostgreSQL 的 Compose 文件，建议在仓库根目录显式指定 `.env` 和 Compose 文件路径：

```bash
docker compose --env-file .env -f docker\postgres\docker-compose.yml up -d
```

第一次启动时会自动：

- 拉取 `pgvector/pgvector:pg17` 镜像
- 创建 PostgreSQL 容器
- 执行初始化脚本
- 启用 `vector` 和 `unaccent` 扩展

### 4. 验证数据库是否可用

查看容器状态：

```bash
docker compose --env-file .env -f docker\postgres\docker-compose.yml ps
```

查看日志：

```bash
docker compose --env-file .env -f docker\postgres\docker-compose.yml logs postgres
```

进入数据库：

```bash
docker compose --env-file .env -f docker\postgres\docker-compose.yml exec postgres psql -U admin -d bid_document_agent
```

进入后可执行：

```sql
\dx
```

如果能看到 `vector` 和 `unaccent` 扩展，就说明初始化已经成功。

## 状态说明

项目仍在持续开发中，当前版本主要用于搭建第一阶段的 RAG MVP。后续会随着知识库能力、前端界面和评估体系的完善不断更新。
