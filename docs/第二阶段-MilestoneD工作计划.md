# 第二阶段 Milestone D 工作计划

本文档用于记录当前 `Agent Phase 2 / Milestone D` 的目标、拆解步骤、验收标准与当前代码现实，方便后续继续开发时直接接上，不需要重新回忆上下文。

## 0. 阶段边界与第二阶段终点（调整后）

当前项目的阶段划分应按实际建设内容理解，而不是按是否已经接入 Agent 框架理解。

### 第一阶段：资料知识底座建设

第一阶段主要解决“资料能不能进入系统并成为可检索知识”的问题，包含：

- 文件接入与资料准入校验
- DOC / DOCX / PDF / 图片解析
- OCR 识别与 OCR 结果回填
- 文本清洗、章节拆分和 Chunk 切分
- Embedding 生成与 PostgreSQL / pgvector 持久化
- 最小检索与 RAG 问答验证

因此，第一阶段的核心是：

**资料清洗、解析、入库和 OCR 识别，并用最小检索闭环验证知识底座可用。**

### 第二阶段：检索基础设施与规则/数据能力建设

第二阶段主要解决“知识底座能不能稳定支撑后续应用”的问题，当前拆分为：

- `Milestone A`：检索底座抽象、评测和调试能力
- `Milestone B`：混合检索、融合和 rerank
- `Milestone C`：HNSW 索引和向量检索性能准备
- `Milestone D`：规则获取、数据获取和结果生成 PoC
- `Milestone E`：知识库收尾，保证现有资料干净、可查、可追溯

**Milestone E 是 Agent Phase 2 的最后一个工作阶段。**

第二阶段结束后，才进入后续应用端阶段。后续应用端负责理解具体银行要求、组织填写任务、进行人工确认和形成最终标书内容；这些内容不提前倒灌到当前知识库底座中。

## 1. 先记住当前结论

在 `Milestone C` 已完成的前提下，当前执行阶段进入 `Milestone D`。

判断与执行的直接依据是：

- `docs/当前阶段与下一阶段计划.md`
- 当前仓库中的实际代码状态

`Milestone D` 的重点不再是继续打磨单点检索性能，而是：

**把已经稳定下来的检索底座，往“规则获取 + 数据获取 + 结果生成”的最小业务闭环推进一小步。**

在 D5 完成机测和人测确认后，Milestone D 收口并进入 `Milestone E`。D5 之后不再继续扩展模板化、完整标书生成或复杂业务 Agent 能力。

## 2. Milestone D 要解决什么

`Milestone D` 在本项目中的定位，不是一下子做成完整业务 Agent，而是先解决三个更贴近真实业务的问题：

1. 当用户提出一个业务判断问题时，系统能不能先拿到足够可引用的规则依据
2. 在已有规则依据后，系统能不能明确知道还需要哪些业务字段，并从一个最小数据入口拿到这些字段
3. 在规则与数据都具备后，系统能不能产出一个可解释、可回溯的判断结果或辅助结论

因此，`Milestone D` 的关键词不是单独的 “生成”，而是：

- 单一业务场景闭环
- 规则依据可引用
- 业务数据可获取
- 结果输出可解释
- 后续 Agent 编排可抽象

## 3. 当前代码现实

当前代码已经具备进入 `Milestone D` 的基础，并且已经完成首个最小业务 PoC；规则获取层、数据获取层与结果生成链路均已完成首版通用化，但真实外部数据源、复杂规则类型与更完整的回归资产仍属于后续收口工作。

### 3.1 已有基础

- 当前已有稳定的检索主链路：
  - 向量召回
  - 关键词召回
  - 融合
  - rerank
- 当前已有统一检索接口：
  - `POST /api/v1/kb/retrieval/search`
  - `POST /api/v1/kb/retrieval/ask`
- 当前已新增一条独立的 D1 PoC 路由：
  - `POST /api/v1/kb/policy-decisions/court-evaluation-materials/review`
- 当前 `ask` 已能基于命中结果生成最小可引用回答
- 当前领域层已经按职责拆分规则代码入口，例如：
  - `app/modules/ingestion/domain/policies.py`
  - `app/modules/knowledge/retrieval/policies.py`
