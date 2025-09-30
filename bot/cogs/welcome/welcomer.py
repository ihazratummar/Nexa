import json

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

        roles = guild_data.get("roles")

        new_member_role_id = roles.get("new_member_role",[])
        bot_role_id = roles.get("bot_role",[])
        if new_member_role_id:
            for role_id in new_member_role_id:
                new_member_role = member.guild.get_role(role_id)
                if new_member_role:
                    await member.add_roles(new_member_role)
        if member.bot:
            for role_id in bot_role_id:
                bot_role = member.guild.get_role(role_id)
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