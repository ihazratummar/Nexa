import logging
from discord.ext import commands
from bot.core.constant import DbCons
from bot.core.models.guild_models import CommandConfig

async def register_commands(bot: commands.Bot):
    """
    Iterates through all registered commands and ensures they exist in the database
    for every guild the bot is in.
    """
    logging.info("Starting command registration...")
    
    # We need to do this for every guild because settings are per-guild
    # Note: For very large bots (10k+ guilds), you wouldn't do this on startup.
    # You would do it lazily (when a user opens the dashboard) or via a separate worker.
    # But for now, this ensures consistency.
    
    commands_list = [c for c in bot.walk_commands()]
    
    # Prepare a list of command objects
    
    async for guild in bot.fetch_guilds():
        for cmd in commands_list:
            cmd_name = cmd.qualified_name
            category = cmd.cog_name if cmd.cog_name else "General"
            
            # Use update_one with upsert=True
            # This prevents duplicates AND updates the category if it's missing/changed
            await bot.command_settings.update_one(
                {"guild_id": str(guild.id), "command": cmd_name},
                {
                    "$set": {"category": category},
                    "$setOnInsert": {
                        "guild_id": str(guild.id),
                        "command": cmd_name,
                        "enabled": True,
                        "settings": {},
                        "enabled_roles": [],
                        "disabled_roles": [],
                        "enabled_channels": [],
                        "disabled_channels": []
                    }
                },
                upsert=True
            )

    logging.info("Command registration complete.")
