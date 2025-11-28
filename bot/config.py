import logging
import os

import discord
import redis.asyncio as redis
from discord.ext import commands

from bot import mongo_client
from bot.core.constant import DbCons
from bot.core.models.guild_models import CommandConfig
from bot.core.registration import register_commands
from bot.core.context import CustomContext

exts = [
    "bot.cogs.error",
    "bot.cogs.general",
    "bot.cogs.fun_commands",
    "bot.cogs.media_commands",
    "bot.cogs.games",
    "bot.cogs.welcome",
    "bot.cogs.Automod",
    "bot.cogs.moderation",
    "bot.cogs.Utility.utility_commands",
    "bot.cogs.logs",
    "bot.cogs.embed_builder"
]




class Bot(commands.AutoShardedBot):
    def __init__(self, command_prefix: str, intents: discord.Intents,  **kwargs):
        super().__init__(command_prefix, intents=intents, **kwargs)
        self.mongo_client = mongo_client
        self.db = self.mongo_client[DbCons.DATABASE_NAME.value]
        if not self.scheduler.running:
            self.scheduler.start()
        self.command_settings = self.db[DbCons.COMMAND_SETTINGS.value]
        # Redis Connection
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis = redis.from_url(redis_url, decode_responses=True)

    async def get_context(self, message, *, cls=CustomContext):
        return await super().get_context(message, cls=cls)

    async def on_ready(self):
        for ext in exts:
            try:
                await self.load_extension(ext)
            except Exception as e:
                logging.error(f"Error loading extension {ext}: {e}")

        synced = await self.tree.sync()
        logging.info(f"Loaded {len(exts)} and {len(synced)} commands(s)")
        
        
        logging.info("Bot is ready.")

        await self.change_presence(
            activity=discord.Game(name="Moderating Code Circle")
        )

    # Debugging: Check if the AutoMod cog is successfully loaded
        if "AutoMod" in self.cogs:
            logging.info("AutoMod cog is loaded successfully.")
        else:
            logging.error("Failed to load AutoMod cog.")

    async def on_message(self, message):
        if message.author.bot:
            return
        
        await self.process_commands(message)

    async def on_command_completion(self, ctx: CustomContext):
        if hasattr(ctx, 'entry_point_cleanup'):
            await ctx.entry_point_cleanup()

    async def on_member_update(self, before: discord.Member, after: discord.Member):
        pass

    async def on_guild_join(self, guild: discord.Guild):
        logging.info(f"Joined new guild: {guild.name} ({guild.id}). Registering commands...")

        # We need to modify register_commands to accept a specific guild, or just run it.
        # For simplicity, we can run the existing function which iterates all guilds, 
        # but it's better to optimize it.
        # Let's just run the global one for now as it handles "exists" checks efficiently.
        self.loop.create_task(register_commands(self))

    async def get_command_config(self, guild_id: str, command_name: str) -> CommandConfig:
        cache_key = f"command_config:{guild_id}:{command_name}"
        
        # Check Redis Cache
        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                # Need to handle potential JSON errors or stale data
                return CommandConfig.model_validate_json(cached_data)
        except Exception as e:
            logging.error(f"Redis read error: {e}")

        # Fetch from DB
        record = await self.command_settings.find_one(
            {"guild_id": guild_id, "command": command_name}
        )
        
        if record:
            config = CommandConfig(**record)
        else:
            # Lazy Load: Create default config if missing
            # Find the command object to get the category
            cmd = self.get_command(command_name)
            category = cmd.cog_name if cmd and cmd.cog_name else "General"
            
            config = CommandConfig(
                guild_id=guild_id,
                command=command_name,
                description=cmd.description,
                category=category,
                enabled=True
            )
            # Insert into DB
            try:
                await self.command_settings.insert_one(config.model_dump())
            except Exception as e:
                # Handle race condition where another thread/process inserted it first
                if "E11000" in str(e):
                    # Fetch the record that was just inserted
                    record = await self.command_settings.find_one(
                        {"guild_id": guild_id, "command": command_name}
                    )
                    if record:
                        config = CommandConfig(**record)
                else:
                    logging.error(f"Error inserting command config: {e}")
            
        # Cache for 5 seconds: Feels instant to user, but protects DB from command spam
        try:
            await self.redis.set(cache_key, config.model_dump_json(), ex=5)
        except Exception as e:
            logging.error(f"Redis write error: {e}")
            
        return config


