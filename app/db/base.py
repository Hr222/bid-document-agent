from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import ORM models here so SQLAlchemy metadata can discover every table mapping.
from app.models import PolicyDocument, PolicySection, PolicyVersion  # noqa: E402,F401
