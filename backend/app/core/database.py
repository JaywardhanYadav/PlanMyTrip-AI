import asyncio
import sys
from collections.abc import AsyncGenerator
from typing import Any
from psycopg import AsyncConnection
from psycopg.rows import DictRow, dict_row
from psycopg_pool import AsyncConnectionPool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from .config import get_settings

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def get_sqlalchemy_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(
        settings.DATABASE_URL.get_secret_value(),
        pool_size=settings.DATABASE_POOL_MIN,
        max_overflow=max(0, settings.DATABASE_POOL_MAX - settings.DATABASE_POOL_MIN),
        pool_pre_ping=True,
        echo=False,
    )


engine: AsyncEngine = get_sqlalchemy_engine()

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_checkpointer_conn_string() -> str:
    raw_url = str(get_settings().DATABASE_URL.get_secret_value())
    return str(raw_url.replace("postgresql+asyncpg://", "postgresql://"))


def create_checkpointer_pool() -> AsyncConnectionPool[AsyncConnection[dict[str, Any]]]:
    settings = get_settings()
    return AsyncConnectionPool(
        conninfo=get_checkpointer_conn_string(),
        min_size=settings.DATABASE_POOL_MIN,
        max_size=settings.DATABASE_POOL_MAX,
        open=False,
        kwargs={"autocommit": True, "row_factory": dict_row},
    )


async def setup_checkpointer(
    pool: AsyncConnectionPool[AsyncConnection[dict[str, Any]]]
) -> AsyncPostgresSaver:
    saver = AsyncPostgresSaver(pool)
    await saver.setup()
    return saver
