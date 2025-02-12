import discord
from discord.ext import commands
import json



class Welcomer(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            first_role_id = 511215381420048384
            first_role = member.guild.get_role(first_role_id)
            if first_role:
                await member.add_roles(first_role)

            second_role_id = 567387858546065408
            second_role = member.guild.get_role(second_role_id)
            if second_role:
                await member.add_roles(second_role)
        
        try:
            with open("data/welcome.json", "r") as f:
                records = json.load(f)
            welcome_data = records[str(member.guild.id)]
        except (FileNotFoundError, KeyError):
            return
        channel_id = welcome_data["channel_id"]
        if not channel_id:
            return
        channel = self.bot.get_channel(int(channel_id))
        embed = discord.Embed(
            title=welcome_data['title'].format(member = member) if 'title' in welcome_data and welcome_data['title'] else f"Welcome to {member.guild.name}",
            description=welcome_data['description'].format(member = member) if 'description' in welcome_data and welcome_data['description'] else f"Hi {member.mention} welcome to your discord server. Enjoy your stay. ",
            color=0x00FFFF,
        )
        embed.set_thumbnail(url=member.avatar.url)
        if welcome_data['image']:
            embed.set_image(
                url=f"{welcome_data['image']}"
            )  
        

        channel_fields = [
            "📣｜sᴇʀᴠᴇʀ-ʀᴜʟᴇs",
            "🎐｜ᴀʙᴏᴜᴛ-ʜᴀᴢʀᴀᴛ",
        ]

        channels_found = []

        for channel_name in channel_fields:
            channel_field = discord.utils.get(
                member.guild.text_channels, name=channel_name
            )
            if channel_field:
                channels_found.append(channel_field.mention)

        if channels_found:
            embed.add_field(
                name="Important Channels",
                value="\n".join(channels_found),
                inline=True,
            )

        channel_fields = [
            "📌｜sᴛʀᴇᴀᴍ",
            "📌｜sᴏᴄɪᴀʟ",
        ]

        channels_found = []

        for channel_name in channel_fields:
            channel_field = discord.utils.get(
                member.guild.text_channels, name=channel_name
            )
            if channel_field:
                channels_found.append(channel_field.mention)

        if channels_found:
            embed.add_field(
                name="Notification",
                value="\n".join(channels_found),
                inline=True,
            )

        inviter = None
        async for entry in member.guild.audit_logs(limit=1):
            if entry.action == discord.AuditLogAction.invite_create:
                inviter = entry.user
                break

        embed.add_field(
            name="Invited By",
            value=inviter.mention if inviter else "Unknown",
            inline=False,
        )

        await channel.send(content=member.mention, embed=embed)

        role_id = 874718527284727838  # Replace with the actual role ID
        role = member.guild.get_role(role_id)
        if role:
            await member.add_roles(role)


        with open("data/invite.json", "r") as f:
            records = json.load(f)
        try:
            channel_id = records[str(member.guild.id)]
        except KeyError:
            return
        invite_channel = self.bot.get_channel(int(channel_id))
        if not invite_channel:
            return
        
        inviter = None
        async for entry in member.guild.audit_logs(limit=1):
            if entry.action == discord.AuditLogAction.invite_create:
                inviter = entry.user
                break
        await invite_channel.send(f"{member.mention} Invited By {inviter}")

    ## Setup welcome channel
    @commands.hybrid_command()
    @commands.has_permissions(administrator=True)
    async def welcome(self, ctx: commands.Context, 
                        title: str = None, 
                        description:str =None,
                        image: str = None ):
        with open("data/welcome.json", "r") as f:
            records = json.load(f)

        records[str(ctx.guild.id)] = {
            "guild_name" : str(ctx.guild.name),
            "channel_id": str(ctx.channel.id),
            "title": title,
            "description": description,
            "image": image
        }
        with open("data/welcome.json", "w") as f:
            json.dump(records, f)

        await ctx.send(
            f"Successfully {ctx.channel.mention} is your welcome channel."
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


async def setup(bot: commands.Bot):
    await bot.add_cog(Welcomer(bot))
