import random
import discord
import requests
from config import Bot
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import os
from .Buttons.social_links import SocialLinks

load_dotenv()

WEATHER_API = os.getenv("WEATHER_API")


class General(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.hybrid_command()
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id))
    async def hi(self, interaction: commands.Context):
        await interaction.send(f"Hi how are you")

    @commands.hybrid_command(
        name="whatsapp", description="whatsapp  group daily stream notification"
    )
    async def whatsapp(self, interaction: commands.Context):
        await interaction.send(
            f"Join Whatsapp Group for stream notification : https://bit.ly/3zBxoCf"
        )

    @commands.hybrid_command(name="support")
    async def support(self, interaction: commands.Context):
        await interaction.send(
            f"You can support us by becoming a facebook page member.\nBecome a supporter:-  https://bit.ly/3xJdNzZ"
        )

    @commands.hybrid_command(name="social")
    async def social(self, interaction: commands.hybrid_command):
        embed = discord.Embed(
            title= "Social Links",
            description= "Check Click and Visit Our Official Links for More info!",
            colour= discord.Colour.brand_green()
        )
        embed.set_thumbnail(url="https://media.tenor.com/-Nc9wGWx3X8AAAAi/pepe-fastest-pepe-the-frog.gif")
        embed.set_image(url="https://media1.tenor.com/m/WmU_8UAyg_8AAAAC/night.gif")
        embed.add_field(name="<:discord:1243197853371859017> Discord", value="[Discord](https://discord.gg/DhsEvqHyE9)")
        embed.add_field(name="<:facebook:1243197848498077716> Facebook", value="[Facebook](https://www.facebook.com/crazyforsurprise)")
        embed.add_field(name="<:youtube:1243197856014139485> YouTube", value="[YouTube](https://www.youtube.com/crazyforsurprise)")
        embed.add_field(name="<:instagram:1243197850880446464> Instagram", value="[Instagram](https://www.instagram.com/ummaroyin/)")

        await interaction.send(
            embed= embed, view=SocialLinks()  
        )
    @commands.hybrid_command(name="youtube", description="search video")
    async def youtube(self, interaction: commands.Context, search: str):
        response = requests.get(f"https://youtube.com/results?search_query={search}")
        html = response.text
        index = html.find("/watch?v=")
        url = "https://www.youtube.com" + html[index : index + 20]
        await interaction.send(url)


async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
