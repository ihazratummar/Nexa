import logging

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ext import commands

from bot import mongo_client
from bot.core.constant import DbCons

exts = [
    "bot.cogs.error",
    "bot.cogs.general",
    "bot.cogs.fun_commands",
    "bot.cogs.media_commands",
    "bot.cogs.games",
    "bot.cogs.welcome",
    # "bot.cogs.Rewards.level",
    # "bot.cogs.Rewards.economy",
    "bot.cogs.Automod",
    "bot.cogs.Utility.utility_commands",
    "bot.cogs.logs",
    "bot.cogs.embed_builder"
]

#new change

class Bot(commands.AutoShardedBot):
    def __init__(self, command_prefix: str, intents: discord.Intents,  **kwargs):
        super().__init__(command_prefix, intents=intents, **kwargs)
        self.mongo_client = mongo_client
        self.db = self.mongo_client[DbCons.DATABASE_NAME.value]
        self.scheduler = AsyncIOScheduler()

    async def on_ready(self):
        for ext in exts:
            try:
                await self.load_extension(ext)
            except Exception as e:
                logging.error(f"Error loading extension {ext}: {e}")

        synced = await self.tree.sync()
        logging.info(f"Loaded {len(exts)} and {len(synced)} commands(s)")
        logging.info("Bot is ready.")

        self.scheduler.start()


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
        
        cogs = [
        ("AutoMod", "auto_mod"),
        ("Level", "level_up"),
        ("Utility", "last_seen"),
    ]
        for cog_name, method_name in cogs:
            cog = self.get_cog(cog_name)
            if cog:
                method = getattr(cog, method_name, None)
                if method:
                    await method(message)
                else:
                    print(f"Error: {method_name} method not found in {cog_name} cog.")
            else:
                print(f"Error: {cog_name} cog is not available.")

        await self.process_commands(message)

    async def on_member_update(self, before: discord.Member, after: discord.Member):
        cogs = [
            ("Logs", "logs_member_update"),
            ("Boosts", "welcome_member_update"),
        ]

        for cog_name, method_name in cogs:
            cog = self.get_cog(cog_name)
            if cog:
                method = getattr(cog, method_name, None)
                if method:
                    await method(before, after)
                else:
                    print(f"Error: {method_name} method not found in {cog_name} cog.")
            else:
                print(f"Error: {cog_name} cog is not available.")