- 当前已经有一版最小规则驱动清单校验能力：
  - `app/modules/online/domain/checklist/definitions.py`
- 当前已经有一版 PoC 级 decision service / schema：
  - `app/modules/online/application/decision/service.py`
  - `app/interfaces/http/schemas/policy_decision.py`
- 当前检索链路已能输出较完整的 debug / trace 信息，具备继续做规则/数据链路可解释性的基础

### 3.2 当前剩余的工程问题

- 当前 D1 已经跑通单场景 PoC，且 D2 已补出首版 `RulePack` 与规则获取服务，但还只完成了第一类规则场景验证
- 当前 D3 已补出首版 `DataPack`、数据获取 service 与来源 trace，但仍只完成 inline provider 落地
- 当前结构化结果已经有首版 schema，但还只覆盖一个审核场景，尚未形成更通用的 decision contract
- 当前 PoC 还集中在“申请材料核验”这一个场景，后续还要验证第二类规则问题能否沿用同一套路
- 当前 D5 已补齐固定 PoC 样例、应用层回归测试和 HTTP Smoke 测试，全量后端测试为 `74 passed`
- D 阶段仍明确保留 inline provider、单一生产场景和轻量规则表达能力，这些不阻塞 D5 收口
- Milestone E 不再以历史案例库、模板库或标书生成能力为目标

## 4. 当前阶段不做什么

为了避免把 `Milestone D` 做散，以下内容当前明确不放进本轮主任务：

- 现在就做完整多场景业务 Agent
- 现在就引入 `LangChain / LangGraph` 做复杂编排
- 现在就接真实外部业务系统做正式集成
- 现在就做历史案例库与模板库工程化
- 现在就把 OCR、入库增强、检索样本扩充一起并入主线

这些内容都重要，但不属于 `Milestone D` 的主线。

## 5. 建议的推进顺序

`Milestone D` 建议分成五个小步推进，而不是一上来就做“大而全业务 Agent”。

### Step D1：PoC 场景收口与输入输出口径确定

这一小步先做一件事：

- 只选一个最小真实业务场景，明确它的输入、输出、依赖规则和依赖数据

建议优先选用的 PoC 场景：

- **单条制度规则驱动的审核/判断类 PoC**

更具体一点，建议把首个 PoC 收敛成：

- 输入一个业务问题或审核事项
- 从知识库中获取对应制度依据
- 判断需要哪些业务字段
- 从最小数据源中拿到这些字段
- 输出“是否满足 / 为什么 / 缺什么”的结构化结果

建议这一小步做完后，至少明确：

- PoC 的目标问题是什么
- 用户侧最小输入有哪些
- 系统侧最小数据字段有哪些
- 最终输出的结构化结果长什么样

做到后应满足：

- 后续开发不再围绕“到底做哪个业务场景”反复摇摆

当前状态：

- **已进入 D1，并已完成首个场景收口与最小落地**
- 当前选定场景为：`委托评估机构申请材料核验`
- 当前最小输入为：`submitted_materials`
- 当前规则查询为：`申请参与委托评估的机构应提交哪些资料`
- 当前结构化输出已包含：
  - `decision`
  - `reasoning`
  - `citations`
  - `used_fields`
  - `missing_fields`
  - `requirement_statuses`
  - `debug`
- 当前已补对应测试与真实 public 数据 smoke，说明 D1 已不再停留在设计阶段

### Step D2：规则获取抽象

这一小步的目标不是重写现有 retrieval pipeline，而是把“检索命中结果”整理成更适合业务判断复用的规则结果。

建议补齐：

- 一个面向业务链路的规则获取 service
- 基于检索命中的规则依据对象
- 规则依据中的引用、来源、命中片段透传
- 对“证据不足”的统一判断出口

建议规则获取结果至少包含：

- 原始问题
- 命中的规则片段
- 对应引用信息
- 规则摘要或规则判断关注点
- 是否足以支撑后续判断

这一小步做完后应达到：

- 系统不再只是“搜到一些 chunk”
- 而是能输出“这次业务判断当前依据的规则包是什么”

当前状态：

- **已完成首版落地**
- 已新增 `ScenarioRegistry`
- 已新增统一 `RulePack`
- 已新增 `PolicyRuleRetrievalService`
- 已将 `court-evaluation-materials-review` 场景迁移到“规则获取层 -> 决策层”的新链路
- 已补齐对应单测与回归验证

