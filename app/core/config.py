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

    openai_model: str = "gpt-4.1-mini"
    embedding_model: str = "text-embedding-3-small"
    vector_dimensions: int = 1536
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    chunk_target_chars: int = 1200
    chunk_overlap_chars: int = 120
    embedding_batch_size: int = 16

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
