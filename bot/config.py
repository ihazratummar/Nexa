import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from pymongo import MongoClient
from bot import mongo_client


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

#new change

class Bot(commands.Bot):
    def __init__(self, command_prefix: str, intents: discord.Intents,  **kwargs):
        super().__init__(command_prefix, intents=intents, **kwargs)
        self.mongo_client = mongo_client

    async def on_ready(self):
        for ext in exts:
            try:
                await self.load_extension(ext)
            except Exception as e:
                print(f"Error loading extension {ext}: {e}")

        print("Loaded all cogs")


        synced = await self.tree.sync()
        print(f"Synced {len(synced)} commands(s)")
        print("Bot is ready.")

        await self.change_presence(
            activity=discord.Game(name="Moderating Code Circle")
        )

    # Debugging: Check if the AutoMod cog is successfully loaded
        if "AutoMod" in self.cogs:
            print("AutoMod cog is loaded successfully.")
        else:
            print("Failed to load AutoMod cog.")

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