### Step D3：数据获取抽象

这一小步的重点是先搭出最小可替换结构，而不是现在就接真实业务系统。

建议第一版先采用：

- 手工输入补充字段
- 本地 mock 数据
- 配置化静态样例

建议补齐：

- 一个最小 `data provider` 接口或抽象层
- 一版 PoC 场景专用的数据请求结构
- 缺失字段识别与提示
- 数据来源 trace，便于后续替换真实来源

这一小步做完后应达到：

- 规则链路可以明确告诉后续步骤“还缺哪些字段”
- 数据获取逻辑不直接散落在 API、prompt 或 service 编排代码里

当前状态：

- **已完成首版落地**
- 已新增 `PolicyDataAcquisitionService`
- 已新增统一 `ChecklistDataAcquisitionRequest`
- 已新增统一 `ChecklistDataPack`
- 已补齐输入字段缺失提示与来源 trace
- 已将 `court-evaluation-materials-review` 场景迁移到“规则层 -> 数据层 -> 决策层”的新链路
- 已补齐对应单测与全量回归验证

### Step D4：结果生成链路

这一小步才把规则和数据真正串起来，形成最小业务输出。

建议补齐：

- 一个 `rule + data -> result` 的编排 service
- 一版结构化结果 schema
- 结果中的结论、理由、证据引用、缺失项说明
- 必要时保留自然语言结论，但结构化字段必须优先

建议首版结果至少包含：

- `decision`：结论或判断状态
- `reasoning`：结论依据
- `citations`：命中的规则引用
- `used_fields`：实际使用到的数据字段
- `missing_fields`：仍然缺失的数据字段
- `debug`：规则获取与数据获取过程摘要

这一小步做完后应达到：

- 系统可以演示一条完整的“规则 -> 数据 -> 结论”最小闭环
- 输出不只是模型自由回答，而是更接近业务系统可消费的结果结构

当前状态：

- **已完成通用化首版落地**
- `DecisionReviewCommand` 支持通过 `scenario_code` 选择已注册场景，未指定时保持默认场景兼容行为
- 决策编排、结果 builder、数据 provider 注册均不再固定依赖法院评估场景
- 已新增通用 HTTP 入口：`POST /api/v1/kb/policy-decisions/{scenario_code}/review`
- 已提供通用 `PolicyDecisionRequest` / `PolicyDecisionResponse` 与 `DecisionResultBuilder`，旧 checklist 名称保留为兼容别名
- 已用第二个独立场景验证同一条“规则 -> 数据 -> 结果”链路可以复用，新增场景不需要修改决策编排代码
- 当前仍保留 checklist 形态的 `submitted_materials` 最小输入，以及 inline provider；真实数据源接入和复杂规则表达能力不属于本轮 D4 通用化首版

### Step D5：PoC 验收与回归资产沉淀

这一小步是 `Milestone D` 真正的验收动作。

建议至少补齐：

- 一组固定 PoC 输入样例
- 对应预期结论或预期判断方向
- “证据不足 / 字段缺失 / 可以判断”三类典型 case
- 一份可重复执行的最小验证脚本或测试

建议优先沉淀：

- 规则获取样例
- 数据字段样例
- 结果结构样例

当前状态：

- **代码与自动化测试已完成，等待项目负责人机测和人测确认**
- 已覆盖规则不足、输入不足、判断通过、判断失败，以及第二场景复用等回归 case
- 已补齐固定 PoC 样例文件、fixture 驱动应用层回归测试和 HTTP API Smoke 测试
- 已完成数据库可用条件下的全量回归：`python -m pytest -q`，共 `74 passed`
- 代码检查与编译检查已通过：`ruff check app tests`、`python -m compileall -q app tests`
- 等待项目负责人完成机测和人测，通过后 D5 即视为验收完成

D5 完成门槛调整为：

- 固定 PoC 样例和自动化回归测试已补齐
- 全量 `pytest` 通过
- 机测和人测由项目负责人执行并确认，通过后视为 D5 验收完成
- 不再要求单独新增阶段验收记录文档

如果条件允许，后续可以继续增加：

