# 第二阶段 Milestone C 工作计划

本文档用于记录当前 `Agent Phase 2 / Milestone C` 的目标、拆解步骤、验收标准与当前代码现实，方便后续继续开发时直接接上，不需要重新回忆上下文。

## 1. 先记住当前结论

当前执行阶段就是 `Milestone C`。

判断与执行的直接依据是：

- `docs/当前阶段与下一阶段计划.md`
- 当前仓库中的实际代码状态

`Milestone C` 的重点不是继续围绕已有召回与 rerank 做小样本调参，而是：

**把当前已经可用的检索能力，进一步整理成适合规模增长的工程结构。**

## 2. Milestone C 要解决什么

`Milestone C` 在本项目中的定位，不是“把检索重新做一遍”，而是解决两个更偏工程的问题：

1. 当 chunk 数量持续增长后，当前精确向量检索还能不能稳定支撑
2. 当前检索代码是否已经具备“可以安全接入 HNSW、并清楚比较 exact 与 HNSW”的工程形态

因此，`Milestone C` 的关键词不是单独的 “HNSW”，而是：

- 检索策略工程化
- 向量索引性能准备
- exact / HNSW 可切换
- baseline / benchmark 可比较

## 3. 当前代码现实

当前代码已经具备继续往前走的基础，但也有几个明确的工程短板。

### 3.1 已有基础

- 当前检索主链路已具备：
  - 向量召回
  - 关键词召回
  - 融合
  - rerank
- 当前 pipeline 已能输出较完整的 debug / trace 信息
- 当前已有最小 baseline 脚本与评测集

### 3.2 仍待补齐的工程问题

- 当前向量检索仍是 `pgvector + cosine distance` 的精确检索
- 代码里还没有清晰的 `exact / hnsw` 检索策略切换结构
- 数据库 schema 中还没有 HNSW 索引的落地方案
- 配置中缺少 HNSW 相关参数与检索策略开关
- 当前测试更偏向 rerank 行为验证，还不足以支撑 C 阶段的性能与策略验收
- 阶段文档与代码状态需要继续保持同步

## 4. 当前阶段不做什么

为了避免把 `Milestone C` 做散，以下内容当前明确不放进本轮主任务：

- 继续围绕 rerank 做小样本微调
- 现在就回头做完整 BM25 工程化
- 现在就做更大的规则 / 数据联动 PoC
- 现在就引入 `LangChain / LangGraph`
- 现在就解决 OCR 录入问题

这些内容后面都重要，但不属于 `Milestone C` 的主线。

## 5. 建议的推进顺序

`Milestone C` 建议分成四个小步推进，而不是一口气直接“加 HNSW”。

### Step C1：文档与状态收口

这一小步先做一件事：

- 把当前阶段计划与当前 C 阶段计划同步到同一口径

做到后应满足：

- 后续任何人阅读 `docs/` 时，都能清楚知道当前正在做的是 `Milestone C`

### Step C2：检索策略抽象

这一小步的目标不是重写整个 pipeline，而是先把“向量召回策略”从当前实现中抽出来，至少形成：

- `exact` 检索路径
- 未来可替换为 `hnsw` 的接入口

建议优先关注：

- `app/services/retrieval_pipeline.py`
- `app/repositories/policy_repository.py`
- `app/services/retrieval_service.py`
- `app/core/config.py`

这一小步做完后应达到：

- 不破坏现有 `search / ask`
- 不破坏现有混合召回、融合、rerank 行为
- 但可以明确知道当前向量召回到底走的是哪一种策略

### Step C3：HNSW 索引接入与配置补齐

这一小步才是 `Milestone C` 的核心落地点。

建议补齐：

- 数据库 migration 或 schema 增量脚本
- `kb_policy_chunk.embedding` 的 HNSW 索引定义
- HNSW 相关配置项
- `.env.example` 同步说明

这一小步做完后应达到：

- 可以明确创建或启用 HNSW 索引
- 可以在配置层切换 exact / hnsw
- 不会把临时实验参数直接写死在业务代码里

### Step C4：baseline / benchmark 与验收

这一小步是 `Milestone C` 真正的验收动作。

建议至少补齐：

- 当前检索策略标识
- exact 与 hnsw 的对比记录
- 命中效果是否明显退化
- 性能是否有实际收益

建议复用并扩展：

- `app/scripts/run_retrieval_baseline.py`
- `tests/retrieval_eval_set_step_a.json`

如果条件允许，后续可以继续增加：

- 更多制度类型样本
- 更大的评测集
- 更明确的耗时统计

## 6. Milestone C 的验收标准

当前建议把验收标准定得清楚一点，避免最后只落成“数据库里有个索引”。

### 6.1 工程结构验收

- 代码层面能够区分当前使用的是 `exact` 还是 `hnsw`
- 新增配置已同步更新 `config.py` 与 `.env.example`
- 现有 `search / ask / rerank` 主链路没有被破坏

### 6.2 索引落地验收

- 数据库侧已有 HNSW 的可执行落地方案
- 向量字段与索引策略之间的关系有明确说明
- 后续重新部署或迁移时知道应该怎么建索引

### 6.3 效果与性能验收

- 至少有一版 exact vs hnsw 的对比结果
- 现有最小 baseline 不应出现明显回退
- 如果性能收益不明显，也要能清楚说明原因，而不是只保留主观判断

## 7. 当前建议优先看的文件入口

如果现在继续往下推进，建议按这个顺序阅读：

1. `docs/当前阶段与下一阶段计划.md`
2. `docs/第二阶段-MilestoneC工作计划.md`
3. `app/services/retrieval_pipeline.py`
4. `app/repositories/policy_repository.py`
5. `app/core/config.py`
6. `sql/001_kb_policy_schema.sql`
7. `app/scripts/run_retrieval_baseline.py`

这样看完之后，会很清楚：

- 当前 C 阶段为什么要做
- 当前 exact 检索在哪里
- HNSW 应该从哪里接入
- 验收应该靠什么而不是靠体感

## 8. 当前一句话交接

如果继续开发时只看一句话，请记住：

**Milestone C 当前主线不是继续纠结 rerank，而是把当前可用检索底座整理成“可切换 exact / hnsw、可验证性能收益、可支撑规模增长”的工程结构。**
