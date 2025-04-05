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
        self.log_channels = self.load_log_channels()

    def load_log_channels(self):
        try:
            with open("Bot/cogs/Automod/log_channels.json", "r") as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def save_log_channels(self):
        with open("Bot/cogs/Automod/log_channels.json", "w") as file:
            json.dump(self.log_channels, file, indent=4)

    

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        if "discord.gg/" in message.content or "discord.com/invite/" in message.content or "https" in message.content or "https" in message.content:
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

        await self.bot.process_commands(message)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setlog(self, ctx, channel: discord.TextChannel):
        """Set the log channel for deleted messages."""
        self.log_channels[str(ctx.guild.id)] = channel.id
        self.save_log_channels()
        await ctx.send(f"Log channel set to {channel.mention}")


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoMod(bot))
