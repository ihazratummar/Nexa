import logging

import discord
import os
from dotenv import load_dotenv
from bot.config import Bot
from bot import token
from multiprocessing import Process
from dashboard.main import run_dashboard


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

    # Run the dashboard in a separate process
    dashboard_process = Process(target=run_dashboard)
    dashboard_process.start()

    bot = Bot(command_prefix=prefix, intents=discord.Intents.all(),  help_command= None )
    bot.run(token=token)