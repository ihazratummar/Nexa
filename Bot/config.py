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