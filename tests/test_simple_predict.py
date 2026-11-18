import os

import asyncpg
import httpx
import pytest

from database import DEFAULT_DSN, get_connection
from repositories.items import ItemRepository
from repositories.users import UserRepository


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def catalog():
    async with asyncpg.create_pool(
        os.getenv("DATABASE_URL", DEFAULT_DSN), max_size=1, min_size=1
    ) as pool:
        async with pool.acquire() as conn:
            tx = conn.transaction()
            await tx.start()
            try:
                yield conn
            finally:
                await tx.rollback()


@pytest.fixture
async def seller(catalog):
    async def create(verified):
        return await UserRepository(catalog).create("Ирина", "Соколова", verified, 2)

    return create


@pytest.fixture
async def item_id(catalog, seller):
    async def create(verified, images):
        user_id = await seller(verified)
        return await ItemRepository(catalog).create(user_id, "Книга", "Новое издание", 1, images)

    return create


@pytest.fixture
async def api(app, catalog):
    # Запрос и подготовка данных используют одну транзакцию, откатываемую после теста.
    async def test_connection():
        return catalog

    app.dependency_overrides[get_connection] = test_connection
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("verified", "images", "expected"),
    [
        (False, 0, True),
        (False, 1, False),
        (True, 0, False),
        (True, 1, False),
    ],
)
async def test_predict_stored_item(api, item_id, verified, images, expected):
    key = await item_id(verified, images)
    response = await api.post("/simple_predict", params={"item_id": key})
    assert response.status_code == 200
    assert response.json() is expected


@pytest.mark.anyio
async def test_deleted_item_returns_404(api, catalog, item_id):
    key = await item_id(False, 0)
    await catalog.execute("DELETE FROM items WHERE id = $1", key)
    assert (await api.post("/simple_predict", params={"item_id": key})).status_code == 404


@pytest.mark.anyio
async def test_repository_round_trip(catalog, seller):
    user_id = await seller(True)
    row = await catalog.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
    assert (row["first_name"], row["last_name"], row["violations_qty"]) == ("Ирина", "Соколова", 2)
    repo = ItemRepository(catalog)
    key = await repo.create(user_id, "Книга", "Новое издание", 4, 3)
    item = await repo.for_prediction(key)
    assert item.model_dump() == {
        "seller_id": user_id,
        "is_verified_seller": True,
        "item_id": key,
        "name": "Книга",
        "description": "Новое издание",
        "category": 4,
        "images_qty": 3,
    }


@pytest.mark.parametrize("value", [None, "", "zero", "1.5", "0", "-1", str(2**63)])
def test_invalid_item_id(client, value):
    params = {} if value is None else {"item_id": value}
    assert client.post("/simple_predict", params=params).status_code == 400
