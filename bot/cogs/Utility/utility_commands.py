from datetime import datetime, timedelta

import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorCollection

from bot.core.constant import Color, DbCons
from bot.core.openai_utils import get_chat_completion
from bot.core.ratelimit import redis_cooldown
from bot.core.checks import guard, premium_only


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db
        self.guild_settings_collection:AsyncIOMotorCollection = self.db[DbCons.GUILD_SETTINGS_COLLECTION.value]
        self.last_seen_collection:AsyncIOMotorCollection = self.db[DbCons.LAST_SEEN_COLLECTION.value]


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        data = {
            "user_id": message.author.id,
            "channel_id" : message.channel.id,
            "last_seen": datetime.now()
        }

        await self.last_seen_collection.update_one(
            {"user_id": message.author.id},
            {"$set": data},
            upsert=True
        )

    @commands.hybrid_command(name="help", description= "Get all the commands list")
    @guard("help")
    async def help(self, interaction: commands.Context):
        embed = discord.Embed(
            title= "Help",
            description= "List of commands all the commands",
            color= discord.Color.from_str(Color.PRIMARY_COLOR)
        )

        for c in self.bot.cogs:
             cog = self.bot.get_cog(c)
             if any(cog.walk_commands()):
                 embed.add_field(name=cog.qualified_name, value= " , ".join(f"`{i.name}`" for i in cog.walk_commands()), inline= False)
        await interaction.send(embed=embed)


    @commands.hybrid_command(name="ping", description="server ping")
    @guard("ping")
    async def ping(self, interaction: commands.Context):
        await interaction.send(
            f"Ping {round(self.bot.latency * 1000)} ms"
        )

    @commands.hybrid_command(name="invite", description="Invite Link")
    @guard("invite")
    async def invite(self, interaction: commands.Context):
        link = await interaction.channel.create_invite(max_age=0)
        await interaction.send(link)

    @commands.hybrid_command(name='server', description = "Get the server information")
    @guard("server")
    async def server_info(self, ctx: commands.Context):
        embed=discord.Embed(title=f"{ctx.guild.name}", description="Information of this Server", color=0x00FFFF)
        embed.add_field(name="👑Owner", value=f"{ctx.guild.owner}", inline=True)
        embed.add_field(name="👥Total members", value=f"{ctx.guild.member_count}", inline=True)
        embed.add_field(name="🧸Categories", value=f"{len(ctx.guild.categories)}", inline=True)
        embed.add_field(name="🔮Total Text Channels", value=f"{len(ctx.guild.text_channels)}", inline=True)
        embed.add_field(name="🎑Total Voice Channels", value=f"{len(ctx.guild.voice_channels)}", inline=True)
        embed.add_field(name="🎐Total Roles", value=f"{len(ctx.guild.roles)}", inline=True)
        embed.set_thumbnail(url= ctx.guild.icon.url)
        embed.set_footer(text= f"ID: {ctx.guild.id} | Server Created - {ctx.guild.created_at.strftime('%A, %d %B %Y %H:%M')}")

        if ctx.guild.banner:
            embed.set_image(url= ctx.guild.banner.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="userinfo", description= "Display a user's info")
    @guard("userinfo")
    async def userinfo(self, ctx: commands.Context, * , user: discord.Member = None):
        if user is None:
            user = ctx.author

        full_user = await self.bot.fetch_user(user.id)

            # Format the datetime objects
        account_created = user.created_at.strftime("%A, %d %B %Y %H:%M")
        server_joining_date = user.joined_at.strftime("%A, %d %B %Y %H:%M")
        embed=discord.Embed(title=f"{user.name}", description="", color=0x00FFFF)
        embed.add_field(name="ID", value=f"{user.id}", inline=True)
        embed.add_field(name="Nickname", value=f"{user.nick}", inline=True)
        embed.add_field(name="", value=f"", inline=True)
        embed.add_field(name="Account Created", value= f"> `{account_created}`" ,inline= False)
        embed.add_field(name="Server joining Date", value=f"> `{server_joining_date}`", inline=False)
        if len(user.roles) >1:
            role_string = '  '.join([r.mention for r in user.roles][1:])
            embed.add_field(name= "Roles[{}]".format(len(user.roles)-1), value=f"{role_string}", inline= False)
        embed.set_author(name=f"{user.name}", icon_url=f"{user.avatar.url}")
        embed.set_thumbnail(url=f"{user.avatar.url}")

        if full_user.banner:
            embed.set_image(url=full_user.banner.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="avatar", description = "Display a User's Avatar")
    @guard("avatar")
    async def avatar(self, ctx: commands.Context, user:discord.Member = None):
        if user is None:
            user = ctx.author
        
        embed=discord.Embed(title=f"{user.name}", description=f"[Avatar URL]({user.avatar.url})", color=0x00FFFF)
        embed.set_image(url=f"{user.avatar.url}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name= "channel_info")
    @guard("channel_info")
    async def channel_info(self, ctx: commands.Context, *, channel: discord.TextChannel = None):
        if channel is None:
            channel = ctx.channel
        embed=discord.Embed(title=f"Channel Info: {channel.name}",color=0x00FFFF)
        embed.add_field(name=f"Channel Name", value=f"<#{channel.id}>", inline=False)
        embed.add_field(name="Channel Topic", value=f"{channel.topic if channel.topic else 'No Topic Set'}", inline= False),
        embed.add_field(name="Channel Category", value=f"{channel.category.name if channel.category else 'No category'}", inline= False)
        embed.add_field(name="Position", value=f"{channel.position}", inline=True)
        embed.add_field(name='NSFW', value=f"{channel.is_nsfw()}", inline=True),
        embed.add_field(name="NEWS", value=f"{channel.is_news()}", inline= True)
        embed.set_footer(text=f"ID: {channel.id} | Created At : {channel.created_at.strftime('%A, %d %B %Y %H:%M')}"),
        embed.set_thumbnail(url=f"{ctx.guild.icon.url}")
        await ctx.send(embed=embed)


    @commands.hybrid_command(name="emojis", description="Displays all the emojis in the server.")
    @guard("emojis")
    async def emojis(self, ctx: commands.Context):
        emojis = ctx.guild.emojis
        if not emojis:
            await ctx.send("This server has no custom emojis.")
            return

        emoji_list = " ".join(str(emoji) for emoji in emojis)
        embed = discord.Embed(title=f"Emojis in {ctx.guild.name}", description=emoji_list, color=0x00FFFF)
        await ctx.send(embed=embed)


    @commands.hybrid_command(name="clear", description="Clears a specified number of messages")
    @commands.has_permissions(manage_messages = True)
    @guard("clear")
    async def clear(self, ctx: commands.Context, number: int = 20, force: bool = False):
        await ctx.defer(ephemeral=True)

        # Discord API limit: Cannot bulk delete messages older than 14 days
        # Deleting older messages one-by-one triggers rate limits (429)
        
        
        cutoff = datetime.now() - timedelta(days=14)

        if force:
            # User explicitly requested to delete everything, including old messages
            # This WILL trigger rate limits if messages are old, but we proceed
            await ctx.send(f"Deleting {number} messages (Force Mode enabled)... This might take a while if messages are old.", ephemeral=True)
            deleted = await ctx.channel.purge(limit=number + 1)
        else:
            # Safe Mode: Only delete messages younger than 14 days
            # This uses the Bulk Delete API which is instant and safe
            deleted = await ctx.channel.purge(limit=number + 1, after=cutoff)
            
            if len(deleted) < number:
                 await ctx.send(f"Deleted {len(deleted)-1} messages. (Messages older than 14 days were skipped. Use `force:True` to delete them, but it will be slow.)", delete_after=10, ephemeral=True)
                 return

        await ctx.send(f"Deleted {len(deleted)-1} messages.", delete_after=5, ephemeral=True)


    @commands.hybrid_command(name="summarize", description="Summarize discord channel text")
    @redis_cooldown(1, 600, commands.BucketType.user)
    @guard("summarize")
    async def summarize(self, ctx: commands.Context, limit: int = 20):
        if limit > 50:
            await ctx.send("Limit should be less than 50")
            return
        
        await ctx.defer()

        messages = [msg async for msg in ctx.channel.history(limit=limit)]
        messages = list(reversed(messages))  # Oldest to newest
        content = "\n".join([
            f"{msg.author.display_name}: {msg.content}" 
            for msg in messages 
            if msg.content and not msg.author.bot and not msg.content.startswith(ctx.prefix)
            ])

        prompt = f"Summarize the following Discord conversation:\n\n{content}\n\nSummary in bullet points:"
        summary = await get_chat_completion(prompt)
        embed = discord.Embed(title="Summary", description=summary, color=0x00FFFF)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="seen", description="Check when a user was last seen")
    @guard("seen")
    async def seen (self, ctx: commands.Context, member: discord.Member = None):

        member = member or ctx.author

        data = await self.last_seen_collection.find_one({"user_id": member.id})

        if not data:
            await ctx.send(f"No data found for {member.name}.")
            return
        
        last_seen = data["last_seen"]
        channel_id = data["channel_id"]
        channel = self.bot.get_channel(channel_id)

        timestamp = int(last_seen.timestamp())
        channel_mention = channel.mention if channel else "Unknown Channel"

        embed = discord.Embed(
            title=f"{member.name}'s Last Seen",
            description=f"Last seen in {channel_mention}",
            color=0x00FFFF
        )
        embed.add_field(name="Last Seen", value=f"<t:{timestamp}:R>", inline=False)
        embed.set_footer(text=f"User ID: {member.id}")
        embed.set_thumbnail(url=member.avatar.url)
        await ctx.send(embed=embed)



async def setup(bot: commands.Bot):
    await bot.add_cog(Utility(bot))
        