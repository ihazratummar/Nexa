import json
import logging

import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorCollection

from bot.core.constant import DbCons


class Welcomer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db
        self.guild_collection: AsyncIOMotorCollection = self.db[DbCons.GUILD_SETTINGS_COLLECTION.value]
        self.embed_collection: AsyncIOMotorCollection = self.db[DbCons.EMBED_COLLECTION.value]

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):

        guild_id = member.guild.id
        guild_data = await self.guild_collection.find_one({"guild_id": guild_id})
        if not guild_data:
            return
            
        # Assign roles to new members and bots
        await self.auto_role_for_new_members_and_bots(member)
        
        is_welcome_enabled = guild_data.get("welcome_enabled")
        if not is_welcome_enabled:
            return

        

        await self.welcome_message(member)
        
    async def auto_role_for_new_members_and_bots(self, member: discord.Member):
        guild_id = member.guild.id
        guild_data = await self.guild_collection.find_one({"guild_id": guild_id})
        if not guild_data:
            return
        new_member_role_id = guild_data.get("new_member_role")
        bot_role_id = guild_data.get("bot_role")
        if new_member_role_id:
            new_member_role = member.guild.get_role(new_member_role_id)
            if new_member_role:
                await member.add_roles(new_member_role)
        if member.bot:
            bot_role = member.guild.get_role(bot_role_id)
            if bot_role:
                await member.add_roles(bot_role)
    
    async def welcome_message(self, member: discord.Member):
        guild = member.guild
        guild_data = await self.guild_collection.find_one({"guild_id": guild.id})

        if not guild_data or not guild_data.get("welcome_enabled"):
            return


        welcome_channel_id = guild_data.get("channels", {}).get("welcome_channel_id")

        if not welcome_channel_id:
            return

        channel = self.bot.get_channel(welcome_channel_id)
        if not channel:
            return

        try:
            embed_builder = self.bot.get_cog("EmbedBuilder")
            get_preset = await embed_builder.get_preset(guild_id=guild.id, name="welcome_embed")
            if not get_preset:
                return

            build_embed = await embed_builder.build_embed(preset=get_preset, server= guild,  user=member, channel= channel)

        except Exception as e:
            print(f"Error loading welcome embed data: {e}")
            return

        await channel.send(embed=build_embed)

    ## Setup welcome channel
    @commands.hybrid_command()
    @commands.has_permissions(administrator=True)
    async def welcome(self, ctx: commands.Context, channel: discord.TextChannel = None ):
        await ctx.defer()
        if not channel:
            channel = ctx.channel
        guild_id = ctx.guild.id

        update = {
            "$set":{
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


    @commands.Cog.listener()
    async def on_boost(self, guild: discord.Guild, booster: discord.Member):
        boost_channel_id = 1123909975522160691
        boost_channel = self.bot.get_channel(boost_channel_id)
        if boost_channel:
            message = (f"Thank you for boosting, {booster.mention}",)
        await boost_channel.send_message(message)

    @commands.hybrid_command(name="setinvite")
    @commands.has_permissions(administrator = True)
    async def setInvite(self, ctx: commands.Context):
        with open("data/invite.json", "r") as file:
            record = json.load(file)

        record[str(ctx.guild.id)] = str(ctx.channel.id)
        with open("data/invite.json", "w") as file:
            json.dump(record, file)

        await ctx.send("Set invite log successful")

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if len(before.roles) < len(after.roles):
            new_roles = [role for role in after.roles if role not in before.roles]
            for role in new_roles:
                if role.is_premium_subscriber():
                    boost_channel_id = 1123909975522160691
                    boost_channel = self.bot.get_channel(boost_channel_id)
                    if boost_channel:
                        message = (f"Thank you for boosting, {after.mention}",)
                        await boost_channel.send(message)

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):

        if before.premium_subscription_count < after.premium_subscription_count:
            boost_difference = after.premium_subscription_count - before.premium_subscription_count
            channel = self.bot.get_channel(1123909975522160691)

            if channel:
                await channel.send(
                    f"Thank you for boosting, {after.name}!\n"
                    f"Total Boosts: {after.premium_subscription_count}\n"
                    f"New Boosts: {boost_difference}"
                )

    @commands.hybrid_command(name = "testboost")
    async def testboost(self, ctx: commands.Context):
        guild = ctx.guild
        before = guild
        after = guild

        before_boost = before.premium_subscription_count
        after.premium_subscription_count += 1  # Simulating a boost

        await self.on_guild_update(before, after)
        await ctx.send(f"Test boost event triggered. Before Boost: {before_boost} After Boost: {after.premium_subscription_count}")
                        


async def setup(bot: commands.Bot):
    await bot.add_cog(Welcomer(bot))
