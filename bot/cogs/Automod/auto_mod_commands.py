import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorCollection

from bot.core.checks import guard
from bot.core.constant import DbCons


from bot.core.models.guild_models import ModerationSettings

class AutoModCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.collection:AsyncIOMotorCollection = self.bot.db[DbCons.GUILD_SETTINGS_COLLECTION.value]
        self.mod_settings_collection:AsyncIOMotorCollection = self.bot.db[DbCons.MOD_SETTINGS.value]

    @commands.hybrid_command(name="toggle_automod", description="Enable AutoMod")
    @commands.has_permissions(manage_messages=True)
    @guard("toggle_automod")
    async def toggle_automod(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id)
        toggle = True
        guild_doc = await self.collection.find_one({"guild_id": guild_id})
        if guild_doc:
            automod = guild_doc.get("automod_enabled", True)
            toggle = automod != True

        await self.collection.update_one(
            {"guild_id": guild_id},
            {"$set": {"automod_enabled": toggle}}, upsert=True,
        )
        new_guild_doc = await self.collection.find_one({"guild_id": guild_id})
        new_automod = new_guild_doc.get("automod_enabled", True)
        if new_automod:
            toggle = "enabled"
        else:
            toggle = "disabled"
        await ctx.send(f"AutoMod has been {toggle} for this guild.")


    


    