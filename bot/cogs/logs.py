import discord
from discord.ext import commands
import os
import json

FILE_PATH = "data/log_channels.json"

if not os.path.exists('data'):
    os.mkdir('data')

def load_log_channels():
    if not os.path.exists(FILE_PATH) or os.stat(FILE_PATH).st_size == 0:
        with open(FILE_PATH, "w") as file:
            json.dump({}, file)
    
    with open(FILE_PATH, "r") as file:
        return json.load(file)

def save_log_channels(data):
    with open(FILE_PATH, "w") as file:
        json.dump(data, file, indent=4)

class Logs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.log_channels = load_log_channels()

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        before_roles = set(before.roles)
        after_roles = set(after.roles)

        added_roles = after_roles - before_roles
        removed_roles = before_roles - after_roles

        if added_roles or removed_roles:
            await self.log_role_changes(before, after, added_roles, removed_roles)

        if before.nick != after.nick:
            await self.log_nickname_chane(before, after)


    async def log_role_changes(self, before: discord.Member, after: discord.member, added_roles, removed_roles):
        guild_id = str(after.guild.id)
        if guild_id in self.log_channels:
            log_channel_id = self.log_channels[guild_id]
            log_channel = self.bot.get_channel(log_channel_id)

            if not log_channel:
                        print(f'Log channel with ID {log_channel_id} not found.')
                        return

            embed = discord.Embed(
                title="Role Changes",
                color=0x00FFFF,
                timestamp=discord.utils.utcnow()
            )
            embed.set_author(name=after.name, icon_url=after.avatar.url)
            embed.set_footer(text=f"User ID: {after.id}")

            if added_roles:
                embed.add_field(
                    name="Roles Added",
                    value="\n".join([role.mention for role in added_roles]),
                    inline=False
                )
            if removed_roles:
                embed.add_field(
                    name="Roles Removed",
                    value="\n".join([role.mention for role in removed_roles]),
                    inline=False
                )

            await log_channel.send(embed=embed)

    async def log_nickname_chane(self, before: discord.Member, after: discord.Member):
        guild_id = str(after.guild.id)
        if guild_id in self.log_channels:
            log_channel_id = self.log_channels[guild_id]
            log_channel = self.bot.get_channel(log_channel_id)

            if not log_channel:
                print(f"Log channel with ID {log_channel_id} not found.")
                return
            
            embed=discord.Embed(title="Nickname Changes", description=None, color=0x00FFFF, timestamp=discord.utils.utcnow())
            embed.set_author(name=after.name, icon_url=after.avatar._url)
            embed.add_field(name="Before", value=before.nick if before.nick else before.name, inline=False)
            embed.add_field(name="After", value=after.nick if after.nick else after.name, inline=False)
            await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        guild_id = str(guild.id)

        if guild_id in self.log_channels:
            log_channel_id = self.log_channels[guild_id]
            log_channel = self.bot.get_channel(log_channel_id)

            if not log_channel:
                print(f'Log channel with ID {log_channel_id} not found.')
                return
            
            embed = discord.Embed(
                title="Member Banned",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_author(name=user.name, icon_url=user.avatar.url)
            embed.set_footer(text=f"User ID: {user.id}")

            embed.add_field(
                name="User",
                value=f"{user.name}#{user.discriminator}",
                inline=True
            )

            await log_channel.send(embed=embed)


    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        guild_id = str(guild.id)
        if guild_id in self.log_channels:
            log_channel_id = self.log_channels[guild_id]
            log_channel = self.bot.get_channel(log_channel_id)

            if not log_channel:
                print(f'Log channel with ID {log_channel_id} not found.')
                return

            embed = discord.Embed(
                title="Member Unbanned",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_author(name=user.name, icon_url=user.avatar.url)
            embed.set_footer(text=f"User ID: {user.id}")

            embed.add_field(
                name="User",
                value=f"{user.name}#{user.discriminator}",
                inline=True
            )

            await log_channel.send(embed=embed)


    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild_id = str(member.guild.id)
        if guild_id in self.log_channels:
            log_channel_id = self.log_channels[guild_id]
            log_channel = member.guild.get_channel(log_channel_id)

            if not log_channel:
                print(f'Log channel with ID {log_channel_id} not found.')
                return
        
            if isinstance(member, discord.Member):
                action = "kicked"
            elif isinstance(member, discord.User):
                action = "left"
            else:
                action = "removed"

            embed = discord.Embed(
                title=f"{member} was {action}",
                color=0x00FFFF,
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text=f"User ID: {member.id}")

            await log_channel.send(embed=embed)

    @commands.hybrid_command(name="setlogchannel")
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Set the log channel for role changes."""
        if not channel:
            channel = ctx.channel

        guild_id = str(ctx.guild.id)
        self.log_channels[guild_id] = channel.id
        save_log_channels(self.log_channels)
        await ctx.send(f"Log channel set to {channel.mention} for role changes.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Logs(bot))
