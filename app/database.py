from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
import os
from pathlib import Path

# SQLite database path - use volume on Fly.io, local file for development
# On Fly.io, volumes are mounted at /data
if os.path.exists("/data") or os.getenv("FLY_APP_NAME"):
    # Production: use persistent volume
    DB_PATH = Path("/data/bluehex2.db")
else:
    # Local development: use current directory
    DB_PATH = Path("./bluehex2.db")

# Ensure parent directory exists
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

# Async engine and session factory
engine = create_async_engine(DATABASE_URL, echo=False, future=True)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autoflush=False, autocommit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency: yield an async database session."""
    async with async_session() as session:
        yield session

async def init_db() -> None:
    """Initialize database and create tables if they do not exist."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

