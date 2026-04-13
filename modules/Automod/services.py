import datetime

import discord
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorCollection

from core.database import Database
from core.models.guild_models import AutoModSettings
from core.models.infraction_models import UserInfraction, InfractionHistory


class AutoModServices:

    @classmethod
    def get_guild_settings_collection(cls) -> AsyncIOMotorCollection:
        return Database.guild_settings()

    @classmethod
    def get_auto_mod_settings_collection(cls) -> AsyncIOMotorCollection:
        return Database.automod_settings()

    @classmethod
    def get_user_infraction_collection(cls) -> AsyncIOMotorCollection:
        return Database.user_infractions()

    @classmethod
    def is_ignored(cls, message, filter_config):
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

    @classmethod
    async def handle_action(cls, message: discord.Message, filter_config, reason: str,
                             settings: AutoModSettings = None):
        actions = filter_config.actions

        collection = cls.get_user_infraction_collection()

        # Default to delete if no actions specified, especially for AI moderation which implies removal
        if not actions:
            actions = ["delete"]

        if "delete" in actions:
            try:
                await message.delete()
            except discord.NotFound:
                pass  # Already deleted
            except discord.Forbidden:
                pass  # Can't delete

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
                infraction_data = await collection.find_one({"guild_id": guild_id, "user_id": user_id})

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
                await collection.update_one(
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
                                    await message.channel.send(
                                        f"{message.author.mention} has been kicked for reaching {rule.threshold} warnings.")

                                    # Reset warnings after kick
                                    infraction.warning_count = 0
                                    await collection.update_one(
                                        {"guild_id": guild_id, "user_id": user_id},
                                        {"$set": {"warning_count": 0}}
                                    )
                                except Exception as e:
                                    logger.error(f"Escalation kick failed: {e}")

                            elif rule.action == "ban":
                                try:
                                    await message.author.ban(reason=escalation_reason)
                                    await message.channel.send(
                                        f"{message.author.mention} has been banned for reaching {rule.threshold} warnings.")

                                    # Reset warnings after ban
                                    infraction.warning_count = 0
                                    await collection.update_one(
                                        {"guild_id": guild_id, "user_id": user_id},
                                        {"$set": {"warning_count": 0}}
                                    )
                                except Exception as e:
                                    logger.error(f"Escalation ban failed: {e}")

                            elif rule.action == "timeout":
                                try:
                                    duration = rule.duration if rule.duration else 3600  # Default 1 hour
                                    timeout_until = discord.utils.utcnow() + datetime.timedelta(seconds=duration)
                                    await message.author.timeout(timeout_until, reason=escalation_reason)
                                    await message.channel.send(
                                        f"{message.author.mention} has been timed out for reaching {rule.threshold} warnings.")
                                except Exception as e:
                                    logger.error(f"Escalation timeout failed: {e}")

            except Exception as e:
                logger.error(f"Failed to process warning: {e}")

        # Send alert message (if not just silent delete)
        # We can send a message to the channel
        try:
            await message.channel.send(f"{message.author.mention}, {reason}", delete_after=5)
        except:
            pass