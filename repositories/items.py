import asyncpg

from models import PredictionRequest


class ItemRepository:
    def __init__(self, connection: asyncpg.Connection) -> None:
        self.connection = connection

    async def create(
        self, seller_id: int, name: str, description: str, category: int, images_qty: int
    ) -> int:
        return await self.connection.fetchval(
            """
            INSERT INTO items (seller_id, name, description, category, images_qty)
            VALUES ($1, $2, $3, $4, $5) RETURNING id
            """,
            seller_id,
            name,
            description,
            category,
            images_qty,
        )

    async def for_prediction(self, item_id: int) -> PredictionRequest | None:
        row = await self.connection.fetchrow(
            """
            SELECT i.id AS item_id, i.seller_id, u.is_verified AS is_verified_seller,
                   i.name, i.description, i.category, i.images_qty
            FROM items AS i JOIN users AS u ON u.id = i.seller_id
            WHERE i.id = $1
            """,
            item_id,
        )
        return PredictionRequest(**row) if row is not None else None
