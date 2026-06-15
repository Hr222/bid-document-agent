# 制度知识库表设计说明

当前第一期只针对 `管理制度` 设计，核心目标是：

- 支持同一制度收录多个年份版本
- 支持追踪制度迭代次数和迭代时间
- 支持记录当前生效版本
- 支持审核留痕
- 支持后续 RAG 检索

## 核心设计思路

制度类资料拆成两层：

- `kb_policy_document`
  - 表示“制度本体”
  - 例如：资产评估报告审核制度、信息安全及保密制度

- `kb_policy_version`
  - 表示“某项制度的一个具体版本”
  - 例如：2005版、2020版、2023版、2025版

这样设计后，一项制度的多个年份版本就可以挂在同一个 `policy_id` 下面。

## 版本迭代相关字段

`kb_policy_version` 中用于表达制度迭代的关键字段：

- `version_seq`
  - 版本顺序号，用于统计收录了多少代

- `version_label`
  - 版本显示名，例如 `2005版`、`2023-09-15版`

- `source_year`
  - 来源年份，便于按年度筛选

- `supersedes_version_id`
  - 当前版本替代了哪个旧版本

- `source_document_date`
  - 原制度文件上的日期

- `issued_at`
  - 制度签发/发布日期

- `effective_date`
  - 制度生效日期

- `expired_at`
  - 制度失效日期

- `ingested_at`
  - 系统入库时间

- `reviewed_at`
  - 审核完成时间

- `approved_at`
  - 知识库正式通过时间

- `version_status`
  - `draft / reviewing / approved / active / superseded / retired`

## 审核与检索

- `kb_policy_section`
  - 按章/条拆分制度正文，便于逐段审核

- `kb_policy_review_record`
  - 记录审核动作和意见

- `kb_policy_chunk`
  - 用于后续向量检索和 RAG

- `kb_policy_version_change`
  - 用于记录两个版本之间的差异摘要

## 推荐查询场景

这套表设计可以支持下面这些场景：

- 查询某项制度当前生效版本
- 查询某项制度一共迭代了多少次
- 查询某个年份有哪些制度版本
- 查询 2025 版相较 2023 版改了什么
- 查询制度某一条款原文
- 查询审核状态为待审核的制度版本
