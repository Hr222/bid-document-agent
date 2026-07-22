# Checklist 场景与 RAG 检索扩展说明

本文档说明 Checklist 场景在当前架构中的位置，以及它如何使用知识库 RAG 检索能力。新增 Checklist 场景或排查场景问题时，先按本文档确定代码应该属于哪一层。

## 1. 先看架构位置

Checklist 不是独立的基础设施，也不是 RAG Pipeline 本身。它是 Online 应用中的一种领域决策模型。

在 `ARCHITECTURE.md` 的分层中，对应关系如下：

| 当前能力 | 架构层级 | 代码位置 | 主要职责 |
|---|---|---|---|
| HTTP 请求和响应 | Interfaces / HTTP | `app/interfaces/http` | 接收请求、Schema 转换、依赖注入、异常映射 |
| 决策流程编排 | Applications / Online | `app/modules/online/application` | 串联规则获取、数据获取和结果生成 |
| Checklist 场景和领域规则 | Applications / Online / Domain | `app/modules/online/domain/checklist` | 定义场景、清单要求、证据匹配和材料核验 |
| 规则证据获取 | Applications / Online / Rule Retrieval | `app/modules/online/application/rule_retrieval` | 使用知识查询能力，将检索结果整理为 `RulePack` |
| 知识查询能力 | Knowledge / Query Capability | `app/modules/knowledge/application/query_capability.py` | 对 Online 提供稳定的查询和检索入口 |
| RAG 检索流程 | Knowledge / Retrieval | `app/modules/knowledge/retrieval` | 向量召回、关键词召回、融合、rerank、过滤和调试追踪 |
| 知识查询端口 | Knowledge / Ports | `app/modules/knowledge/ports` | 定义应用层访问知识库的能力契约 |
| 数据库、Embedding 等具体实现 | Infrastructure | `app/infrastructure` | Repository、数据库、Embedding 和其他技术适配器 |
| 具体依赖组装 | Composition Root | `app/composition` | 注册场景并组装检索、数据和决策服务 |

## 2. Checklist 如何调用 RAG

调用链路是：

```text
HTTP Route
  -> PolicyDecisionApplicationService
  -> RuleDrivenChecklistDecisionService
  -> PolicyRuleRetrievalService
  -> KnowledgeBaseQueryCapability
  -> Knowledge Read Port / Repository
  -> Knowledge Retrieval Pipeline
  -> RulePack
  -> ChecklistScenarioDefinition + RuleDrivenChecklistPolicy
  -> DecisionResult
  -> HTTP Response
```

Checklist 只消费经过规则获取层整理后的规则证据，不直接调用数据库、向量索引、Embedding 客户端或具体 Repository。

RAG 层负责回答：

- 哪些知识片段与场景问题相关
- 命中片段来自哪个文档、版本、章节和页码
- 召回、融合和 rerank 的过程信息是什么
- 当前是否有足够的规则证据支撑后续判断

Checklist 层负责回答：

- 当前场景要求哪些材料或业务字段
- 规则片段命中了哪些要求
- 用户提交的数据是否覆盖已命中的要求
- 当前结果是通过、失败还是证据不足

## 3. 新增 Checklist 场景

新增一个仍然属于“规则清单核验”的场景时，按以下步骤执行。

### 3.1 新建场景定义

在以下目录新增独立文件：

```text
app/modules/online/domain/checklist/scenarios/
```

场景定义使用通用的 `ChecklistScenarioDefinition`，通常需要提供：

- `scenario_code`：稳定的场景编码
- `scenario_name`：展示名称
- `retrieval_query`：用于获取规则证据的查询问题
- `policy_category`：知识库检索分类，可为空
- `requirements`：当前场景的要求清单
- `min_rule_match_count`：规则证据最低充分性阈值
- `input_field_key` 和 `input_field_label`：业务输入字段定义

每个 `ChecklistRequirementDefinition` 再定义：

- `field_key`
- `label`
- `components`
- `evidence_keywords`
- `required`

具体场景内容应放在场景文件中，不要写回通用的 `definitions.py` 或 `registry.py`。

### 3.2 在 Composition Root 注册

在 `app/composition/root.py` 中将场景定义注册到 `ChecklistScenarioRegistry`：

```python
ChecklistScenarioRegistry(
    definitions=(场景定义一, 场景定义二),
    default_scenario_code="默认场景编码",
)
```

注册表只负责保存和查找场景，不负责导入或创建具体业务场景。

### 3.3 判断是否需要新的 Data Provider

如果新场景仍然使用当前的 inline 材料输入，可以复用现有 Provider。

如果新场景需要表单、数据库或外部业务系统数据，应在 `app/modules/online/application/data_acquisition` 中增加对应 Provider，并在 Composition Root 注册，不能把数据读取逻辑写进 Checklist Domain。

### 3.4 补充测试

至少补充：

- 场景注册和查询测试
- 规则证据充分与不足测试
- 业务输入缺失测试
- 材料完整与不完整测试
- 引用和调试追踪测试
- HTTP 入口测试（如果新增或修改接口契约）

## 4. 哪些情况不能继续扩展 Checklist

以下能力不应为了复用代码而强行套入 `ChecklistScenarioDefinition`：

- 评分或排序模型
- 长文本结构化提取
- 投标书章节生成
- 多轮问答或复杂 Agent 编排
- 不以“规则要求与输入覆盖关系”为核心的业务流程

这类需求应先定义新的领域契约和 Application Service，再决定是否复用 Knowledge Query Capability 或 RAG Pipeline。

## 5. 分层边界

- `domain/checklist` 不得依赖 HTTP、数据库、Repository、Embedding 或 LLM 框架。
- Checklist 场景定义不负责执行 RAG 检索。
- `knowledge/retrieval` 不得写入具体 Checklist 场景规则。
- `application/rule_retrieval` 负责连接 RAG 证据与 Checklist 规则包。
- 具体 Repository、Embedding 和外部服务只在 Infrastructure / Composition Root 出现。
- 新增场景不得修改通用决策流程来添加单场景分支。

## 6. 一句话判断

```text
场景定义属于 Online Domain，
规则获取属于 Online Application，
RAG 检索属于 Knowledge，
具体数据库和模型实现属于 Infrastructure，
所有具体场景和适配器由 Composition Root 组装。
```
