# 第二阶段 Milestone A 进度记录

本文档用于记录当前 `Agent Phase 2 / Milestone A` 已完成内容、当前边界、验证结果与下一步建议，方便后续继续开发时快速恢复上下文。

## 1. 当前里程碑目标

`Milestone A` 的目标不是立刻提升检索效果，而是先把当前检索能力整理成一个更适合继续演进的底座。

当前里程碑主要包含两部分：

1. 检索链路抽象与调试能力增强
2. 最小评测集与 baseline

本次实际完成的是第 `1` 部分，第 `2` 部分尚未开始。

## 2. 本次已完成内容

### 2.1 检索链路抽象为独立 pipeline

已新增：

- `app/services/retrieval_pipeline.py`

当前已经把原有的单路向量检索流程整理成一个独立的 pipeline 骨架。

当前 pipeline 仍然保持原行为，流程是：

1. 用户问题做 embedding
2. 基于 `pgvector` 做精确向量召回
3. 基于 `retrieval_min_score` 做低分过滤

说明：

- 当前没有加入关键词召回
- 当前没有加入混合检索
- 当前没有加入 rerank
- 当前没有加入 HNSW

也就是说，本次是“结构抽象”，不是“召回策略升级”。

### 2.2 后端响应补充检索调试信息

已更新：

- `app/schemas/retrieval.py`
- `app/services/retrieval_service.py`

当前检索返回结构中已经新增 `debug` 信息，主要包括：

- `pipeline`
- `strategy`
- `min_score`
- `stages`

其中 `stages` 当前可看到：

- `query_embedding`
- `vector_recall`
- `score_filter`

这一步的意义是：后续做混合检索、rerank、召回融合时，不需要重新设计整套返回结构。

### 2.3 每条检索命中结果补充来源与分数拆解

已更新：

- `app/schemas/retrieval.py`
- `app/services/retrieval_service.py`

当前每条 `hit` 已新增：

- `retrieval_source`
- `score_breakdown`

在当前单路向量检索下，表现为：

- `retrieval_source = vector`
- `score_breakdown = {"vector": 当前分数}`

这也是为后续混合检索提前预留结构。

### 2.4 `/retrieval/ask` 接口保留检索调试上下文

已更新：

- `app/api/routes/retrieval.py`

当前 `ask` 接口除了返回：

- `answer`
- `citations`
- `hits`

也会同时返回对应的 `debug` 信息。

这样即使用户走的是“检索并提问”链路，仍然可以看到这次问答背后的检索过程。

### 2.5 前端调试台展示检索调试信息

已更新：

- `frontend/src/types/retrieval.ts`
- `frontend/src/components/RetrievalResultPanel.tsx`
- `frontend/src/constants/uiText.ts`

当前检索调试台已经可以看到：

- 当前 pipeline 名称
- 当前 strategy 名称
- 当前最小分数阈值
- 检索阶段列表
- 每条 hit 的来源
- 每条 hit 的分数拆解

这意味着当前调试台已经从“只看结果”演进为“可观察检索过程”。

## 3. 本次改动涉及文件

### 新增文件

- `app/services/retrieval_pipeline.py`
- `docs/第二阶段-MilestoneA进度记录.md`

### 已修改文件

- `app/api/routes/retrieval.py`
- `app/schemas/__init__.py`
- `app/schemas/retrieval.py`
- `app/services/retrieval_service.py`
- `frontend/src/components/RetrievalResultPanel.tsx`
- `frontend/src/constants/uiText.ts`
- `frontend/src/types/retrieval.ts`
- `tests/test_retrieval.py`
- `docs/当前阶段与下一阶段计划.md`
- `docs/RAG学习笔记.md`

## 4. 本次未做内容

以下内容仍未开始，属于 `Milestone A` 后续工作或 `Milestone B` 之后的工作：

- 最小评测集
- baseline
- 关键词召回
- 混合检索
- rerank
- HNSW

## 5. 当前阶段准确定位

当前进度不应表述为“检索效果已经升级”，而应表述为：

**当前已经完成第二阶段第一批底座工作：把现有单路向量检索整理成可扩展、可观察、可继续演进的检索结构。**

换句话说：

- 当前不是“效果优化完成”
- 当前是“为后续效果优化做好结构准备”

## 6. 已完成验证

本次改动后，已完成以下验证：

- `python -m pytest tests/test_retrieval.py`
- `npm run build`

验证结果：

- 检索测试通过
- 前端构建通过

## 7. 建议下一步

建议下一步直接进入 `Milestone A` 的第二部分：

### 7.1 先建立最小评测集

建议先准备一小批标准问题，至少覆盖：

- 文档级命中
- 章节级命中
- chunk 级相关性

### 7.2 再记录当前 baseline

在当前“只有单路向量检索”的前提下，先记录：

- 哪些问题能命中
- 哪些问题命不中
- 哪些问题命中了但排序不好

这样后面引入：

- 关键词召回
- 混合检索
- rerank

时，才有明确对比依据。

## 8. 一句话交接

如果后续继续开发时只看一句话，请记住：

**Milestone A 当前只完成了“检索链路抽象 + 调试能力增强”，还没有进入“评测集 + baseline”阶段。**
