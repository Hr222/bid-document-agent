import uuid
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base


class SchemaHarness:
    def __init__(self, prefix: str) -> None:
        self.schema = f"{prefix}_{uuid.uuid4().hex[:8]}"
        self.admin_engine = create_engine(
            settings.database_url,
            future=True,
            pool_pre_ping=True,
        )
        self.test_engine = create_engine(
            settings.database_url,
            future=True,
            pool_pre_ping=True,
            connect_args={"options": f"-csearch_path={self.schema},public"},
        )
        self.session_local = sessionmaker(
            bind=self.test_engine,
            autoflush=False,
            autocommit=False,
        )

    def create_schema(self) -> None:
        with self.admin_engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{self.schema}"'))

        Base.metadata.create_all(bind=self.test_engine, checkfirst=False)

    def drop_schema(self) -> None:
        self.test_engine.dispose()
        with self.admin_engine.begin() as conn:
            conn.execute(text(f'DROP SCHEMA IF EXISTS "{self.schema}" CASCADE'))
        self.admin_engine.dispose()

    def truncate_tables(self, *tables: str) -> None:
        quoted_tables = ", ".join(f'"{self.schema}".{table}' for table in tables)
        with self.test_engine.begin() as conn:
            conn.execute(text(f"TRUNCATE TABLE {quoted_tables} RESTART IDENTITY CASCADE"))

    def override_get_db_session(self) -> Generator[Session, None, None]:
        session = self.session_local()
        try:
            yield session
        finally:
            session.close()
