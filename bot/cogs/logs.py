import discord
from discord.ext import commands

from bot.core.constant import DbCons


class Logs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.mongo_client[DbCons.BOT_DATABASE]
        self.collection = self.db[DbCons.GUILD_SETTINGS_COLLECTION]

    def load_log_channels(self, guild_id: str) -> int:
        guild_data = self.collection.find_one({"guild_id": str(guild_id)})
        if not guild_data:
            return None
        log_channel_id = guild_data.get("log_channel")
        if not log_channel_id:
            return None
        return int(log_channel_id)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        before_roles = set(before.roles)
        after_roles = set(after.roles)

        added_roles = after_roles - before_roles
        removed_roles = before_roles - after_roles

        if added_roles or removed_roles:
            await self.log_role_changes(before = before, after=after, added_roles = added_roles, removed_roles = removed_roles)

        if before.nick != after.nick:
            await self.log_nickname_chane(before, after)


    async def log_role_changes(self, before: discord.Member, after: discord.Member, added_roles, removed_roles):
        log_channel_id = self.load_log_channels(after.guild.id)
        if not log_channel_id:
            print(f'Log channel with ID {log_channel_id} not found.')
            return
        log_channel = self.bot.get_channel(log_channel_id)

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
        log_channel_id = self.load_log_channels(after.guild.id)
        log_channel = self.bot.get_channel(log_channel_id)

        if not log_channel:
            print(f"Log channel with ID {log_channel_id} not found.")
            return
        
        embed=discord.Embed(title="Nickname Changes", description=None, color=0x00FFFF, timestamp=discord.utils.utcnow())
        embed.set_author(name=after.name, icon_url=after.avatar.url)
        embed.add_field(name="Before", value=before.nick if before.nick else before.name, inline=False)
        embed.add_field(name="After", value=after.nick if after.nick else after.name, inline=False)
        await log_channel.send(embed=embed)
            

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        log_channel_id = self.load_log_channels(guild.id)
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
        log_channel_id = self.load_log_channels(guild_id)
        if log_channel_id:
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
        log_channel_id = self.load_log_channels(guild_id)
        if log_channel_id:
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
        guild_id = str(ctx.guild.id)

        guild_data = self.collection.find_one({"guild_id": guild_id})
        if not guild_data:
            await ctx.send("Guild data not found.")
            return
        
        if channel is None:
            await ctx.send("Please specify a channel.")
            return
        
        channel_id = str(channel.id)

        self.collection.update_one(
            {"guild_id": guild_id},
            {"$set": {"log_channel": channel_id}}
        )
        await ctx.send(f"Log channel set to {channel.mention}.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Logs(bot))
