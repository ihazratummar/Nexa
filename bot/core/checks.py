from discord.ext import commands

from bot.core.constant import DbCons
from bot.core.context import CustomContext

def guard(command_name: str):
    async def predicate(ctx: CustomContext):
        # Access the bot instance from the context
        bot = ctx.bot
        
        # Ensure the bot has the get_command_config method
        if not hasattr(bot, 'get_command_config'):
            return True

        config = await bot.get_command_config(guild_id=str(ctx.guild.id), command_name=command_name)
        if config:
            # Attach config to context for later use (auto-delete)
            ctx.command_config = config
            
            # 1. Check Global Enable
            if not config.enabled:
                return False
            
            # 2. Check Disabled Roles
            if config.disabled_roles:
                user_role_ids = [str(r.id) for r in ctx.author.roles]
                if any(rid in config.disabled_roles for rid in user_role_ids):
                    return False

            # 3. Check Enabled Roles (Whitelist mode)
            if config.enabled_roles:
                user_role_ids = [str(r.id) for r in ctx.author.roles]
                if not any(rid in config.enabled_roles for rid in user_role_ids):
                    return False
            
            # 4. Check Disabled Channels
            if str(ctx.channel.id) in config.disabled_channels:
                return False

            # 5. Check Enabled Channels (Whitelist mode)
            if config.enabled_channels:
                if str(ctx.channel.id) not in config.enabled_channels:
                    return False

        return True
    return commands.check(predicate)

def premium_only():
    async def predicate(ctx: CustomContext):
        # Access the bot instance from the context
        bot = ctx.bot
        
        # Ensure the bot has the db connection
        if not hasattr(bot, 'db'):
            return False

        guild_settings_collection = bot.db[DbCons.GUILD_SETTINGS_COLLECTION.value]
        
        # Check cache first if possible (TODO: Add caching for guild settings)
        # For now, direct DB query
        guild_data = await guild_settings_collection.find_one({"guild_id": str(ctx.guild.id)})
        
        if guild_data and guild_data.get("is_premium", False):
            return True
            
        await ctx.send("💎 This command is restricted to **Premium** servers only.")
        return False
    return commands.check(predicate)
