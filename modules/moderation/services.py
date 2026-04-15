import asyncio
from typing import List, Optional

from loguru import logger
from motor.motor_asyncio import AsyncIOMotorCollection
import discord
from typing_extensions import Literal

from core.database import Database
from core.models.guild_models import ModerationSettings, Roles
from core.models.user_model import UserModel
from modules.error.custom_errors import GenericError
from modules.guild.services import GuildService
from modules.user.user_service import UserService


class ModerationService:

    @classmethod
    def get_moderation_settings_collection(cls) -> AsyncIOMotorCollection:
        return Database.moderation_settings()

    @classmethod
    async def get_mod_settings(cls, guild_id: str) -> ModerationSettings:
        mod_collection = cls.get_moderation_settings_collection()
        data = await mod_collection.find_one({"guild_id": guild_id})
        if data:
            return ModerationSettings(**data)

        # Create default
        new_settings = ModerationSettings(guild_id=guild_id)
        await mod_collection.insert_one(new_settings.model_dump())
        return new_settings

    @classmethod
    async def send_logs(
            cls,
            guild: discord.Guild,
            action: Literal["Kick","Ban","Mute","UnMute","Timeout","Remove Timeout","Unban","Warn"],
            moderator: discord.Member,
            target: discord.Member,
            reason: str = None,
    ):
        guild_setting = await GuildService.get_guild_setting(guild_id=guild.id)
        if not guild_setting:
            return
        mod_log_channel_id = guild_setting.log_channel.mod_log_channel_id
        if not mod_log_channel_id:
            return

        channel: discord.TextChannel = guild.get_channel(mod_log_channel_id)
        if not channel:
            return

        color_map = {
            "Kick": discord.Color.from_str("#F59E0B"),  # Amber (warning action)
            "Ban": discord.Color.from_str("#DC2626"),  # Strong red (severe punishment)
            "Warn": discord.Color.from_str("#FACC15"),  # Bright yellow (attention)
            "Mute": discord.Color.from_str("#6366F1"),  # Indigo (temporary restriction)
            "Unban": discord.Color.from_str("#22C55E"),  # Green (positive action)
        }

        embed = discord.Embed(
            title=f"🔨{action.capitalize()}",
            color= color_map.get(action, discord.Color.orange()),
            timestamp= discord.utils.utcnow()
        )
        embed.add_field(name="User", value=f"{target.name} {target.id}", inline=True)
        embed.add_field(name="Moderator", value=f"{moderator.mention}", inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_thumbnail(url=target.avatar.url if target.avatar else None)

        asyncio.create_task(channel.send(embed=embed))


    @classmethod
    async def get_or_create_mute_role(cls, guild: discord.Guild)-> discord.Role:
        """
        Get Mute role by guild
        """
        try:
            guild_setting = await GuildService.get_guild_setting(guild_id=guild.id)
            if not guild_setting:
                logger.error(f"Failed to get guild setting for mute role create or get")
                raise GenericError("Server data not found")

            ## Check role id in guild collection
            mute_role_id = guild_setting.roles.mute_role_id if guild_setting.roles else None
            if  not mute_role_id:
                permissions = discord.Permissions(view_channel=False, send_messages=False)
                role = await cls.create_role(guild=guild, role_name="Mute", permission= permissions)
                guild_collection = GuildService.get_guild_collection()

                update = await guild_collection.update_one(
                    {"guild_id": guild.id},
                    {"$set":{"roles.mute_role_id": role.id}},
                    upsert=True
                )
                if update.modified_count > 0:
                    return role
                else:
                    raise GenericError(f"Failed to create role {role.name}")

            mute_role = guild.get_role(mute_role_id)
            if not mute_role:
                raise GenericError(f"Failed to create role {mute_role_id}")
            return mute_role
        except discord.Forbidden:
            logger.error(f"Failed to create role")
            raise GenericError(f"I do not have permission to create role")
        except Exception as e:
            logger.error(f"Failed to create role {e}")
            raise GenericError(f"Failed to create role {e}")


    @classmethod
    async def create_role(cls, guild: discord.Guild, role_name: str, permission: discord.Permissions)-> discord.Role :
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
    async def save_member_role(cls, member: discord.Member, guild_id: int, roles: List[discord.Role]) -> bool:
        if not roles:
            return False

        role_ids = [role.id for role in roles]
        user_collection: AsyncIOMotorCollection = Database.user()

        result = await user_collection.update_one(
            {"user_id": member.id, "guild_id": guild_id},
            {
                "$setOnInsert": {"user_id": member.id, "guild_id": guild_id},
                "$addToSet": {"roles": {"$each": role_ids}}
            },
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None


    @classmethod
    async def get_user_roles_from_database(cls, user_id: int, guild: discord.Guild) -> Optional[List[discord.Role]]:
        """
        Get user roles from database
        """
        user_doc = await UserService.get_user_data(user_id=user_id, guild_id=guild.id)
        if not user_doc:
            return None
        roles_id = user_doc.roles or []

        roles = [
            role for role_id in roles_id
            if (role := guild.get_role(role_id)) is not None
        ]
        return roles









