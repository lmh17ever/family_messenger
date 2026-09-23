from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
)
from app.core.config import settings


engine = create_async_engine(settings.DATABASE_URL, echo=settings.ECHO_SQL)
AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    bind=engine,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_`%(constraint_name)s`",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )

