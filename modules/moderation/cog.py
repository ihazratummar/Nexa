import asyncio
from datetime import timedelta
from typing import Union

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorCollection

from core.checks import moderation_enabled_predicate, hierarchy_check
from core.database import Database
from core.embed.embed_builder import embed_builder
from core.utils.time_parse import parse_duration
from modules.Automod.services import AutoModServices
from modules.error.custom_errors import GenericError
from modules.guild.services import GuildService
from modules.moderation.services import ModerationService
from modules.moderation.ui import warning_embed, DeleteWarningsLogsUi


class ModerationCommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.collection: AsyncIOMotorCollection = AutoModServices.get_guild_settings_collection()
        self.mod_settings_collection: AsyncIOMotorCollection = Database.moderation_settings()

    @app_commands.command(name="toggle_moderation", description="Enable/Disable Moderation System")
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def toggle_moderation(self, interaction: commands.Context):
        guild_id = interaction.guild_id
        settings = await ModerationService.get_mod_settings(guild_id=guild_id)
        new_state = not settings.is_moderation_settings_enabled

        await self.mod_settings_collection.update_one(
            {"guild_id": guild_id},
            {"$set": {"is_moderation_settings_enabled": new_state}},
            upsert=True
        )

        status = "enabled" if new_state else "disabled"
        await interaction.response.send_message(f"🛡️ Moderation system has been **{status}**.")

    @app_commands.command(name="ban", description="Ban a user")
    @app_commands.default_permissions(ban_members=True)
    @app_commands.guild_only()
    @app_commands.check(moderation_enabled_predicate)
    @hierarchy_check(action="ban")
    async def ban(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer()

        if not member:
            await interaction.followup.send(f"If you are not trying to ban a ghost, please mention a member.")
            return

        try:
            await member.ban(reason=f"For violating discord server rules.")
            await interaction.followup.send(f"{member.mention} has been banned from this server for good.")
            task = []
            task.append(
                ModerationService.send_logs(
                    guild=interaction.guild,
                    action="Ban",
                    moderator=interaction.user,
                    target=member,
                )
            )
            task.append(
                ModerationService.send_logs(
                    guild=interaction.guild,
                    action="Ban",
                    moderator=interaction.user,
                    target=member,
                )
            )
        except discord.Forbidden:
            await interaction.followup.send("❌ I do not have permission to ban this member.")
        except Exception as e:
            await interaction.followup.send(f"❌ An error occurred: {e}")

    @app_commands.command(name="unban", description="Unban a user")
    @app_commands.default_permissions(ban_members=True)
    @app_commands.guild_only()
    @app_commands.check(moderation_enabled_predicate)
    @hierarchy_check(action="unban")
    async def unban(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer()

        if not member:
            await interaction.followup.send(f"Please provide a valid user to unban.")
            return

        try:
            await interaction.guild.unban(member, reason=f"We decided to unban this user")
            await interaction.followup.send(f"{member.mention} has been unbanned from this server.")
        except discord.NotFound:
            await interaction.followup.send(f"❌ {member.name} is not banned in this server.")
        except discord.Forbidden:
            await interaction.followup.send("❌ I do not have permission to unban this user.")
        except Exception as e:
            await interaction.followup.send(f"❌ An error occurred: {e}")

    @app_commands.command(name="kick", description="Kick a user from the server")
    @app_commands.default_permissions(kick_members=True)
    @app_commands.guild_only()
    @app_commands.check(moderation_enabled_predicate)
    @hierarchy_check(action="kick")
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        await interaction.response.defer()

        # --- Hierarchy checks ---
        if member == interaction.user:
            await interaction.followup.send(f"Why would you kick yourself? 😅", ephemeral=True)
            return

        if not member:
            await interaction.followup.send(f"Please tag a user to kick.", ephemeral=True)
            return

        ## -- Notify user via DM before kicking----\
        reason_text = reason or "No reason provided."
        try:
            embed = embed_builder(
                title=f"You have been kicked from {interaction.guild.name}",
                color=discord.Color.orange(),
                timestamp=discord.utils.utcnow(),
            )
            embed.add_field(name="Reason", value=reason_text, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            icon_url = interaction.guild.icon.url if interaction.guild.icon else None
            embed.set_footer(text=interaction.guild.name, icon_url=icon_url)
            await member.send(embed=embed)
            dm_sent = True
        except discord.Forbidden:
            dm_sent = False

        try:
            await member.kick(reason=f"[{interaction.user}] {reason_text}")
        except discord.Forbidden:
            await interaction.followup.send(f"Failed to kick the user due to lack of permissions", ephemeral=True)
            return
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")

        await interaction.followup.send(f"{member.mention} has been kicked from this server.")

        task = []
        task.append(
            ModerationService.send_logs(
                guild=interaction.guild,
                action="Kick",
                moderator=interaction.user,
                target=member,
                reason=reason_text
            )
        )
        task.append(
            ModerationService.send_logs(
                guild=interaction.guild,
                action="Kick",
                moderator=interaction.user,
                target=member,
                reason=reason_text
            )
        )

    @app_commands.command(name="timeout", description="Timeout a user")
    @app_commands.default_permissions(mute_members=True)
    @app_commands.guild_only()
    @app_commands.check(moderation_enabled_predicate)
    @hierarchy_check(action="timeout")
    @app_commands.describe(
        duration="Duration of the timeout.(Example: 10s for 10 seconds and m,h,w (minutes, hours, weeks) etc.)",
        member="Mention a server member",
        reason="Reason for timeout",
    )
    async def timeout(self, interaction: discord.Interaction, duration: str, member: discord.Member,
                      reason: str = None):
        await interaction.response.defer()

        if member.is_timed_out():
            await interaction.followup.send(f"{member.name} has already been timed out in this server.")
            return

        if not duration:
            await interaction.followup.send(f"Please provide a valid duration to timeout.")
            return

        reason_text = reason or "No reason provided."
        try:
            time_delta = parse_duration(duration)
            max_timeout_limit = timedelta(days=28)

            if time_delta > max_timeout_limit:
                raise GenericError("Timeout duration cannot exceed 28 days")

            if time_delta.total_seconds() < 5:
                raise GenericError("Timeout duration must be at least 5 seconds")

            await member.timeout(time_delta, reason=reason_text)
            await interaction.followup.send(f"{member.mention} has been timed out from the server.")
        except discord.Forbidden:
            await interaction.followup.send(f"Failed to timeout the user due to lack of permissions", ephemeral=True)

        task = []
        task.append(ModerationService.record_moderation_logs(
            guild_id=interaction.guild_id,
            offender_id=member.id,
            moderator_id=interaction.user.id,
            reason=reason_text,
            action_type="Mute"
        ))
        task.append(ModerationService.send_logs(
            guild=interaction.guild,
            action="Timeout",
            moderator=interaction.user,
            target=member,
            reason=reason_text
        ))

        results = await asyncio.gather(*task, return_exceptions=True)
        for res in results:
            if isinstance(res, Exception):
                logger.error(f"Error occurred during the timeout action: {res}")

    @app_commands.command(name="remove_timeout", description="Remove a user timed out")
    @app_commands.default_permissions(mute_members=True)
    @app_commands.guild_only()
    @app_commands.check(moderation_enabled_predicate)
    @hierarchy_check(action="remove_timeout")
    @app_commands.describe(
        member="Mention a server member",
        reason="Reason for remove_timeout",
    )
    async def remove_timeout(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        await interaction.response.defer()
        try:
            reason_text = reason or "No reason provided."
            await member.timeout(None, reason=reason_text)
            await interaction.followup.send(f"{member.mention} has been removed from the server.")
        except discord.Forbidden:
            await interaction.followup.send(f"Failed to remove the user due to lack of permissions")

        await ModerationService.send_logs(
            guild=interaction.guild,
            action="Remove Timeout",
            moderator=interaction.user,
            target=member,
            reason=reason_text
        )

    @app_commands.command(name="mute", description="Mute a user")
    @app_commands.default_permissions(mute_members=True)
    @app_commands.guild_only()
    @app_commands.check(moderation_enabled_predicate)
    @hierarchy_check(action="mute")
    @app_commands.describe(
        member="Mention a server member",
    )
    async def mute_command(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        await interaction.response.defer()
        await self.mute(interaction, member, reason)

    @staticmethod
    async def mute(interaction: discord.Interaction, member: discord.Member, reason: str = None):
        _guild = interaction.guild
        if _guild is None:
            return
        try:
            reason_text = reason or "No reason provided."
            mute_role = await ModerationService.get_or_create_mute_role(guild=_guild)
            if not mute_role:
                raise GenericError("Failed to mute because of mute role failure")

            if mute_role in member.roles:
                await interaction.followup.send(f"{member.mention} has already been muted in this server.")
                return

            roles = [
                role for role in member.roles
                if not role.is_default() and role.id != mute_role.id
            ]
            if roles:
                await ModerationService.save_member_role(member=member, guild_id=_guild.id, roles=roles)

            await member.edit(roles=[mute_role], reason=reason_text)
            await interaction.followup.send(f"{member.mention} has been muted from the server.")
            asyncio.create_task(ModerationService.record_moderation_logs(
                guild_id=_guild.id,
                offender_id=member.id,
                moderator_id=interaction.user.id,
                reason=reason_text,
                action_type="Mute"
            ))
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")

    @app_commands.command(name="unmute", description="Unmute a user")
    @app_commands.default_permissions(mute_members=True)
    @app_commands.guild_only()
    @app_commands.check(moderation_enabled_predicate)
    @hierarchy_check(action="unmute")
    @app_commands.describe(
        member="Mention a server member",
    )
    async def unmute(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        await interaction.response.defer()
        try:
            guild = interaction.guild
            if guild is None:
                await interaction.followup.send(f"Failed to unmute because of guild failure")
                return
            mute_role = await ModerationService.get_or_create_mute_role(guild=member.guild)
            if not mute_role:
                raise GenericError("Failed to unmute because of mute role failure")
            if mute_role not in member.roles:
                raise GenericError("Failed to unmute because, user is not muted in this server")

            reason_text = reason or "No reason provided."
            user_roles = await ModerationService.get_user_roles_from_database(user_id=member.id, guild=guild)
            await member.edit(roles=user_roles or [], reason=reason_text)
            await interaction.followup.send(f"{member.mention} has been unmuted from the server.")
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")

    @app_commands.command(name="set_mute_role", description="Set mute role")
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def set_mute_role(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.defer()

        guild = interaction.guild
        if guild is None:
            return

        try:
            if role >= guild.me.top_role:
                await interaction.followup.send("I cannot manage this role due to role hierarchy.")
                return

            await GuildService.update_guild_settings(
                guild_id=guild.id,
                **{"roles.mute_role_id": role.id}
            )

            # ✅ Always apply to channels regardless of DB update result
            await interaction.followup.send(
                f"Mute role set to {role.mention}. Applying to all channels in background...")

            task = asyncio.create_task(
                ModerationService.apply_mute_role_to_channels(mute_role=role, guild=guild)
            )

            def on_done(t: asyncio.Task):
                if t.exception():
                    logger.error(f"Failed to apply mute role to channels: {t.exception()}")

            task.add_done_callback(on_done)

        except discord.Forbidden:
            await interaction.followup.send("I don't have permission to manage channel permissions.")
        except Exception as e:
            logger.error(f"Failed to set mute role: {e}")
            await interaction.followup.send(f"An error occurred: {e}")

    @app_commands.command(name="slowmode", description="Set slowmode delay for a channel")
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    @app_commands.check(moderation_enabled_predicate)
    @app_commands.describe(
        channel="Mention a channel",
        duration="Set duration. Ex: 0 to disable, 10s, 10m, 1h, 6h",
    )
    async def slowmode(
            self,
            interaction: discord.Interaction,
            duration: str,
            channel: Union[
                discord.TextChannel, discord.VoiceChannel, discord.ForumChannel, discord.StageChannel, discord.Thread] = None
    ):
        await interaction.response.defer()

        try:
            SLOWMODE_SUPPORTED = (
                discord.TextChannel,
                discord.VoiceChannel,
                discord.Thread,
                discord.ForumChannel,
            )
            # Resolve channel
            target_channel = channel or interaction.channel
            if not isinstance(target_channel, SLOWMODE_SUPPORTED):
                await interaction.followup.send("Slowmode is not supported for this channel type.")
                return

            # ✅ Handle "0" as disable before parsing
            if duration.strip() == "0":
                parsed_time = timedelta(seconds=0)
            else:
                try:
                    parsed_time = parse_duration(duration_str=duration)
                except Exception:
                    await interaction.followup.send(
                        f"Invalid duration format `{duration}`. Ex: `0` to disable, `10s`, `5m`, `1h`, `6h`")
                    return

            max_duration = timedelta(hours=6)
            # ✅ Allow 0 to disable slowmode
            if parsed_time.total_seconds() < 0:
                await interaction.followup.send("Duration cannot be negative.")
                return

            if parsed_time > max_duration:
                await interaction.followup.send("Slowmode duration cannot exceed 6 hours.")
                return

            duration_in_seconds = int(parsed_time.total_seconds())
            await target_channel.edit(slowmode_delay=duration_in_seconds)
            # ✅ Clean success message
            if duration_in_seconds == 0:
                await interaction.followup.send(f"Slowmode disabled in {target_channel.mention}.")
            else:
                await interaction.followup.send(f"Slowmode set to `{duration}` in {target_channel.mention}.")
        except ValueError as e:
            await interaction.followup.send(f"Invalid duration format: {e}")
        except discord.Forbidden:
            await interaction.followup.send("I don't have permission to manage channel permissions.")
        except Exception as e:
            logger.error(f"Failed to set slowmode: {e}")
            await interaction.followup.send(f"An error occurred: {e}")

    @app_commands.command(name="warn", description="Warn a user")
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    @app_commands.check(moderation_enabled_predicate)
    @hierarchy_check(action="warn")
    @app_commands.describe(
        member="Mention a user to warn",
        reason="Reason for the warning"
    )
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """
        Warn a user and handle automatic punishments if thresholds are reached.
        """
        await interaction.response.defer()

        try:
            guild = interaction.guild
            if guild is None:
                return

            # 1. Count existing active warnings
            offense_count = await ModerationService.get_offense_count(
                guild_id=guild.id,
                offender_id=member.id,
                action_type="Warn"
            )

            # 2. Record the new warning in DB
            await ModerationService.record_moderation_logs(
                guild_id=guild.id,
                offender_id=member.id,
                moderator_id=interaction.user.id,
                action_type="Warn",
                reason=reason
            )

            # 3. Notification Embed for the current interaction
            embed = discord.Embed(
                title="User Warned",
                color=discord.Color.gold(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
            embed.add_field(name="User", value=f"{member.mention} (`{member.id}`)", inline=True)
            embed.add_field(name="Moderator", value=f"{interaction.user.mention}", inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Total Warnings", value=f"{offense_count + 1}", inline=True)
            embed.set_footer(text="Nexa Moderation")

            await interaction.followup.send(embed=embed)

            # 4. DM the user
            try:
                dm_embed = discord.Embed(
                    title=f"You have been warned in {guild.name}",
                    description=f"**Reason:** {reason}",
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                await member.send(embed=dm_embed)
            except discord.Forbidden:
                logger.warning(f"Could not DM user {member.id} about their warning.")

            # 5. Log to mod-log channel
            guild_data = await GuildService.get_guild_setting(guild_id=guild.id)
            if guild_data and guild_data.log_channel and guild_data.log_channel.mod_log_channel_id:
                log_channel = guild.get_channel(guild_data.log_channel.mod_log_channel_id)
                if log_channel:
                    log_embed = discord.Embed(
                        title="Member Warned",
                        color=discord.Color.gold(),
                        timestamp=discord.utils.utcnow()
                    )
                    log_embed.set_thumbnail(url=member.display_avatar.url)
                    log_embed.add_field(name="Target", value=f"{member.mention} ({member.id})", inline=False)
                    log_embed.add_field(name="Moderator", value=f"{interaction.user.mention} ({interaction.user.id})",
                                        inline=False)
                    log_embed.add_field(name="Reason", value=reason, inline=False)
                    log_embed.add_field(name="History", value=f"Warning #{offense_count + 1}", inline=False)
                    await log_channel.send(embed=log_embed)

            # 6. Automatic Punishment Logic (e.g., Mute on 3rd warn)
            if offense_count is not None and offense_count >= 2:  # Already has 2, this is 3rd
                mute_reason = f"Automatic mute: reached 3 warnings. Latest warn: {reason}"

                # Perform mute
                await self.mute(interaction=interaction, member=member, reason=mute_reason)

                # Resolve the warnings in DB
                await ModerationService.resolve_offense_logs(
                    guild_id=guild.id,
                    offender_id=member.id,
                    action_type="Warn"
                )

                # Send additional follow-up for the threshold reached
                threshold_embed = discord.Embed(
                    description=f"🛡️ {member.mention} has been automatically muted for reaching the **3-warning threshold**.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=threshold_embed)

        except Exception as e:
            logger.error(f"Failed to warn: {e}")
            await interaction.followup.send(f"An error occurred while processing the warning: {e}", ephemeral=True)

    @app_commands.command(name="warnings", description="Shows warnings for a user")
    @app_commands.guild_only()
    @app_commands.describe()
    async def warnings(
            self,
            interaction: discord.Interaction,
            member: discord.Member = None,
    ):
        """Get all warnings for a user"""
        await interaction.response.defer()
        try:
            if member is None:
                member = interaction.user

            logs = await ModerationService.get_offense_logs(
                guild_id=interaction.guild.id,
                offender_id= member.id
            )

            embed = await warning_embed(
                guild=interaction.guild,
                warning_logs= logs,
                offender= member
            )
            view = DeleteWarningsLogsUi(offender=member, logs= logs)
            await interaction.followup.send(view =view, embed= embed)
        except Exception as e:
            logger.error(f"Failed to get warnings: {e}")
            await interaction.followup.send(f"An error occurred while processing the warnings: {e}", ephemeral=True)



async def setup(bot):
    await bot.add_cog(ModerationCommandsCog(bot))
