import asyncpg


class UserRepository:
    def __init__(self, connection: asyncpg.Connection) -> None:
        self.connection = connection

    async def create(
        self, first_name: str, last_name: str, is_verified: bool = False, violations_qty: int = 0
    ) -> int:
        return await self.connection.fetchval(
            """
            INSERT INTO users (first_name, last_name, is_verified, violations_qty)
            VALUES ($1, $2, $3, $4) RETURNING id
            """,
            first_name,
            last_name,
            is_verified,
            violations_qty,
        )
