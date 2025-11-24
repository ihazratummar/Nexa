import requests
from discord import app_commands
from discord.ext import commands

from bot.config import Bot


class General(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.hybrid_command()
    @app_commands.checks.cooldown(1, 10, key=lambda i: i.user.id)
    async def hi(self, interaction: commands.Context):
        await interaction.send(f"Hi how are you")


    @commands.hybrid_command(name="youtube", description="search video")
    async def youtube(self, interaction: commands.Context, search: str):
        response = requests.get(f"https://youtube.com/results?search_query={search}")
        html = response.text
        index = html.find("/watch?v=")
        url = "https://www.youtube.com" + html[index : index + 20]
        await interaction.send(url)


async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
