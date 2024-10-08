#config.py
# region imports <- This is foldable
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from discord import Activity, ActivityType
import datetime, time
from pymongo import MongoClient


# endregion

load_dotenv()
token = os.getenv("DISCORD_TOKEN")
mongo_username = os.getenv("MONGO_USERNAME")
mongo_password = os.getenv("MONGO_PASSWORD")

uri = f"mongodb+srv://{mongo_username}:{mongo_password}@cluster0.7aptm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
mongo_client = MongoClient(uri)
database = mongo_client["Level_Database"]

exts = [
    "cogs.error",
    "cogs.general",
    "cogs.fun_commands",
    "cogs.media_commands",
    "cogs.games",
    "cogs.welcomer",
    "cogs.Rewards.level",
    # "cogs.Rewards.economy",
    "cogs.Automod.automod",
    "cogs.Utility.utility_commands",
    "cogs.notification",
    "cogs.logs"
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
            activity=discord.Game(name="Moderating CrazyForSurprise")
        )


if __name__ == "__main__":
    bot = Bot(command_prefix=".", intents=discord.Intents.all(), database=database, help_command = None)
    bot.run(token)