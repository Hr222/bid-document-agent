# OCR 与样本分类脚本

当前目录用于放最小可跑通的 OCR 验证脚本，以及进入 `Milestone D` 前的样本资料分类脚本。

## 当前脚本

- [tencent_ocr_mvp.py](/D:/workspace/bid-document-agent/tests/ocr/tencent_ocr_mvp.py)
- [classify_sample_inventory.py](/D:/workspace/bid-document-agent/tests/ocr/classify_sample_inventory.py)

## 1. 腾讯 OCR MVP

支持范围：

- `PDF`：按页循环调用腾讯 OCR 的 `GeneralAccurateOCR`
- `DOCX`：提取嵌入图片后逐张调用腾讯 OCR

说明：

- PDF 走的是腾讯 OCR 官方支持的 `IsPdf=true + PdfPageNumber` 单页识别方式
- DOCX 主要覆盖“扫描件塞进 Word”的场景

环境准备：

1. 安装依赖

```bash
pip install -r requirements-dev.txt
```

2. 在 `.env` 中配置：

```env
TENCENT_OCR_SECRET_ID=你的SecretId
TENCENT_OCR_SECRET_KEY=你的SecretKey
TENCENT_OCR_REGION=ap-guangzhou
```

用法：

识别 PDF：

```bash
python tests/ocr/tencent_ocr_mvp.py "D:\data\sample.pdf" --page-start 1 --page-limit 5
```

识别 DOCX：

```bash
python tests/ocr/tencent_ocr_mvp.py "D:\data\sample.docx" --docx-image-limit 10
```

默认输出到：

```text
tests/ocr/output/<时间戳>_<文件名>/
```

目录中会包含：

- 每页或每张图片对应的原始响应 JSON
- `summary.json` 汇总文件

## 2. 样本资料分类脚本

这个脚本用于 `step2` 的资料盘点与分流，不会修改原始文件，也不会自动转换 DOC。

### 技术分类

- `direct_parse`：可直接进入后续解析
- `convert_doc_to_docx`：老旧 `.doc`，建议借助 WPS 转成 `.docx`
- `ocr`：扫描版 PDF、图片型样本
- `review`：混合型 PDF，建议人工确认
- `exclude`：当前不在首批样本接入范围

### 业务分类

- `rag_text`：适合 OCR/解析后进入 RAG 文本库
- `structured_fields`：更适合做字段抽取，不建议直接作为当前 RAG 主语料
- `review_business`：技术上可处理，但业务去向还需要人工判断
- `exclude_low_value`：低价值图片或附件，不建议入库

### RAG 适配度

- `high`：文字密度高，适合切块后进入 RAG
- `medium`：可以入库，但更依赖后续清洗或混合方案
- `low`：更适合结构化抽取，不建议直接作为 RAG 主语料

### 用法

```bash
python tests/ocr/classify_sample_inventory.py "E:\data" --pdf-sample-pages 3
```

如果只想先看一部分：

```bash
python tests/ocr/classify_sample_inventory.py "E:\data" --limit 200 --preview 20
```

### 输出

```text
tests/ocr/output/inventory/<时间戳>_<目录名>/
```

目录中会包含：

- `summary.json`：完整分类结果与统计
- `items.csv`：便于你直接用 Excel/WPS 打开筛选

`items.csv` 里重点看这些列：

- `pipeline_bucket`：技术处理方式
- `knowledge_route`：业务去向
- `rag_suitability`：RAG 适配度
- `reason`：技术分类原因
- `business_reason`：业务分类原因

### 建议流程

1. 先用 `classify_sample_inventory.py` 盘点目录
2. 优先看 `knowledge_route=rag_text` 的样本
3. 再看 `structured_fields`，决定是否后续做字段抽取
4. 最后把 `ocr` 且 `rag_text` 的样本交给 `tencent_ocr_mvp.py`
