from loguru import logger
from motor.motor_asyncio import AsyncIOMotorCollection

from core.database import Database
from core.models.guild_models import GuildSettings


class GuildService:

    @classmethod
    def get_guild_collection(cls) -> AsyncIOMotorCollection:
        return Database.guild_settings()

    @classmethod
    async def get_guild_setting(cls, guild_id: int) -> GuildSettings | None:
        try:
            guild_setting_collection = cls.get_guild_collection()
            settings = await guild_setting_collection.find_one({"guild_id": guild_id})
            if settings:
                return GuildSettings(**settings)
            return None
        except Exception as err:
            logger.error(f"Failed to get guild setting from database: {err}")
            return None

    @classmethod
    async def update_guild_settings(cls, guild_id: int, **fields) -> None:
        """Update one or more fields on the guild's settings collection"""
        await cls.get_guild_collection().update_one(
            {"guild_id": guild_id},
            {"$set": fields},
            upsert=True,
        )
