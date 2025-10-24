import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorCollection

from bot.core.constant import DbCons


class WelcomeCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db
        self.guild_collection: AsyncIOMotorCollection = self.db[DbCons.GUILD_SETTINGS_COLLECTION.value]
        self.embed_collection: AsyncIOMotorCollection = self.db[DbCons.EMBED_COLLECTION.value]

    ## Setup welcome channel
    @commands.hybrid_command()
    @commands.has_permissions(administrator=True)
    async def welcome(self, ctx: commands.Context, channel: discord.TextChannel = None):
        await ctx.defer()
        if not channel:
            channel = ctx.channel
        guild_id = ctx.guild.id

        update = {
            "$set": {
                "guild_id": guild_id,
                "guild_name": ctx.guild.name,
                "welcome_enabled": True,
                "channels.welcome_channel_id": channel.id,
            }
        }

        await self.guild_collection.update_one({"guild_id": guild_id}, update, upsert=True)

        await ctx.send(
            f"Successfully {channel.mention} is your welcome channel."
        )

    @commands.hybrid_command(name="set_new_member_role", description="Set the new member role")
    @commands.has_permissions(administrator=True)
    async def set_new_member_role(self, ctx: commands.Context, roles: commands.Greedy[discord.Role]):
        await ctx.defer()
        guild = ctx.guild
        try:
            roles_id = [ role.id for role in roles]
            mentions = [role.mention for role in roles]
        except commands.RoleNotFound:
            await ctx.send(f"Roles not found")
            return

        await self.guild_collection.update_one(
            {"guild_id": guild.id},
            {
                "$set": {
                    "roles.new_member_role": roles_id  # replace with provided list
                }
            },
            upsert=True
        )

        await ctx.send(f"New member role set to {", ".join(mentions)}.")


    @commands.hybrid_command(name="set_bot_role", description="Set the bot role")
    @commands.has_permissions(administrator=True)
    async def set_bot_role(self, ctx: commands.Context, roles: commands.Greedy[discord.Role]):
        await ctx.defer()
        guild = ctx.guild
        try:
            roles_id = [role.id for role in roles]
            mentions = [role.mention for role in roles]
        except commands.RoleNotFound:
            await ctx.send(f"Roles not found")
            return

        await self.guild_collection.update_one(
            {"guild_id": guild.id},
            {
                "$set": {
                    "roles.bot_roles": roles_id  # replace with provided list
                }
            },
            upsert=True
        )

        await ctx.send(f"New bot role set to {", ".join(mentions)}.")


    @commands.hybrid_command(name="boost_channel")
    @commands.has_permissions(administrator=True)
    async def set_boost_channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        await ctx.defer()

        if not channel:
            channel = ctx.channel

        await self.guild_collection.update_one(
            {"guild_id": ctx.guild.id},
            {"$set":{
                "channels.boost_channel": channel.id
            }},
            upsert= True
        )
        await ctx.send(f"{channel.mention} is now set for boost announcements", ephemeral=True)



