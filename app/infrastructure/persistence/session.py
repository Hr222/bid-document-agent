from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.shared.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args={"connect_timeout": settings.postgres_connect_timeout_seconds},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
