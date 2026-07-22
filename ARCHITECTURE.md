# 当前架构基准

## 最终结构图

```mermaid
flowchart LR
    subgraph Interfaces["Interfaces 外部接口层"]
        direction TB
        Http["HTTP API"]
        HttpAdapter["HTTP Assemblers"]
        Agent["LangChain / LangGraph"]
        ToolAdapter["Function Calling Adapter"]

        Http --> HttpAdapter
        Agent --> ToolAdapter
    end

    subgraph Applications["Applications 应用模块层"]
        direction TB
        Online["Online Application<br/>RAG Facade / Decision"]
        Ingestion["Ingestion Application<br/>文档入库用例"]

        HttpAdapter --> Online
        HttpAdapter --> Ingestion
        ToolAdapter --> Online
    end

    subgraph Knowledge["Knowledge 知识能力层"]
        direction TB
        Query["Query Capability<br/>查询 / 检索 / 引用"]
        Write["Write Capability<br/>知识写入"]
        Publish["Publication Service<br/>版本发布 / 激活"]

        Online --> Query
        Ingestion --> Write
        Ingestion --> Publish
    end

    subgraph Persistence["Persistence 持久化与基础设施层"]
        direction TB
        Ports["Ports<br/>Read / Write / Publication"]
        Repositories["Repository Layer<br/>Read / Write / Publication Repository"]
        Providers["Technical Adapters<br/>LLM / Embedding / OCR / File System"]
        Storage[("PostgreSQL / pgvector<br/>Published Read Model / Vector Index")]

        Query --> Ports
        Write --> Ports
        Publish --> Ports
        Ports -.实现.-> Repositories
        Repositories --> Storage
    end

    Composition["Composition Root<br/>ApplicationContainer"]

    Composition -.->|组装| Online
    Composition -.->|组装| Ingestion
    Composition -.->|组装| Query
    Composition -.->|组装| Repositories
    Composition -.->|组装| Providers

    classDef interface fill:#e8f1ff,stroke:#3478c9,color:#123b63;
    classDef application fill:#eaf7ee,stroke:#3c9b5f,color:#1d5c32;
    classDef knowledge fill:#fff7e6,stroke:#d99a18,color:#714e00;
    classDef infrastructure fill:#f4f0ff,stroke:#7956b3,color:#432d6e;
    classDef composition fill:#f5f5f5,stroke:#666,color:#333;

    class Http,HttpAdapter,Agent,ToolAdapter interface;
    class Online,Ingestion application;
    class Query,Write,Publish knowledge;
    class Ports,Repositories,Providers,Storage infrastructure;
    class Composition composition;
```

## 当前物理目录结构

```text
app/
├── modules/                              # 三大业务模块总包
│   ├── online/                           # 在线 RAG / Decision
│   │   ├── application/
│   │   │   ├── rag_facade.py
│   │   │   ├── ask_knowledge.py
│   │   │   └── policy_decision.py
│   │   ├── domain/
│   │   │   ├── checklist/
│   │   │   │   ├── definitions.py
│   │   │   │   └── registry.py
│   │   │   └── decision_result.py
│   │   └── contracts.py
│   │
│   ├── knowledge/                        # 知识能力层
│   │   ├── application/
│   │   │   ├── query_capability.py
│   │   │   ├── publication_service.py
│   │   │   └── write_capability.py
│   │   ├── domain/
│   │   │   ├── knowledge_version.py
│   │   │   └── publication_state.py
│   │   ├── ports/                         # 仓储抽象与能力端口
│   │   │   ├── read_port.py
│   │   │   ├── write_port.py
│   │   │   └── publication_port.py
│   │   └── retrieval/
│   │       ├── pipeline.py
│   │       ├── policies.py
│   │       ├── rerank.py
│   │       └── vector_search.py
│   │
│   └── ingestion/                        # 独立文档入库层
│       ├── application/
│       │   ├── ingestion_use_case.py
│       │   └── scan_candidates.py
│       ├── domain/
│       │   └── policies.py
│       ├── ports/
│       │   ├── file_port.py
│       │   ├── embedding_port.py
│       │   └── ocr_port.py
│       └── pipeline/
│           ├── pipeline.py
│           ├── context.py
│           ├── persistence.py
│           └── steps/
│
├── interfaces/                           # 外部接口层
│   ├── http/                             # 给前端的 HTTP API
│   │   ├── routes/
│   │   ├── assemblers/
│   │   └── schemas/
│   └── agent/                            # LangChain / LangGraph
│       ├── function_calling_adapter.py
│       └── contracts.py
│
├── infrastructure/                       # 基础设施具体实现
│   ├── persistence/
│   │   ├── repositories/                  # 仓储层具体实现
│   │   │   ├── knowledge_read_repository.py
│   │   │   ├── knowledge_write_repository.py
│   │   │   └── knowledge_publication_repository.py
│   │   ├── models/                        # ORM 持久化模型
│   │   └── session.py
│   ├── llm/
│   │   ├── llm_client.py
│   │   └── embedding_client.py
│   ├── ocr/
│   │   └── tencent_ocr.py
│   └── filesystem/
│       ├── policy_file_service.py
│       └── upload_service.py
│
├── composition/                          # Composition Root
│   ├── root.py
│   ├── online.py
│   ├── knowledge.py
│   └── ingestion.py
│
└── shared/                               # 少量公共基础类型
    ├── exceptions.py
    ├── identifiers.py
    └── events.py
```

