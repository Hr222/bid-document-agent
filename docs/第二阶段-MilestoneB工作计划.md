# 第二阶段 Milestone B 工作计划

本文档用于记录当前 `Agent Phase 2 / Milestone B` 的目标、拆解步骤、验收标准与前置结论，方便明天继续开发时直接接上，不需要重新回忆上下文。

## 1. 先记住当前结论

`Milestone A` 已完成，已经收尾的内容包括：

1. 检索链路抽象为独立 pipeline
2. 检索 debug 信息打通到后端与前端
3. 命中结果补充来源与分数拆解
4. 最小评测集与 baseline 脚本落仓
5. 基于本地测试库完成了一次真实 baseline 验证

当前 `Milestone A` 的准确定位不是“效果优化完成”，而是：

**已经把单路向量检索整理成可扩展、可调试、可继续评测的底座。**

## 2. Milestone B 要解决什么

`Milestone B` 不是一口气把所有高级检索能力全做完，而是先解决当前 baseline 已经暴露出来的两个现实问题：

1. 制度条款类问法，单纯向量召回的第一名不够稳定
2. 期望条款虽然常常能进 `top3`，但不一定能排到 `top1`

当前真实 baseline 中，已经有两个很适合拿来驱动开发的例子：

- `HR-001`：“人事管理制度适用于哪些人”
  - 期望条款：`第二条`
  - 当前 top1：`第一条`
  - 期望结果已进入 `top2`
- `HR-002`：“员工试用期多久”
  - 期望条款：`第五条`
  - 当前 top1：`第六十一条`
  - 期望结果已进入 `top3`

所以 `Milestone B` 的核心目标很明确：

**先把“召回更稳、排序更准”做出第一轮落地，不追求一步到位。**

## 3. 明天建议直接做的最小步骤

### Step B1：补一个最小可用的关键词召回

这一步只做一件事：在现有向量召回旁边，加一条最小可用的关键词召回路径。

建议优先查看和改动：

- `app/repositories/policy_repository.py`
- `app/services/retrieval_pipeline.py`
- `app/services/retrieval_service.py`

这一步做完应达到：

- 输入查询后，除了向量召回，还能拿到一份关键词召回结果
- 调试信息里能看到关键词召回阶段
- 每条命中结果能标明来源是 `vector`、`keyword` 或后续融合结果

这一步暂时不要追求：

- BM25 完整工程化
- 复杂权重调参
- rerank

### Step B2：把双路召回接进当前 pipeline

这一步的目标是让 pipeline 不再只有单一路径，而是能够顺序执行：

1. 查询 embedding
2. 向量召回
3. 关键词召回
4. 结果融合
5. 分数过滤

建议优先关注：

- `debug.stages` 的输出不要丢
- `RetrievalSearchResponse` 的结构尽量不推翻，只做增量扩展

这一步做完应达到：

- `search` 和 `ask` 都能走双路召回
- 前端调试台能看到新增阶段
- 不破坏现有接口调用方式

### Step B3：先做最简单的融合规则

这一步不要上来就做复杂算法，先用足够简单、明白、可解释的融合规则。

建议第一版直接采用：

- 按 `chunk_id` 去重
- 同一 chunk 同时被两路命中时合并
- 保留 `score_breakdown`
- 先按简单融合分排序

这一步做完应达到：

- 同一 chunk 不会重复展示
- 能清楚看到某条结果是靠哪一路命中的
- baseline 能开始对比“向量单路”和“混合第一版”

### Step B4：重新跑 baseline，对比结果

这一步是 `Milestone B` 第一轮最重要的验收动作。

建议直接复用现有：

- `app/scripts/run_retrieval_baseline.py`
- `docs/retrieval_eval_set_step_a.json`

这一步做完应补充记录：

- `top1 document match`
- `top1 section match`
- `top3 section match`
- `HR-001` 和 `HR-002` 是否改善

只要这一步能证明：

- 条款类问题的 `top1` 更稳了
- 至少没有把现有 baseline 明显做坏

那 `Milestone B` 第一轮就算落地成功。

### Step B5：只有在效果还不够时，再考虑 rerank

如果 `Step B4` 后发现：

- 召回已经够了
- 但排序还是经常第一名不准

那再进入 rerank。

也就是说，`rerank` 不是明天必须开做的内容，而是：

**只有在双路召回 + 简单融合之后仍然不够，再作为下一小步。**

## 4. 明天真正的落地范围

明天最合理的完成范围不是“做完整个 Milestone B”，而是：

1. 做完 `Step B1`
2. 做完 `Step B2`
3. 尽量完成 `Step B3`
4. 至少跑通一次 `Step B4`

如果这个范围顺利完成，那么我们就能得到一个非常清晰的结果：

- 仓库里已经有第一版混合召回
- baseline 已经能对比优化前后效果
- 是否需要 rerank，不再靠感觉判断

## 5. 明天要看的文件入口

如果明天开始时只想快速进入状态，建议按这个顺序看：

1. `docs/retrieval_baseline_step_a.md`
2. `docs/retrieval_eval_set_step_a.json`
3. `app/scripts/run_retrieval_baseline.py`
4. `app/services/retrieval_pipeline.py`
5. `app/services/retrieval_service.py`
6. `app/repositories/policy_repository.py`

这样看完后，会很清楚：

- 当前 baseline 是怎么跑的
- 当前评测问题是什么
- 关键词召回应该从哪里接进去

## 6. 每个小步骤的验收标准

### Step B1 验收

- 能返回关键词召回结果
- debug 里能看到关键词召回阶段
- 单元测试至少补到新召回路径

### Step B2 验收

- `search` / `ask` 都能走双路召回
- 接口结构不乱
- 前端调试台不报错

### Step B3 验收

- 命中结果完成去重
- 能看到融合后的来源与分数拆解
- 返回顺序稳定

### Step B4 验收

- baseline 能重新跑通
- 至少记录一版优化后结果
- `HR-001`、`HR-002` 这两个问题要重点人工复核

## 7. 当前不做的内容

以下内容先明确不放进明天的最小落地范围：

- HNSW
- 大规模评测体系重构
- 复杂 rerank 策略
- LangChain / LangGraph 接入
- 多业务数据联动

这样做的原因很简单：

**先把“混合召回第一版 + baseline 对比”落地，才是当前最值当的一步。**

## 8. 一句话交接

如果明天继续开发时只看一句话，请记住：

**Milestone B 明天先做关键词召回、双路接入、简单融合和 baseline 对比，不要一上来就做 rerank 和 HNSW。**
