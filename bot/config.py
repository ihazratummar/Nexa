import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from pymongo import MongoClient


# endregion

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

mongo_uri = os.getenv("MONGO_CONNECTION")
mongo_client = MongoClient(mongo_uri)
database = mongo_client["Level_Database"]

exts = [
    "bot.cogs.error",
    "bot.cogs.general",
    "bot.cogs.fun_commands",
    "bot.cogs.media_commands",
    "bot.cogs.games",
    "bot.cogs.welcomer",
    "bot.cogs.Rewards.level",
    "bot.cogs.Rewards.economy",
    "bot.cogs.Automod.automod",
    "bot.cogs.Utility.utility_commands",
    "bot.cogs.notification",
    "bot.cogs.logs"
]


class Bot(commands.Bot):
    def __init__(self, command_prefix: str, intents: discord.Intents, database,  **kwargs):
        super().__init__(command_prefix, intents=intents, **kwargs)
        self.mongo_client = mongo_client
        self.database = database

    async def on_ready(self):
        for ext in exts:
            if ext not in self.extensions:
                await self.load_extension(ext)
        print("loaded all cogs")


        synced = await self.tree.sync()
        print(f"Synced {len(synced)} commands(s)")
        print("Bot is ready.")

        await self.change_presence(
            activity=discord.Game(name="Moderating Code Circle")
        )
