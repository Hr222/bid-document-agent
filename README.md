# Bid Document Agent

这是一个围绕招投标文档处理场景构建的 AI 项目，也是我对过去一年多 AI 实践的一次阶段性总结。

过去一年多里，我持续关注并动手实践了大模型应用、提示词工程、自动化工作流、知识检索、文档理解，以及面向真实业务场景的 AI 工具落地。这个仓库一方面是我个人 AI 项目经验的汇总入口，另一方面也是我当前正在持续投入的一个实际项目方向: 用 AI 提升招投标文档处理、信息提取、内容生成与辅助决策的效率。

## 项目定位

`bid-document-agent` 旨在探索一个面向招投标业务的智能助手原型，目标包括:

- 理解和解析招标文件、投标文件等复杂文档
- 提取关键信息，例如项目名称、资格要求、评分标准、时间节点等
- 协助生成标准化内容，减少重复劳动
- 为后续构建检索、问答、摘要、比对、风险提示等能力打基础

当前仓库处于早期搭建阶段，先以一个轻量的 FastAPI 服务作为项目起点，后续会逐步补充更完整的 AI 能力模块与业务流程。

## 这个仓库想表达什么

这个项目不只是一个单点 Demo，它更像是我在 AI 方向上的一个持续作品集:

- 总结我过去一年多对 AI 应用开发的理解与实践
- 沉淀从想法验证到业务落地的项目方法
- 结合当前从业中的真实需求，做一个更贴近场景的问题解决方案

我希望它既能记录自己的成长路径，也能逐步演化成一个真正可用的产品雏形。

## 当前技术基础

目前项目采用:

- Python
- FastAPI
- PostgreSQL（计划使用 Docker）
- pgvector（计划作为 PostgreSQL 扩展启用）

现有接口示例:

- `GET /`
- `GET /hello/{name}`

## 本地运行

安装依赖后，可使用如下方式启动:

```bash
uvicorn main:app --reload
```

启动后访问:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/hello/User`

## 本地基础设施

当前推荐使用 Docker 启动本地 PostgreSQL，而不是直接在 Windows 里手动安装数据库。这样更适合作为个人展示项目的可复现开发环境。

### 1. 安装 Docker Desktop

先在 Windows 上安装 Docker Desktop，并确保它可以正常启动。

安装完成后，可以在终端里确认:

```bash
docker --version
docker compose version
```

### 2. 准备环境变量

复制一份环境变量模板:

```bash
copy .env.example .env
```

如果你不是在 Windows CMD 里执行，也可以手动新建 `.env`，内容参考 `.env.example`。

默认配置:

- `POSTGRES_DB=bid_document_agent`
- `POSTGRES_USER=postgres`
- `POSTGRES_PASSWORD=postgres`
- `POSTGRES_PORT=5432`

### 3. 启动 PostgreSQL + pgvector

项目已经提供了 `docker-compose.yml`，直接在仓库根目录运行:

```bash
docker compose up -d
```

第一次启动时会自动:

- 拉取 `pgvector/pgvector:pg17` 镜像
- 创建 PostgreSQL 容器
- 执行初始化脚本
- 启用 `vector` 和 `unaccent` 扩展

### 4. 验证数据库是否可用

查看容器状态:

```bash
docker compose ps
```

查看日志:

```bash
docker compose logs postgres
```

进入数据库:

```bash
docker compose exec postgres psql -U postgres -d bid_document_agent
```

进入后可执行:

```sql
\dx
```

如果能看到 `vector` 扩展，就说明 `pgvector` 已经启用成功。

### 5. 停止和清理

停止容器:

```bash
docker compose down
```

如果你想连数据卷一起清掉，重新初始化数据库:

```bash
docker compose down -v
```

注意: 这会删除容器里的本地数据库数据。

## 后续规划

接下来我计划逐步补充以下能力:

- 文档上传与解析
- 招投标关键信息抽取
- 基于大模型的摘要与问答
- 多文档内容比对
- 招标要求与投标内容的匹配分析
- 面向实际业务流程的智能辅助能力

## 关于我做这个项目的原因

过去一年多，我一直在持续关注 AI 技术如何从“看起来很强”走向“真正能解决问题”。相比纯概念性的尝试，我更希望把 AI 放进真实工作流里，让它承担明确任务、减少重复劳动、提升决策效率。

`Bid Document Agent` 就是在这样的思路下开始的。它既是我对过去 AI 学习和实践的整理，也承载着我当前职业方向中一个非常具体、非常现实的应用场景。

## 状态说明

项目仍在持续开发中，当前版本主要用于搭建基础结构与明确演进方向。后续会随着功能完善不断更新。
