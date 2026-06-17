from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Bid Document Agent"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    policy_pipeline_workspace: str = ".runtime/policy_pipeline"

    postgres_db: str = "bid_document_agent"
    postgres_user: str = "admin"
    postgres_password: str = "123456"
    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5432

    openai_model: str = "gpt-4.1-mini"
    embedding_model: str = "text-embedding-3-small"
    vector_dimensions: int = 1536

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
