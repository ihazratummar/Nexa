import discord
from discord.ext import commands
from bot.config import Bot
import json
from bot.core.perspective_api import analyze_comment, check_image_content, extract_scores, check_video_content



VIDEO_EXTENSIONS = [".mp4", ".mov", ".avi", ".webm"]
IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif"]

class AutoMod(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = bot.mongo_client["BotDatabase"]
        self.collection = self.db["guild_settings"]

    async def auto_mod(self, message):

        guild_id = str(message.guild.id)
        guild_data = self.collection.find_one({"guild_id": guild_id})
        if not guild_data:
            return
        automod_enabled = guild_data.get("automod_enabled", False)
        if not automod_enabled:
            return
        # Check if the message is from a bot
    
        if message.author.bot:
            return
        
        if "discord.gg/" in message.content or "discord.com/invite/" in message.content or "http" in message.content:
            if isinstance(message.author, discord.Member):
                if (
                    message.author.guild_permissions.administrator
                    or message.author == message.guild.owner
                ):
                    pass
                else:
                    await message.delete()

                    dm_message = "Links not allowed"
                    try:
                        await message.author.send(dm_message)
                    except discord.Forbidden:
                        pass

                    log_channel_id = self.log_channels.get(str(message.guild.id))
                    log_channel = self.bot.get_channel(log_channel_id)
                    if log_channel:
                        embed = discord.Embed(
                            title="Invite Link Deleted",
                            description=f"Invite Link Deleted in <#{message.channel.id}>",
                            color=discord.Color.red(),
                        )
                        embed.add_field(name="Author", value=message.author.mention)
                        embed.add_field(name="Content", value=message.content)
                        await log_channel.send(embed=embed)

        # Analyze text toxicity

    
        score = await analyze_comment(message.content)
        print(f"[TEXT CHECK] Message: {message.content} | Toxicity Score: {score:.2f}")

        if score >= 0.80:
            await message.delete()
            await message.channel.send(
                f"Message deleted due to toxicity. Score: {score:.2f}"
            )
        elif score >= 0.60:
            await message.channel.send(
                f"{message.author.mention}, please keep it respectful ({score:.2f})."
            )

        # Check image attachments
        for attachment in message.attachments:
            filename = attachment.filename.lower()

            # ✅ Check for images
            if any(filename.endswith(ext) for ext in IMAGE_EXTENSIONS):
                print(f"[IMAGE CHECK] Checking image: {attachment.url}")
                data = await check_image_content(attachment.url)
                print(f"[IMAGE RESULT] {data}")
                flagged_scores = extract_scores(data)

                if flagged_scores:
                    await message.delete()
                    reasons = "\n".join([f"{k}: {v:.2f}" for k, v in flagged_scores])
                    await message.channel.send(
                        f"Message deleted due to inappropriate image content. Triggered:\n{reasons}"
                    )
                    print(f"[DELETED] Image flagged by: {reasons}")
                    break

            # ✅ Check for videos
            elif any(filename.endswith(ext) for ext in VIDEO_EXTENSIONS):
                print(f"[VIDEO CHECK] Checking video: {attachment.url}")
                data = await check_video_content(attachment.url)
                print(f"[VIDEO RESULT] {data}")
                flagged_scores = extract_scores(data)

                if flagged_scores:
                    await message.delete()
                    reasons = "\n".join([f"{k}: {v:.2f}" for k, v in flagged_scores])
                    await message.channel.send(
                        f"Message deleted due to inappropriate video content. Triggered:\n{reasons}"
                    )
                    print(f"[DELETED] Video flagged by: {reasons}")
                    break

    
    @commands.hybrid_command(name="enable_automod", description="Enable AutoMod")
    @commands.has_permissions(administrator=True)
    async def enable_automod(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id)

        guild_data = self.collection.find_one({"guild_id": guild_id})

        # if not guild_data:
        #     await ctx.send("Guild data not found.")
        #     return
        
        self.collection.update_one(
            {"guild_id": guild_id},
            {"$set": {"automod_enabled": True}}, upsert=True,
        )
        await ctx.send("AutoMod has been enabled for this guild.")

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoMod(bot))
