from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorCollection

from core.checks import moderation_enabled_predicate, hierarchy_check
from core.database import Database
from core.embed.embed_builder import embed_builder
from core.utils.time_parse import parse_duration
from modules.Automod.services import AutoModServices
from modules.error.custom_errors import GenericError
from modules.moderation.services import ModerationService


class ModerationCommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.collection:AsyncIOMotorCollection = AutoModServices.get_guild_settings_collection()
        self.mod_settings_collection:AsyncIOMotorCollection = Database.moderation_settings()

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
                timestamp= discord.utils.utcnow(),
            )
            embed.add_field(name="Reason", value=reason_text, inline=False)
            embed.add_field(name="Moderator", value= interaction.user.mention, inline=False)
            icon_url = interaction.guild.icon.url if interaction.guild.icon else None
            embed.set_footer(text=interaction.guild.name, icon_url=icon_url)
            await member.send(embed=embed)
            dm_sent = True
        except discord.Forbidden:
            dm_sent = False

        try:
            await member.kick(reason= f"[{interaction.user}] {reason_text}")
        except discord.Forbidden:
            await interaction.followup.send(f"Failed to kick the user due to lack of permissions", ephemeral=True)
            return
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")

        await interaction.followup.send(f"{member.mention} has been kicked from this server.")

        await ModerationService.send_logs(
            guild=interaction.guild,
            action="Kick",
            moderator=interaction.user,
            target=member,
            reason=reason_text
        )

    @app_commands.command(name="timeout", description="Timeout a user")
    @app_commands.default_permissions(mute_members=True)
    @app_commands.guild_only()
    @app_commands.check(moderation_enabled_predicate)
    @hierarchy_check(action="timeout")
    @app_commands.describe(
        duration="Duration of the timeout.(Example: 10s for 10 seconds and m,h,w (minutes, hours, weeks) etc.)",
        member= "Mention a server member",
        reason= "Reason for timeout",
    )
    async def timeout(self, interaction: discord.Interaction, duration: str, member: discord.Member, reason: str = None):
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

        await ModerationService.send_logs(
            guild=interaction.guild,
            action="Timeout",
            moderator=interaction.user,
            target=member,
            reason=reason_text
        )

    @app_commands.command(name="remove_timeout", description="Remove a user timed out")
    @app_commands.default_permissions(mute_members=True)
    @app_commands.guild_only()
    @app_commands.check(moderation_enabled_predicate)
    @hierarchy_check(action="remove_timeout")
    @app_commands.describe(
        member= "Mention a server member",
        reason= "Reason for remove_timeout",
    )
    async def remove_timeout(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        await interaction.response.defer()
        try:
            reason_text = reason or "No reason provided."
            await member.timeout(None,reason= reason_text)
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



async def setup(bot):
    await bot.add_cog(ModerationCommandsCog(bot))
