import logging
import os

import discord
from dotenv import load_dotenv

from bot import token
from bot.config import Bot

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    force='%(asctime)s %(levelname)s:%(name)s: %(message)s'
)



if __name__ == "__main__":
    TEST_TOKEN = os.getenv("TEST_DISCORD_TOKEN")
    PRODUCTION_TOKEN = os.getenv("PRODUCTION_DISCORD_TOKEN")

    if token == TEST_TOKEN:
        prefix = "nt!"
    elif token == PRODUCTION_TOKEN:
        prefix = "n!"
    else:
        prefix = "n!"


    bot = Bot(command_prefix=prefix, intents=discord.Intents.all(),  help_command= None )
    bot.run(token=token)