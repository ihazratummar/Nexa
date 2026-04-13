import logging

import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorCollection

from core.database import Database
from core.perspective_api import analyze_comment, check_image_content, extract_scores, check_video_content
from modules.Automod.services import AutoModServices

VIDEO_EXTENSIONS = [".mp4", ".mov", ".avi", ".webm"]
IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif"]

from core.models.guild_models import AutoModSettings

class AutoModCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.infractions:AsyncIOMotorCollection = Database.user_infractions()
        # In-memory stores for spam/duplicate detection (replaces Redis)
        self._last_messages: dict[str, str] = {}      # "{guild_id}:{user_id}" -> last message content
        self._spam_counters: dict[str, list] = {}      # "{guild_id}:{user_id}" -> [timestamp, ...]

    @commands.hybrid_command(name="toggle_automod", description="Enable AutoMod")
    @commands.has_permissions(manage_messages=True)
    async def toggle_automod(self, ctx: commands.Context):
        guild_id = ctx.guild.id
        toggle = True
        guild_settings_collection = AutoModServices.get_guild_settings_collection()
        guild_doc = await guild_settings_collection.find_one({"guild_id": guild_id})
        if guild_doc:
            automod = guild_doc.get("automod_enabled", True)
            toggle = automod != True

        await guild_settings_collection.update_one(
            {"guild_id": guild_id},
            {"$set": {"automod_enabled": toggle}}, upsert=True,
        )
        new_guild_doc = await guild_settings_collection.find_one({"guild_id": guild_id})
        new_automod = new_guild_doc.get("automod_enabled", True)
        if new_automod:
            toggle = "enabled"
        else:
            toggle = "disabled"
        await ctx.send(f"AutoMod has been {toggle} for this guild.")


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore bots
        if message.author.bot:
            return

        # Ignore messages with no content AND no media (attachments/embeds)
        # This allows image-only messages to pass through for AI moderation
        if not message.content and not message.attachments and not message.embeds:
            return

        guild_id = str(message.guild.id)
        auto_mod_settings_collection = AutoModServices.get_auto_mod_settings_collection()
        # Fetch AutoMod Settings
        data = await auto_mod_settings_collection.find_one({"guild_id": guild_id})
        if not data:
            return
            
        settings = AutoModSettings(**data)
        
        # 1. Check Global Enable
        if not settings.global_settings.is_enabled:
            return

        # 2. Check Global Ignored Channels
        if str(message.channel.id) in settings.global_settings.ignored_channels:
            return

        # 3. Check Global Ignored Roles
        user_role_ids = [str(r.id) for r in message.author.roles]
        if any(rid in settings.global_settings.ignored_roles for rid in user_role_ids):
            return

        # --- GLOBAL CHANNEL RESTRICTIONS ---
        # ... (existing code) ...

        # --- FILTERS ---
        
        # 0. AI Moderation (Premium)
        if settings.filters.ai_moderation.enabled:
            # Check ignores FIRST to save API calls
            if AutoModServices.is_ignored(message, settings.filters.ai_moderation):
                pass # Skip AI check if ignored
            else:
                # Text Analysis
                if message.content:
                    toxicity_threshold = settings.filters.ai_moderation.custom_config.get("toxicity_threshold", 80)
                    score = await analyze_comment(message.content)
                    if score and (score * 100) > toxicity_threshold:
                        await AutoModServices.handle_action(message, settings.filters.ai_moderation, f"Toxic content detected (Score: {int(score*100)}%)", settings=settings)
                        return

                # Image/Video Analysis
                if message.attachments or message.embeds:
                    nudity_threshold = settings.filters.ai_moderation.custom_config.get("nudity_threshold", 80)
                    gore_threshold = settings.filters.ai_moderation.custom_config.get("gore_threshold", 80)
                    
                    media_urls = [a.url for a in message.attachments] + [e.url for e in message.embeds if e.url]
                    
                    for url in media_urls:
                        # Check if image or video
                        is_video = any(ext in url.lower() for ext in VIDEO_EXTENSIONS)
                        result = None
                        try:
                            if is_video:
                                result = await check_video_content(url)
                            else:
                                result = await check_image_content(url)
                        except Exception as e:
                            logging.error(f"AI Moderation API Error: {e}")
                            continue
                        
                        if result:
                            # logging.info(f"AI Check Result for {url}: {result}") # Uncomment for full debug
                            scores = extract_scores(result)
                            logging.info(f"AI Scores for {url}: {scores}")
                            
                            for category, score in scores:
                                score_pct = score * 100
                                logging.info(f"Checking {category}: {score_pct}% vs Threshold: {nudity_threshold if 'nudity' in category else gore_threshold}%")
                                
                                if "nudity" in category and score_pct > nudity_threshold:
                                    await AutoModServices.handle_action(message, settings.filters.ai_moderation, f"NSFW content detected ({category}: {int(score_pct)}%)", settings=settings)
                                    return
                                if ("gore" in category or "violence" in category) and score_pct > gore_threshold:
                                    await AutoModServices.handle_action(message, settings.filters.ai_moderation, f"Graphic violence detected ({category}: {int(score_pct)}%)", settings=settings)
                                    return

        # 1. Links
        if settings.filters.links.enabled:
             if "http" in message.content:
                 if not AutoModServices.is_ignored(message, settings.filters.links):
                     await AutoModServices.handle_action(message, settings.filters.links, "Links not allowed", settings=settings)
                     return

        # 2. Discord Invites
        if settings.filters.discord_invites.enabled:
            if "discord.gg/" in message.content or "discord.com/invite/" in message.content:
                 if not AutoModServices.is_ignored(message, settings.filters.discord_invites):
                     await AutoModServices.handle_action(message, settings.filters.discord_invites, "Discord invites not allowed", settings=settings)
                     return

        # 3. Bad Words
        if settings.filters.bad_words.enabled:
            bad_words = settings.filters.bad_words.custom_config.get("bad_words", [])
            if bad_words:
                content_lower = message.content.lower()
                if any(word.lower() in content_lower for word in bad_words):
                    if not AutoModServices.is_ignored(message, settings.filters.bad_words):
                        await AutoModServices.handle_action(message, settings.filters.bad_words, "Profanity detected", settings=settings)
                        return

        # 4. Spammed Caps
        if settings.filters.spammed_caps.enabled:
            if len(message.content) > 10: # Min length to trigger
                caps_count = sum(1 for c in message.content if c.isupper())
                max_caps_pct = settings.filters.spammed_caps.custom_config.get("max_caps_percentage", 70)
                if (caps_count / len(message.content)) * 100 > max_caps_pct:
                    if not AutoModServices.is_ignored(message, settings.filters.spammed_caps):
                        await AutoModServices.handle_action(message, settings.filters.spammed_caps, "Excessive caps", settings=settings)
                        return

        # 5. Mass Mention
        if settings.filters.mass_mention.enabled:
            max_mentions = settings.filters.mass_mention.custom_config.get("max_mentions", 5)
            if len(message.mentions) > max_mentions:
                if not AutoModServices.is_ignored(message, settings.filters.mass_mention):
                    await AutoModServices.handle_action(message, settings.filters.mass_mention, "Mass mention detected", settings=settings)
                    return

        # 6. Emoji Spam
        if settings.filters.emoji_spam.enabled:
            import re
            custom_emojis = re.findall(r'<:\w*:\d*>', message.content)
            unicode_emojis = re.findall(r'[^\w\s,.]', message.content) # Simplified unicode check, might need better regex
            # Better unicode emoji regex:
            # emoji_count = len(re.findall(r'[^\w\s,]', message.content)) # Very rough
            # Let's count custom emojis + a heuristic for unicode
            
            # Using a slightly better regex for unicode emojis if possible, or just counting custom for now to be safe
            emoji_count = len(custom_emojis)
            
            # Simple unicode check (non-ascii) - this is aggressive but works for many cases
            # Or iterate characters.
            # For robustness, let's stick to custom emojis + basic non-ascii count if needed.
            # But user asked for "emoji spam".
            
            # Let's use a common emoji regex pattern if we can import it, otherwise simple count.
            # Assuming mostly custom emojis for discord spam.
            
            max_emojis = settings.filters.emoji_spam.custom_config.get("max_emojis", 10)
            if emoji_count > max_emojis:
                if not AutoModServices.is_ignored(message, settings.filters.emoji_spam):
                    await AutoModServices.handle_action(message, settings.filters.emoji_spam, "Too many emojis", settings=settings)
                    return

        # 7. Repeated Messages / Duplicate Text
        if settings.filters.repeated_messages.enabled or settings.filters.duplicate_text.enabled:
            # Use in-memory dict to check last message
            mem_key = f"{guild_id}:{message.author.id}"
            last_content = self._last_messages.get(mem_key)
            
            if last_content and last_content == message.content:
                if not AutoModServices.is_ignored(message, settings.filters.repeated_messages):
                     await AutoModServices.handle_action(message, settings.filters.repeated_messages, "Repeated message", settings=settings)
                     return
            
            # Save current message
            self._last_messages[mem_key] = message.content

        # 8. Anti-Spam (Rate Limit)
        if settings.filters.spam.enabled:
            import time
            spam_key = f"{guild_id}:{message.author.id}"
            now = time.time()
            window = 5  # 5 second window
            
            # Get or create timestamp list, prune old entries
            timestamps = self._spam_counters.get(spam_key, [])
            timestamps = [t for t in timestamps if now - t < window]
            timestamps.append(now)
            self._spam_counters[spam_key] = timestamps
            
            max_messages = 5
            
            if len(timestamps) > max_messages:
                 if not AutoModServices.is_ignored(message= message, filter_config= settings.filters.spam):
                     await AutoModServices.handle_action(message, settings.filters.spam, "Sending messages too fast", settings=settings)
                     return



    
    
async def setup(bot):
    await bot.add_cog(AutoModCog(bot))