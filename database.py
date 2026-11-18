import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI, Request

DEFAULT_DSN = "postgresql://postgres:postgres@localhost:5435/hw"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with asyncpg.create_pool(
        os.getenv("DATABASE_URL", DEFAULT_DSN), min_size=0, max_size=10, timeout=5
    ) as pool:
        app.state.pool = pool
        yield


async def get_connection(request: Request) -> AsyncIterator[asyncpg.Connection]:
    async with request.app.state.pool.acquire(timeout=5) as connection:
        yield connection
