from bot.config import Bot, token, database
import discord

if __name__ == "__main__":
    bot = Bot(command_prefix="u!", intents=discord.Intents.all(), database=database, help_command= None )
    bot.run(token=token)