import discord
from discord.ext import commands
import json
from bot.core.models import guild_models
from bot.core.embed.embed_builder import build_welcome_embed


class Welcomer(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.mongo_client["BotDatabase"]
        self.collection = self.db["guild_settings"]

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):

        guild_id = str(member.guild.id)

        guild_data = self.collection.find_one({"guild_id": guild_id})
        if not guild_data:
            return
            
        # Assign roles to new members and bots
        await self.auto_role_for_new_members_and_bots(member)
        
        is_welcome_enabled = guild_data.get("welcome_enabled")
        if not is_welcome_enabled:
            return
        
        
        await self.welcome_message(member)
        
    async def auto_role_for_new_members_and_bots(self, member: discord.Member):
        guild_id = str(member.guild.id)
        guild_data = self.collection.find_one({"guild_id": guild_id})
        if not guild_data:
            return
        new_member_role_id = guild_data.get("new_member_role")
        bot_role_id = guild_data.get("bot_role")
        if new_member_role_id:
            new_member_role = member.guild.get_role(int(new_member_role_id))
            if new_member_role:
                await member.add_roles(new_member_role)
        if member.bot:
            bot_role = member.guild.get_role(int(bot_role_id))
            if bot_role:
                await member.add_roles(bot_role)
    
    async def welcome_message(self, member: discord.Member):
        guild_id = str(member.guild.id)
        guild_data = self.collection.find_one({"guild_id": guild_id})

        if not guild_data or not guild_data.get("welcome_enabled"):
            return

        welcome_channel_id = guild_data.get("welcome_channel_id")
        welcome_embed_data = guild_data.get("welcome_embed")

        if not welcome_channel_id or not welcome_embed_data:
            return

        channel = self.bot.get_channel(int(welcome_channel_id))
        if not channel:
            return

        try:
            welcome_embed = guild_models.WelcomeEmbed(**welcome_embed_data)
        except Exception as e:
            print(f"Error loading welcome embed data: {e}")
            return

        embed = build_welcome_embed(welcome_embed)
        embed.set_thumbnail(url=member.avatar.url)

        await channel.send(embed=embed)

    ## Setup welcome channel
    @commands.hybrid_command()
    @commands.has_permissions(administrator=True)
    async def welcome(self, ctx: commands.Context, title: str = None,description:str =None,color: str = None,image: str = None ):
        guild_id = str(ctx.guild.id)

        welcome_embed = guild_models.WelcomeEmbed(
            title=title or "Welcome!",
            description=description or "Glad to have you here!",
            color=color or None,
            image_url=image or None,
            thumbnail_url=ctx.guild.icon.url if ctx.guild.icon else None,
            footer=f"Welcome to {ctx.guild.name}!",
        )

        update = {
            "$set":{
                "guild_id": guild_id,
                "guild_name": str(ctx.guild.name),
                "welcome_enabled": True,
                "welcome_channel_id": str(ctx.channel.id),
                "welcome_embed": welcome_embed.dict(),
            }
        }

        self.collection.update_one({"guild_id": guild_id}, update, upsert=True)

        await ctx.send(
            f"Successfully {ctx.channel.mention} is your welcome channel."
        )

    @commands.hybrid_command(name = "add_welcome_field", description = "Add a field to the welcome embed")
    @commands.has_permissions(administrator=True)
    async def add_welcome_field(self, ctx: commands.Context, name: str, value: str, inline: bool = True):
        guild_id = str(ctx.guild.id)

        # Fetch the current welcome embed data
        guild_data = self.collection.find_one({"guild_id": guild_id})
        if not guild_data or not guild_data.get("welcome_embed"):
            await ctx.send("Welcome embed is not set up yet.")
            return

        try:
            welcome_embed = guild_models.WelcomeEmbed(**guild_data["welcome_embed"])
        except Exception as e:
            await ctx.send(f"Error loading welcome embed data: {e}")
            return
        
        if len(welcome_embed.fields) >= 25:
            await ctx.send("Cannot add more than 25 fields to the embed.")
            return
        
        # Add the new field
        welcome_embed.fields.append(guild_models.EmbedField(name=name, value=value, inline=inline))

        # Update the database

        self.collection.update_one(
            {"guild_id": guild_id},
            {"$set": {"welcome_embed": welcome_embed.dict()}}
        )

        await ctx.send(f"Field '{name}' added to the welcome embed.")

    @commands.hybrid_command(name = "remove_welcome_field", description = "Remove a field from the welcome embed")
    @commands.has_permissions(administrator=True)
    async def remove_welcome_field(self, ctx: commands.Context, name: str):
        guild_id = str(ctx.guild.id)

        # Fetch the current welcome embed data
        guild_data = self.collection.find_one({"guild_id": guild_id})
        if not guild_data or not guild_data.get("welcome_embed"):
            await ctx.send("Welcome embed is not set up yet.")
            return

        try:
            welcome_embed = guild_models.WelcomeEmbed(**guild_data["welcome_embed"])
        except Exception as e:
            await ctx.send(f"Error loading welcome embed data: {e}")
            return

        # Remove the field
        welcome_embed.fields = [field for field in welcome_embed.fields if field.name != name]
        
        if len(welcome_embed.fields) == len(guild_data["welcome_embed"]["fields"]):
            await ctx.send(f"No field named '{name}' found in the welcome embed.")
            return

        # Update the database
        self.collection.update_one(
            {"guild_id": guild_id},
            {"$set": {"welcome_embed": welcome_embed.dict()}}
        )

        await ctx.send(f"Field '{name}' removed from the welcome embed.")

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
