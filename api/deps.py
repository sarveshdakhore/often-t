"""
Shared FastAPI dependencies:
* get_db_session()  – one AsyncSession per request, with auto-commit / rollback
* PaginationDep     – typed pagination helper
* ETagDep           – placeholder for If-Match / ETag handling
"""
from __future__ import annotations

from typing import AsyncGenerator, Annotated, Optional

from fastapi import Depends, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.database import engine
from schemas.pagination import PaginationParams

# -----------------------------------------------------------
# Session factory (expire_on_commit=False keeps objects alive)
# -----------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield ONE AsyncSession per request, commit on success, rollback on error."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError:
            await session.rollback()
            raise

DbSession = Annotated[AsyncSession, Depends(get_db_session)]

# --------------------
# Pagination helper
# --------------------
def _pagination_params(
    limit: int = Query(10, ge=1, le=100, description="Max rows to return"),
    offset: int = Query(0, ge=0,  description="Rows to skip     "),
) -> PaginationParams:
    return PaginationParams(limit=limit, offset=offset)

PaginationDep = Annotated[PaginationParams, Depends(_pagination_params)]

# -------------
# ETag placeholder
# -------------
async def _check_etag(
    if_match: Optional[str] = Query(None, alias="If-Match"),
) -> Optional[str]:
    return if_match

ETagDep = Annotated[Optional[str], Depends(_check_etag)]
