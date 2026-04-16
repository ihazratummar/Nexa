import discord
from discord.ext import  commands

from modules.moderation.services import ModerationService


class Listener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener("on_guild_channel_create")
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        """
        Listens for channel creation events and add mute roles
        """

        """Add mute role to channel"""
        await ModerationService.apply_mute_role_to_single_channel(guild=channel.guild, channel=channel)

async def setup(bot):
    await bot.add_cog(Listener(bot))