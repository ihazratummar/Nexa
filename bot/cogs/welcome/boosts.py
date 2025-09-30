import discord
from discord.ext import  commands
from motor.motor_asyncio import AsyncIOMotorCollection

from bot.core.constant import DbCons


class Boosts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db
        self.guild_collection: AsyncIOMotorCollection = self.db[DbCons.GUILD_SETTINGS_COLLECTION.value]

    @commands.hybrid_command(name="testboost")
    async def testboost(self, ctx: commands.Context):
        guild = ctx.guild
        before = guild
        after = guild

        before_boost = before.premium_subscription_count
        after.premium_subscription_count += 1  # Simulating a boost
        await self.on_guild_update(before, after)
        await ctx.send(
            f"Test boost event triggered. Before Boost: {before_boost} After Boost: {after.premium_subscription_count}")


    @commands.Cog.listener()
    async def on_boost(self, guild: discord.Guild, booster: discord.Member):

        guild_config = await self.guild_collection.find_one({"guild_id": guild.id})
        boost_channel_id = guild_config.get("channels", {}).get("boost_channel")
        boost_channel = self.bot.get_channel(boost_channel_id)
        if boost_channel:
            message = (f"Thank you for boosting, {booster.mention}",)
        await boost_channel.send_message(message)

    async def welcome_member_update(self, before: discord.Member, after: discord.Member):
        guild_doc = await self.guild_collection.find_one({"guild_id": before.guild.id})
        boost_channel_id = guild_doc.get("channels", {}).get("boost_channel")
        if len(before.roles) < len(after.roles):
            new_roles = [role for role in after.roles if role not in before.roles]
            for role in new_roles:
                if role.is_premium_subscriber():
                    boost_channel = self.bot.get_channel(boost_channel_id)
                    if boost_channel:
                        message = (f"Thank you for boosting, {after.mention}",)
                        await boost_channel.send(message)

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        if before.premium_subscription_count < after.premium_subscription_count:
            boost_difference = after.premium_subscription_count - before.premium_subscription_count

            guild_doc = await self.guild_collection.find_one({"guild_id": before.id})
            channel_id = guild_doc.get("channels", {}).get("boost_channel")
            channel = self.bot.get_channel(channel_id)

            if channel:
                await channel.send(
                    f"Thank you for boosting, {after.name}!\n"
                    f"Total Boosts: {after.premium_subscription_count}\n"
                    f"New Boosts: {boost_difference}"
                )
