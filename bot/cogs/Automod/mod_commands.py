import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorCollection

from bot.core.constant import DbCons


class ModCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.collection:AsyncIOMotorCollection = self.bot.db[DbCons.GUILD_SETTINGS_COLLECTION.value]


    @commands.hybrid_command(name="toggle_automod", description="Enable AutoMod")
    @commands.has_permissions(administrator=True)
    async def toggle_automod(self, ctx: commands.Context):
        guild_id = ctx.guild.id
        toggle = True
        guild_doc = await self.collection.find_one({"guild_id": ctx.guild.id})
        if guild_doc:
            automod = guild_doc.get("automod_enabled", True)
            toggle = automod != True
        
        await self.collection.update_one(
            {"guild_id": guild_id},
            {"$set": {"automod_enabled": toggle}}, upsert=True,
        )
        new_guild_doc = await self.collection.find_one({"guild_id": ctx.guild.id})
        new_automod = new_guild_doc.get("automod_enabled", True)
        if new_automod:
            toggle = "enabled"
        else:
            toggle = "disabled"
        await ctx.send(f"AutoMod has been {toggle} for this guild.")

    @commands.hybrid_command(name="ban", description="Ban a user")
    @commands.has_permissions(manage_messages = True)
    async def ban(self, ctx: commands.Context, member: discord.Member):
        if not member:
            await ctx.send(f"If you are not trying to ban a ghost, please mention a member.")
            return

        await member.ban(reason=f"For violating discord server rules.")
        await ctx.send(f"{member.mention} has been ban in this server for good.")   
    


    