- 更多制度类型的业务问题
- 更复杂的数据字段组合
- 更明确的结果正确性断言

## 6. Milestone D 的验收标准

当前建议把验收标准定得清楚一点，避免最后只落成“检索结果后面多接了一次模型调用”。

### 6.1 工程结构验收

- 代码层面已经能区分规则获取、数据获取、结果生成三个职责
- 现有检索主链路没有被破坏，`search / ask` 仍可正常使用
- D 阶段新增能力尽量通过独立 service / schema 接入，而不是直接堆在现有 retrieval route 里

### 6.2 场景闭环验收

- 至少有一个最小真实业务场景跑通
- 该场景下系统能明确说明需要哪些规则、哪些字段、最终给出什么结果
- 在字段不足时，系统能返回“缺什么”，而不是直接编造结论

### 6.3 可解释性验收

- 输出结果能回溯到具体制度依据
- 输出结果能说明实际使用了哪些业务字段
- 对“无法判断”或“证据不足”的场景有统一且可观察的返回方式

### 6.4 可扩展性验收

- 数据来源至少具备从 mock 切换到真实来源的结构准备
- 规则获取结果可以被后续 chain / tool / agent 复用
- 结果 schema 不只适用于自然语言展示，也适合后续 API / 前端消费

## 7. 当前建议优先看的文件入口

如果现在继续往下推进，建议按这个顺序阅读：

1. `docs/当前阶段与下一阶段计划.md`
2. `app/modules/knowledge/retrieval/pipeline.py`
3. `app/modules/knowledge/retrieval/service.py`
4. `app/infrastructure/llm/llm_client.py`
5. `app/modules/knowledge/retrieval/policies.py`
6. `app/modules/online/domain/checklist/definitions.py`
7. `app/modules/online/application/decision/service.py`
8. `app/interfaces/http/routes/retrieval.py`
9. `app/interfaces/http/routes/policy_decision.py`

这样看完之后，会很清楚：

- 当前 D 阶段为什么要做
- 当前规则获取最接近从哪里切入
- 数据获取为什么要先抽象而不是直接硬编码
- 结果生成为什么需要从问答式输出走向结构化输出

## 8. Milestone E：知识库收尾（Phase 2 最后一步）

Milestone E 不再做历史案例库、模板库、银行格式统一或完整标书生成。当前手头资料和业务认知不足以支撑这些抽象，相关内容留到后续应用端，由具体业务场景和人工确认补足。

Milestone E 的唯一定位是：

**保证现有资料干净、可查、可追溯，能够作为应用端后续使用的可靠知识底座。**

### E1：资料清单与状态盘点

- 盘点资料主档、版本、章节、文档块和检索切块
- 统计资料类别、解析状态、版本状态和当前可用范围
- 明确 `draft / approved / active` 的技术状态含义
- 不替业务人员判断资料是否适合某家银行或某个标书

### E2：资料质量清理

- 检查空文本、空切块、异常切块和解析失败资料
- 识别重复文件、重复版本和疑似重复资料
- 检查章节、页码、来源文件和版本信息是否完整
- 对 OCR 资料保留来源和识别状态，不在没有业务确认时擅自改写原文

### E3：检索与追溯可靠性

- 现有资料能够按类别、版本、章节和关键词检索
- 检索结果能够回到原始文档、具体版本、章节、页码和原文片段
- 对无足够证据的查询保持明确的“资料不足”结果
- 为资料清理和检索行为补充必要的 `pytest` 回归测试

### E4：第二阶段收尾边界

Milestone E 完成后，Agent Phase 2 结束。第二阶段最终沉淀的是：

```text
资料知识底座
  -> 混合检索与 rerank
  -> HNSW 性能准备
  -> 规则 / 数据 / 结果 PoC
  -> 干净、可查、可追溯的知识库
```

后续应用端再负责：

- 理解具体银行要求
- 组织标书填写任务
- 让人工确认资料是否适用
- 生成或修改最终标书内容

这些不属于 Milestone E 的数据库和知识底座职责。

## 9. 当前一句话交接

如果继续开发时只看一句话，请记住：

**Milestone D 在 D5 机测和人测通过后收口，Milestone E 作为 Phase 2 最后一步，只负责把现有资料收尾为干净、可查、可追溯的可靠知识底座。**
