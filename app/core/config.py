from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置：优先从环境变量和 `.env` 中加载。"""

    app_name: str = "Bid Document Agent"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    policy_pipeline_workspace: str = ".runtime/policy_pipeline"

    postgres_driver: str = "postgresql+psycopg"
    postgres_db: str = "bid_document_agent"
    postgres_user: str = "admin"
    postgres_password: str = "123456"
    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5432
    database_url_override: str | None = Field(default=None, alias="DATABASE_URL")

    gitee_api_key: str | None = Field(default=None, alias="GITEE_API_KEY")
    gitee_base_url: str = "https://ai.gitee.com/v1"
    embedding_model: str = "Qwen3-Embedding-0.6B"
    vector_dimensions: int = 1024
    chunk_target_chars: int = 1200
    chunk_overlap_chars: int = 120
    embedding_batch_size: int = 16
    zhipu_api_key: str | None = Field(default=None, alias="ZHIPU_API_KEY")
    zhipu_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    zhipu_chat_model: str | None = "glm-4-flash"
    ocr_model: str = "glm-4.6v-flash"
    ocr_max_pages_per_batch: int = 4
    ocr_image_max_side: int = 1800
    ocr_timeout_seconds: int = 60
    ocr_request_interval_seconds: float = 10.0
    retrieval_top_k_default: int = 5
    retrieval_top_k_max: int = 20
    rag_answer_top_k: int = 6
    rag_max_context_chars_per_chunk: int = 500
    ocr_enabled: bool = True
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    @property
    def database_url(self) -> str:
        """优先返回 `DATABASE_URL`，否则根据分项配置动态拼接连接串。"""
        if self.database_url_override:
            return self.database_url_override

        return (
            f"{self.postgres_driver}://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