## 关键边界图

```mermaid
flowchart TB
    HTTP["interfaces/http"]
    Agent["interfaces/agent"]
    Online["modules/online"]
    Ingestion["modules/ingestion"]
    KnowledgeQuery["modules/knowledge<br/>Query Capability"]
    KnowledgeWrite["modules/knowledge<br/>Write / Publication Capability"]
    Ports["modules/knowledge/ports"]
    Repositories["infrastructure/persistence/repositories"]
    Providers["infrastructure/llm / ocr / filesystem"]
    Storage[("PostgreSQL / pgvector / Object Storage")]

    HTTP --> Online
    HTTP --> Ingestion
    Agent --> Online

    Online --> KnowledgeQuery
    Ingestion --> KnowledgeWrite
    KnowledgeQuery --> Ports
    KnowledgeWrite --> Ports
    Ports -.实现.-> Repositories
    Repositories --> Storage
    Online -.依赖.-> Providers
    Ingestion -.依赖.-> Providers

    Forbidden["禁止：Online 直接依赖 Ingestion<br/>禁止：Ingestion 直接依赖 Online<br/>禁止：Domain 依赖 HTTP / DB / LangChain"]

    classDef forbidden fill:#fff1f0,stroke:#cf1322,color:#820014;
    class Forbidden forbidden;
```

## 核心调用关系图

```mermaid
flowchart LR
    subgraph External["外部调用"]
        HTTP["HTTP API"]
        Agent["LangChain / LangGraph"]
        Source["文档 / PDF / 图片"]
    end

    subgraph Online["在线应用层：RAG / Decision"]
        HttpAdapter["HTTP Assembler"]
        ToolAdapter["Function Calling Adapter"]
        Facade["RAG Application Facade"]
        Ask["AskKnowledge"]
        Decision["Policy Decision"]
    end

    subgraph Knowledge["知识能力层"]
        Query["KnowledgeBaseQueryCapability"]
        Read["KnowledgeBaseReadPort"]
        ReadRepo["KnowledgeReadRepository"]
        Write["KnowledgeBaseWritePort"]
        WriteRepo["KnowledgeWriteRepository"]
        Publish["KnowledgePublicationService"]
        PublishRepo["KnowledgePublicationRepository"]
        Store[("Knowledge Base<br/>Published Read Model / Vector Index")]
    end

    subgraph Ingestion["独立入库应用层"]
        IngestAdapter["Ingestion Adapter"]
        Ingest["Ingestion Use Case"]
        Pipeline["解析 / OCR / 清洗<br/>分节 / 切块 / 向量化"]
    end

    PublicationHttp["HTTP Publication Route"]

    HTTP --> HttpAdapter
    HTTP --> PublicationHttp
    Agent --> ToolAdapter

    HttpAdapter --> Facade
    ToolAdapter --> Facade
    Facade --> Ask
    Facade --> Decision

    Ask --> Query
    Decision --> Query
    Query --> Read
    Read --> ReadRepo
    ReadRepo --> Store

    Source --> IngestAdapter
    IngestAdapter --> Ingest
    Ingest --> Pipeline
    Pipeline --> Write
    Write --> WriteRepo
    PublicationHttp --> Publish
    Publish --> PublishRepo
    PublishRepo --> Store
```

## Checklist 与 RAG 的架构对应

Checklist 场景属于 `modules/online/domain/checklist`，负责场景定义、规则要求和输入材料核验；它不直接实现 RAG，也不直接访问数据库或具体 Repository。

Checklist 通过 `modules/online/application/rule_retrieval` 调用 Knowledge Query Capability，使用 `modules/knowledge/retrieval` 提供的召回、融合、rerank 和来源追踪能力，得到规则证据包后再进行领域判断。

具体场景的新增方式和各层职责见 `docs/Checklist场景与RAG检索扩展说明.md`。
