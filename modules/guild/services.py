from typing import Optional, Literal

import discord
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.results import UpdateResult

from core.database import Database
from core.models.guild_models import GuildSettings
from modules.error.custom_errors import GenericError


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
    async def update_guild_settings(cls, guild_id: int, **fields) -> Optional[UpdateResult]:
        """Update one or more fields on the guild's settings collection"""
        update = await cls.get_guild_collection().update_one(
            {"guild_id": guild_id},
            {"$set": fields},
            upsert=True,
        )
        return update

    @classmethod
    async def create_role(cls, guild: discord.Guild, role_name: str, permission: discord.Permissions) -> discord.Role:
        try:
            existing_role = discord.utils.get(guild.roles, name=role_name)
            if existing_role:
                return existing_role
            role = await guild.create_role(name=role_name, permissions=permission)
            return role
        except discord.Forbidden:
            logger.error(f"Failed to create role {role_name}")
            raise GenericError(f"I do not have permission to create role {role_name}")

    @classmethod
    async def create_channel(
            cls,
            guild: discord.Guild,
            channel_name: str,
            channel_type: Literal["text", "voice", "category", "forum", "stage"] = "text",
            overwrites: dict[discord.Role | discord.Member, discord.PermissionOverwrite] = {},
            category: discord.CategoryChannel = None,
            topic: str = None,
            reason: str = None,
    ) -> Optional[discord.abc.GuildChannel]:
        """
        Generic channel creation for all channel types
        """
        try:
            # Check if channel already exists
            existing_channel = discord.utils.get(guild.channels, name=channel_name)
            if existing_channel:
                return existing_channel

            kwargs = {
                "name": channel_name,
                "overwrites": overwrites,
                "category": category,
                "reason": reason,
            }

            match channel_type:
                case "text":
                    if topic:
                        kwargs["topic"] = topic
                    channel = await guild.create_text_channel(**kwargs)

                case "voice":
                    channel = await guild.create_voice_channel(**kwargs)

                case "category":
                    channel = await guild.create_category(**kwargs)

                case "forum":
                    channel = await guild.create_forum(**kwargs)

                case "stage":
                    channel = await guild.create_stage_channel(**kwargs)

                case _:
                    raise ValueError(f"Invalid channel type: {channel_type}")

            return channel

        except discord.Forbidden:
            logger.error(f"Missing permissions to create channel {channel_name}")
            raise
        except discord.HTTPException as e:
            logger.error(f"Failed to create channel {channel_name}: {e}")
            raise
