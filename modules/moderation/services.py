import asyncio

from motor.motor_asyncio import AsyncIOMotorCollection
import discord
from typing_extensions import Literal

from core.database import Database
from core.models.guild_models import ModerationSettings
from modules.guild.services import GuildService


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



