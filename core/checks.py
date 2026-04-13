import discord
from discord.ext import commands
from discord import app_commands

from core.config import settings
from core.database import Database
from modules.error.custom_errors import ModerationDisabled, HierarchyError
from modules.moderation.services import ModerationService


def premium_only():
    async def predicate(ctx: commands.Context):
        # Access the bot instance from the context
        guild_settings_collection = Database.guild_settings()
        users_collection = Database.user()
        
        guild_id = ctx.guild.id
        
        # 1. Check Guild Settings (Direct Premium)
        guild_data = await guild_settings_collection.find_one({"guild_id": guild_id})
        if guild_data and guild_data.get("is_premium", False):
            return True
            
        # 2. Check User Assignments (User assigned premium to this guild)
        # Find ANY user who has premium_guild_id set to this guild
        user_premium = await users_collection.find_one({"premium_guild_id": guild_id})
        if user_premium:
            return True
            
        await ctx.send("💎 This command is restricted to **Premium** servers only.")
        return False
    return commands.check(predicate)


async def moderation_enabled_predicate(ctx_or_interaction: discord.Interaction | commands.Context) -> bool:
    if isinstance(ctx_or_interaction, discord.Interaction):
        guild_id = ctx_or_interaction.guild_id
    else:
        guild_id = ctx_or_interaction.guild.id
        
    moderation_settings = await ModerationService.get_mod_settings(guild_id=guild_id)
    if not moderation_settings or not moderation_settings.is_moderation_settings_enabled:
        raise ModerationDisabled()
    return True

def hierarchy_check(action: str = "moderate"):
    async def predicate(interaction: discord.Interaction):
        member: discord.Member = interaction.namespace.member

        # Safety check (in case missing)
        if not member:
            raise HierarchyError("Please provide a valid member")
        if member == interaction.guild.owner:
            raise HierarchyError(f"I wont tell the owner, but do not try to {action} the owner again.. 🫣")
        if member.top_role >= interaction.user.top_role:
            raise HierarchyError(f"You can not {action} someone with an equal or higher role than yours.")
        if member.top_role >= interaction.guild.me.top_role:
            raise HierarchyError(f"I can not {action} someone with an equal or higher role than mine.")
        return True
    return app_commands.check(predicate)



def moderation_enabled():
    return commands.check(moderation_enabled_predicate)

