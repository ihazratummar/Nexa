import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorCollection

from bot.core.checks import guard
from bot.core.constant import DbCons
from bot.core.models.guild_models import ModerationSettings


class ModerationCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.collection:AsyncIOMotorCollection = self.bot.db[DbCons.GUILD_SETTINGS_COLLECTION.value]
        self.mod_settings_collection:AsyncIOMotorCollection = self.bot.db[DbCons.MOD_SETTINGS.value]

    async def get_mod_settings(self, guild_id: str) -> ModerationSettings:
        data = await self.mod_settings_collection.find_one({"guild_id": guild_id})
        if data:
            return ModerationSettings(**data)

        # Create default
        new_settings = ModerationSettings(guild_id=guild_id)
        await self.mod_settings_collection.insert_one(new_settings.model_dump())
        return new_settings

    @commands.hybrid_command(name="toggle_moderation", description="Enable/Disable Moderation System")
    @commands.has_permissions(administrator=True)
    @guard("toggle_moderation")
    async def toggle_moderation(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id)
        settings = await self.get_mod_settings(guild_id)

        new_state = not settings.is_moderation_settings_enabled

        await self.mod_settings_collection.update_one(
            {"guild_id": guild_id},
            {"$set": {"is_moderation_settings_enabled": new_state}},
            upsert=True
        )

        status = "enabled" if new_state else "disabled"
        await ctx.send(f"🛡️ Moderation system has been **{status}**.")

    @commands.hybrid_command(name="ban", description="Ban a user")
    @commands.has_permissions(manage_messages=True)
    @guard("ban")
    async def ban(self, ctx: commands.Context, member: discord.Member):
        # Check Moderation Settings
        settings = await self.get_mod_settings(str(ctx.guild.id))
        if not settings.is_moderation_settings_enabled:
            await ctx.send("⚠️ Moderation system is disabled in this server.")
            return

        if not member:
            await ctx.send(f"If you are not trying to ban a ghost, please mention a member.")
            return

        await member.ban(reason=f"For violating discord server rules.")
        await ctx.send(f"{member.mention} has been ban in this server for good.")
