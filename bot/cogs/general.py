import asyncio
import os
import re
import discord
import requests
from bot.config import Bot
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from ..core.Buttons.buttons import  LinksButton

load_dotenv()

WEATHER_API = os.getenv("WEATHER_API")


class General(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.hybrid_command()
    @app_commands.checks.cooldown(1, 10, key=lambda i: i.user.id)
    async def hi(self, interaction: commands.Context):
        await interaction.send(f"Hi how are you")




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
        embed.add_field(name="<:instagram:1243197850880446464> Instagram", value="[Instagram](https://www.instagram.com/ihazratummar)")

        button_list = [
            ("Discord", "https://discord.gg/g3M4MWK", "<:discord:1243197853371859017>"),
            ("Facebook", "https://www.facebook.com/crazyforsurprise", "<:facebook:1243197848498077716>"),
            ("YouTube", "https://www.youtube.com/crazyforsurprise", "<:youtube:1243197856014139485>"),
            ("Instagram", "https://www.instagram.com/ihazratummar", "<:instagram:1243197850880446464>")

        ]

        await interaction.send(
            embed= embed, view = LinksButton(buttons_list= button_list)
        )
    @commands.hybrid_command(name="youtube", description="search video")
    async def youtube(self, interaction: commands.Context, search: str):
        response = requests.get(f"https://youtube.com/results?search_query={search}")
        html = response.text
        index = html.find("/watch?v=")
        url = "https://www.youtube.com" + html[index : index + 20]
        await interaction.send(url)


    def generate_ai_response(self, prompt: str):
        """Calls ollama Api to generate a love note."""
        url = "http://localhost:11434/api/generate"

        payload = {
            "model" : "deepseek-r1:8b",
            "prompt": prompt,
            "stream": False
        }

        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get("response", "").strip()
                ai_response = re.sub(r"<think>.*?</think>", "", ai_response, flags=re.DOTALL).strip()
                return ai_response[:2000]  if ai_response else "Oops! No love note generated. Try again! 💖"
            else:
                return "Error generating a love message, but you know I love you! 💖"
        except Exception as e:
            return f"Error: {str(e)}"

    @commands.hybrid_command("ai")
    async def ai(self, ctx: commands.Context, *,  message: str):
        await ctx.defer()
        love_message = self.generate_ai_response(prompt=message)
        await ctx.send(love_message)

async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
