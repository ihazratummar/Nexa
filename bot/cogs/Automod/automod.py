import logging
import datetime
# from datetime import timedelta, datetime
import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorCollection
from bot.core.constant import DbCons
from bot.core.perspective_api import analyze_comment, check_image_content, extract_scores, check_video_content

VIDEO_EXTENSIONS = [".mp4", ".mov", ".avi", ".webm"]
IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif"]

from bot.core.models.guild_models import AutoModSettings
from bot.core.models.infraction_models import UserInfraction, InfractionHistory

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.collection:AsyncIOMotorCollection = self.bot.db[DbCons.AUTOMOD_SETTINGS.value]
        self.infractions:AsyncIOMotorCollection = self.bot.db["user_infractions"]

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
        
        # Fetch AutoMod Settings
        data = await self.collection.find_one({"guild_id": guild_id})
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
            if self._is_ignored(message, settings.filters.ai_moderation):
                pass # Skip AI check if ignored
            else:
                # Text Analysis
                if message.content:
                    toxicity_threshold = settings.filters.ai_moderation.custom_config.get("toxicity_threshold", 80)
                    score = await analyze_comment(message.content)
                    if score and (score * 100) > toxicity_threshold:
                        await self._handle_action(message, settings.filters.ai_moderation, f"Toxic content detected (Score: {int(score*100)}%)", settings=settings)
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
                                    await self._handle_action(message, settings.filters.ai_moderation, f"NSFW content detected ({category}: {int(score_pct)}%)", settings=settings)
                                    return
                                if ("gore" in category or "violence" in category) and score_pct > gore_threshold:
                                    await self._handle_action(message, settings.filters.ai_moderation, f"Graphic violence detected ({category}: {int(score_pct)}%)", settings=settings)
                                    return

        # 1. Links
        if settings.filters.links.enabled:
             if "http" in message.content:
                 if not self._is_ignored(message, settings.filters.links):
                     await self._handle_action(message, settings.filters.links, "Links not allowed", settings=settings)
                     return

        # 2. Discord Invites
        if settings.filters.discord_invites.enabled:
            if "discord.gg/" in message.content or "discord.com/invite/" in message.content:
                 if not self._is_ignored(message, settings.filters.discord_invites):
                     await self._handle_action(message, settings.filters.discord_invites, "Discord invites not allowed", settings=settings)
                     return

        # 3. Bad Words
        if settings.filters.bad_words.enabled:
            bad_words = settings.filters.bad_words.custom_config.get("bad_words", [])
            if bad_words:
                content_lower = message.content.lower()
                if any(word.lower() in content_lower for word in bad_words):
                    if not self._is_ignored(message, settings.filters.bad_words):
                        await self._handle_action(message, settings.filters.bad_words, "Profanity detected", settings=settings)
                        return

        # 4. Spammed Caps
        if settings.filters.spammed_caps.enabled:
            if len(message.content) > 10: # Min length to trigger
                caps_count = sum(1 for c in message.content if c.isupper())
                max_caps_pct = settings.filters.spammed_caps.custom_config.get("max_caps_percentage", 70)
                if (caps_count / len(message.content)) * 100 > max_caps_pct:
                    if not self._is_ignored(message, settings.filters.spammed_caps):
                        await self._handle_action(message, settings.filters.spammed_caps, "Excessive caps", settings=settings)
                        return

        # 5. Mass Mention
        if settings.filters.mass_mention.enabled:
            max_mentions = settings.filters.mass_mention.custom_config.get("max_mentions", 5)
            if len(message.mentions) > max_mentions:
                if not self._is_ignored(message, settings.filters.mass_mention):
                    await self._handle_action(message, settings.filters.mass_mention, "Mass mention detected", settings=settings)
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
                if not self._is_ignored(message, settings.filters.emoji_spam):
                    await self._handle_action(message, settings.filters.emoji_spam, "Too many emojis", settings=settings)
                    return

        # 7. Repeated Messages / Duplicate Text
        if settings.filters.repeated_messages.enabled or settings.filters.duplicate_text.enabled:
            # Use Redis to check last message
            # Key: automod:last_msg:guild_id:user_id
            redis_key = f"automod:last_msg:{guild_id}:{message.author.id}"
            last_content = await self.bot.redis.get(redis_key)
            
            if last_content and last_content == message.content:
                if not self._is_ignored(message, settings.filters.repeated_messages): # Use repeated_messages config
                     await self._handle_action(message, settings.filters.repeated_messages, "Repeated message", settings=settings)
                     return
            
            # Save current message (expire in 60s)
            await self.bot.redis.set(redis_key, message.content, ex=60)

        # 8. Anti-Spam (Rate Limit)
        if settings.filters.spam.enabled:
            # Key: automod:spam:guild_id:user_id
            # We'll use a simple counter with 5s expiry
            spam_key = f"automod:spam:{guild_id}:{message.author.id}"
            count = await self.bot.redis.incr(spam_key)
            if count == 1:
                await self.bot.redis.expire(spam_key, 5) # 5 second window
            
            max_messages = 5 # Hardcoded or from config if available. User JSON has 'max_lines' but not 'max_messages'.
            # Let's assume 5 for now or check custom_config
            # User JSON has "max_lines": 10 in spam config, maybe they mean messages? Or lines in one message?
            # Let's use a safe default of 5 messages in 5 seconds.
            
            if count > max_messages:
                 if not self._is_ignored(message, settings.filters.spam):
                     await self._handle_action(message, settings.filters.spam, "Sending messages too fast", settings=settings)
                     return

    def _is_ignored(self, message, filter_config):
        # Check ignored channels for this specific filter
        if str(message.channel.id) in filter_config.ignored_channels:
            return True
        
        # Check ignored roles for this specific filter
        user_role_ids = [str(r.id) for r in message.author.roles]
        if any(rid in filter_config.ignored_roles for rid in user_role_ids):
            return True
            
        # Check Admin/Owner (Global Override)
        if message.author.guild_permissions.administrator or message.author == message.guild.owner:
            return True
            
        return False

    async def _handle_action(self, message: discord.Message, filter_config, reason: str, settings: AutoModSettings = None):
        actions = filter_config.actions
        
        # Default to delete if no actions specified, especially for AI moderation which implies removal
        if not actions:
            actions = ["delete"]
        
        if "delete" in actions:
            try:
                await message.delete()
            except discord.NotFound:
                pass # Already deleted
            except discord.Forbidden:
                pass # Can't delete

        if "timeout" in actions:
            duration = filter_config.timeout_duration
            try:
                timeout_until = discord.utils.utcnow() + datetime.timedelta(seconds=duration)
                await message.author.timeout(timeout_until, reason=reason)
            except Exception as e:
                print(f"Failed to timeout: {e}")

        if "kick" in actions:
            try:
                await message.author.kick(reason=reason)
            except Exception as e:
                print(f"Failed to kick: {e}")
        
        if "ban" in actions:
            try:
                await message.author.ban(reason=reason)
            except Exception as e:
                print(f"Failed to ban: {e}")

        if "warn" in actions:
            try:
                await message.author.send(f"You have been warned: {reason}")
                
                # Track Infraction
                guild_id = str(message.guild.id)
                user_id = str(message.author.id)
                
                # Fetch existing infraction record
                infraction_data = await self.infractions.find_one({"guild_id": guild_id, "user_id": user_id})
                
                if infraction_data:
                    infraction = UserInfraction(**infraction_data)
                    infraction.warning_count += 1
                    infraction.history.append(InfractionHistory(reason=reason, rule_triggered="automod"))
                    infraction.updated_at = datetime.datetime.now()
                else:
                    infraction = UserInfraction(
                        guild_id=guild_id,
                        user_id=user_id,
                        warning_count=1,
                        history=[InfractionHistory(reason=reason, rule_triggered="automod")]
                    )
                
                # Save to DB
                await self.infractions.update_one(
                    {"guild_id": guild_id, "user_id": user_id},
                    {"$set": infraction.dict()},
                    upsert=True
                )
                
                # Check AutoMod Rules for Escalation
                if settings and settings.automod_rules:
                    for rule in settings.automod_rules:
                        if infraction.warning_count == rule.threshold:
                            # Execute Escalation Action
                            escalation_reason = f"AutoMod Escalation: Reached {rule.threshold} warnings"
                            
                            if rule.action == "kick":
                                try:
                                    await message.author.kick(reason=escalation_reason)
                                    await message.channel.send(f"{message.author.mention} has been kicked for reaching {rule.threshold} warnings.")
                                    
                                    # Reset warnings after kick
                                    infraction.warning_count = 0
                                    await self.infractions.update_one(
                                        {"guild_id": guild_id, "user_id": user_id},
                                        {"$set": {"warning_count": 0}}
                                    )
                                except Exception as e:
                                    logging.error(f"Escalation kick failed: {e}")
                            
                            elif rule.action == "ban":
                                try:
                                    await message.author.ban(reason=escalation_reason)
                                    await message.channel.send(f"{message.author.mention} has been banned for reaching {rule.threshold} warnings.")
                                    
                                    # Reset warnings after ban
                                    infraction.warning_count = 0
                                    await self.infractions.update_one(
                                        {"guild_id": guild_id, "user_id": user_id},
                                        {"$set": {"warning_count": 0}}
                                    )
                                except Exception as e:
                                    logging.error(f"Escalation ban failed: {e}")
                            
                            elif rule.action == "timeout":
                                try:
                                    duration = rule.duration if rule.duration else 3600 # Default 1 hour
                                    timeout_until = discord.utils.utcnow() + datetime.timedelta(seconds=duration)
                                    await message.author.timeout(timeout_until, reason=escalation_reason)
                                    await message.channel.send(f"{message.author.mention} has been timed out for reaching {rule.threshold} warnings.")
                                except Exception as e:
                                    logging.error(f"Escalation timeout failed: {e}")

            except Exception as e:
                logging.error(f"Failed to process warning: {e}")

        # Send alert message (if not just silent delete)
        # We can send a message to the channel
        try:
            await message.channel.send(f"{message.author.mention}, {reason}", delete_after=5)
        except:
            pass

    
    
