from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.session import SessionLocal


def get_db_session() -> Generator[Session, None, None]:
    """为每个请求提供一个数据库会话，并在结束后关闭。"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
