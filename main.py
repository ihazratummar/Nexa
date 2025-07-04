import discord
import os
from dotenv import load_dotenv
from bot.config import Bot
from bot import token

load_dotenv()


if __name__ == "__main__":
    TEST_TOKEN = os.getenv("TEST_DISCORD_TOKEN")
    PRODUCTION_TOKEN = os.getenv("PRODUCTION_DISCORD_TOKEN")

    if token == TEST_TOKEN:
        prefix = "ut!"
    elif token == PRODUCTION_TOKEN:
        prefix = "u!"
    else:
        prefix = "u!"

    bot = Bot(command_prefix=prefix, intents=discord.Intents.all(),  help_command= None )
    bot.run(token=token)