import discord
from discord.ext import commands
from discord import app_commands
from config import Bot
import requests
import random
import json
import os
from dotenv import load_dotenv
import aiohttp
import tempfile

load_dotenv()



class Media_Commands(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @app_commands.command(name="imgur", description="search for images")
    async def imgur(self, interaction: discord.Interaction, *, query: str):
        headers = {"Authorization": "Client-ID 20c2904655c6a1f"}
        params = {"q": query}
        response = requests.get(
            "https://api.imgur.com/3/gallery/search/", headers=headers, params=params
        )

        if response.status_code == 200:
            data = json.loads(response.content.decode("utf-8"))
            images = [
                item for item in data["data"] if "images" in item and item["images"]
            ]

            if images:
                random_image = random.choice(images)
                image_url = random.choice(random_image["images"])["link"]

                embed = discord.Embed(
                    title=f'Results for **{query}**', color= 0x00FFFF
                )
                embed.set_image(url=image_url)
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(
                    f'Sorry, no images found for "{query}"'
                )
        else:
            await interaction.response.send_message(
                "Sorry, there was an error processing your request. Please try again later."
            )

    @app_commands.command(name= "images_search", description="search a images")
    async def image_search(self, interaction : discord.Interaction, topic:str):
        key = os.getenv("PIXABAY_API")
        response = requests.get(f"https://pixabay.com/api/?key={key}&q={topic}")

        data = response.json()

        images = [item for item in data["hits"] if "previewURL" in item]
        if not images:
            await interaction.response.send_message("No Images Found.")
            return
        # preview_url = [item["previewURL"] for item in images]

        random_images = random.choice(images)

        embed = discord.Embed(
            title=f"Your search result for {topic}",
            description= "",
            color= 0x00FFFF
        )
        embed.add_field(name="Likes", value=random_images["likes"])
        embed.add_field(name="Downloads", value=random_images["downloads"])
        embed.add_field(name="Views", value=random_images["views"])
        embed.set_image(url= random_images["largeImageURL"])
        embed.set_author(name=random_images["user"], icon_url=random_images["userImageURL"])

        button1 = discord.ui.Button(
            label="Open Image", 
            url=random_images["pageURL"],
            style= discord.ButtonStyle.link
        )
        view = discord.ui.View()
        view.add_item(button1)

        await interaction.response.send_message(embed= embed, view= view)

    @app_commands.command(name="search_video", description="Search a video")
    async def search_video(self,interaction: discord.Interaction, topic: str):
        key = os.getenv("PIXABAY_API")
        if not key:
            await interaction.response.send_message("API key not found.")
            return

        # Defer the response to give more time for processing
        await interaction.response.defer()

        response = requests.get(f"https://pixabay.com/api/videos/?key={key}&q={topic}")
        if response.status_code != 200:
            await interaction.followup.send("Failed to fetch data from Pixabay.")
            return

        data = response.json()

        # Debugging: Print the response data to check its structure
        # print(data)

        video = [item for item in data["hits"] if "videos" in item]
        if not video:
            await interaction.followup.send("No Video Found.")
            return

        random_video = random.choice(video)
        video_details = random_video["videos"]
        video_url = video_details["small"]["url"]

        try:
            # Download the video
            async with aiohttp.ClientSession() as session:
                async with session.get(video_url) as resp:
                    if resp.status != 200:
                        await interaction.followup.send("Failed to download video.")
                        return
                    
                    video_data = await resp.read()

            # Define the custom directory path
            custom_directory = "Bot/cogs/temp_videos"

            # Ensure the custom directory exists
            os.makedirs(custom_directory, exist_ok=True)

            # Save the video data to a temporary file in the custom directory
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4", dir=custom_directory) as temp_video:
                temp_video.write(video_data)
                temp_video_path = temp_video.name

            # Log the temporary file path for debugging
            # print(f"Temporary video file path: {temp_video_path}")

            file = discord.File(temp_video_path, filename="search_video.mp4")

            embed = discord.Embed(
                title=f"Your search result for {topic}",
                description="Here is the video you searched for!",
                color=0x00FFFF
            )
            embed.add_field(name="Likes", value=random_video["likes"])
            embed.add_field(name="Downloads", value=random_video["downloads"])
            embed.add_field(name="Views", value=random_video["views"])
            embed.set_author(name=random_video["user"], icon_url=random_video["userImageURL"])

            button1 = discord.ui.Button(
            label="Download Video", 
            url=random_video["pageURL"],
            style= discord.ButtonStyle.link
            )
            view = discord.ui.View()
            view.add_item(button1)

            await interaction.followup.send(embed=embed, file=file, view= view)

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")

        finally:
            # Clean up the temporary file
            if 'temp_video_path' in locals() and os.path.exists(temp_video_path):
                os.remove(temp_video_path)


async def setup(bot: commands.Bot):
    await bot.add_cog(Media_Commands(bot))
