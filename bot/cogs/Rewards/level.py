from builtins import int
import discord
from discord.ext import commands
from bot.config import Bot
from discord import app_commands , File
from easy_pil import Canvas, Editor, font , load_image_async
from PIL import Image


class Level(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = bot.database
        self.collection = self.db['level']

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot and not message.content.startswith(self.bot.command_prefix):
            user_id = str(message.author.id)
            collection = self.db[f"{message.guild.name}({message.guild.id})"]
            # Use upsert to insert or update the document
            collection.update_one(
                {"_id": user_id,},
                {"$inc": {"xp": 5}, "$setOnInsert": {"level": 0, "name": message.author.name}},
                upsert=True
            )

            user_data = collection.find_one({"_id": user_id})
            if user_data:
                xp = user_data.get("xp", 0)
                level = user_data.get("level", 0)
                new_level = self.calculate_level(xp= xp, current_level=level)
                if new_level > user_data.get("level", 0):
                    collection.update_one(
                        {"_id": user_id},
                        {"$set": {"level": new_level}}
                    )
                    await message.channel.send(
                            f"{message.author.mention}, you have reached level {new_level} "
                        )


    def calculate_level(self, xp, current_level):
        # Define XP thresholds for each level
        level_thresholds = [
            (50, 1),
            (350, 5),
            (1000, 10),
            (1500, 15),
            (2000, 20),
            (2500, 25),
            (3000, 30),
            (3500, 35),
            (4000, 40),
        ]

        # Determine the user's level based on their XP
        for threshold, level in level_thresholds:
            if xp >= threshold and current_level < level:
                return level
        return current_level

    def get_next_level_xp(self, current_level):
    # Define XP thresholds for each level
        level_thresholds = [
            (50, 1),
            (350, 5),
            (1000, 10),
            (1500, 15),
            (2000, 20),
            (2500, 25),
            (3000, 30),
            (3500, 35),
            (4000, 40),
        ]
        
        # Find the XP required for the next level based on the current level
        for threshold, level in level_thresholds:
            if level > current_level:
                return threshold
        return level_thresholds[-1][0]  # If max level reached, return max threshold

    @commands.hybrid_command("rank")
    async def rank(self, interaction: commands.context):
        """Check your current XP"""
        user_id = str(interaction.author.id)
        collection = self.db[f"{interaction.guild.name}({interaction.guild.id})"]
        user_data = collection.find_one({"_id": user_id})

        if user_data:
            xp = user_data.get("xp", 0)

            level = user_data.get("level", 0)
            next_level_xp = self.get_next_level_xp(level)
            previous_level_xp = self.get_next_level_xp(level - 1) if level > 0 else 0
            progress = ((xp - previous_level_xp) / (next_level_xp - previous_level_xp)) * 100

            background = Image.open("Bot/cogs/Rewards/assests/galaxy.jpg")

            image = Editor(background).resize((740, 260))
            user_name_font = font.Font.poppins(variant = 'bold', size = 30)
            xp_text_font = font.Font.poppins(variant = 'bold', size = 20)
            profile_image = await load_image_async(str(interaction.author.avatar._url))
            profile_image = Editor(profile_image).resize((120,120)).rounded_corners(radius=20)

            profile_picture_background = Canvas((150, image.image.size[1]), color=(0, 66, 108, 255))
            background_shade = Editor(Canvas((600, image.image.size[1] -20)))
            background_shade.rectangle(position=(0,0), width=600, height= background_shade.image.size[1],  color=(0, 0, 0, 100),  stroke_width=2, radius= 10)

            background_shade_height = background_shade.image.size[1]
            image_height = image.image.size[1]
            shade_top_position = (image_height - background_shade_height) //2

            image.paste(background_shade, (profile_picture_background.size[0] + 40 , shade_top_position))

            # Calculate the center position for the profile picture
            profile_picture_background_height = profile_picture_background.image.size[1]
            profile_picture_height = profile_image.image.size[1]

            # Calculate the center horizontal position for profile picture
            profile_picture_background_width = profile_picture_background.image.size[0]
            profile_picture_width = profile_image.image.size[0]

            # Calculate the top and horizontal position for centering the profile picture
            top_position = (profile_picture_background_height - profile_picture_height) // 2
            left_position = (profile_picture_background_width - profile_picture_width) //2

            

            # Create an instance of the Editor class for the progress bar
            progress_bar = Editor(Canvas((image.image.size[0], image.image.size[1])))  # Create a canvas for the progress bar
            progress_bar.rectangle(position=(0, 0), width=500, height=25,  color=(255, 255, 255, 150),  stroke_width=2, radius= 10)
            progress_bar.bar(position=(0,0), max_width=500, height=25, percentage=progress, fill= (255, 255, 255), color= (118, 247, 251) ,radius=10)

            #text
            image.text(position=(220, 120), text=f"{interaction.author.name}", font= user_name_font ,color="white")
            #xp tex
            image.text(position=(600, 135), text=f"{xp} / {next_level_xp} XP", font=xp_text_font, color= 'white')


            
            # Paste the profile picture background onto the main image
            image.paste(profile_picture_background.image, (30, 0))

            # Paste the profile picture onto the profile picture background at the calculated position
            image.paste(profile_image, (30 + left_position, top_position))  # Use the image as a mask if needed

            image.paste(progress_bar.image, (220, 160))


            file  = File(fp= image.image_bytes, filename='rankcad.png')
        else:
            embed = discord.Embed(
                title=" ",
                description="You don't have any XP yet. Start chatting to earn XP!",
                color=discord.Color.blurple(),
            )
            await interaction.send(embed=embed)
        
        await interaction.send(file=file)

    @commands.hybrid_command("level")
    async def level(self, interaction: commands.context):
        """Check your current level"""
        user_id = str(interaction.author.id)
        collection = self.db[f"{interaction.guild.name}({interaction.guild.id})"]
        user_data = collection.find_one({"_id": user_id})
        
        if user_data:
            level = user_data.get("level", 0)
            embed = discord.Embed(
                title=" ",
                description=f"Your current level is <:blurple:1109870387614990367> {level} level.",
                color=discord.Color.blurple(),
            )
        else:
            embed = discord.Embed(
                title=" ",
                description="You don't have a level yet. Start chatting to earn XP!",
                color=discord.Color.blurple(),
            )
        
        await interaction.send(embed=embed)

    @commands.hybrid_command("resetxp")
    async def resetxp(self, interaction: commands.context):
        """Reset your XP"""
        user_id = str(interaction.author.id)
        collection = self.db[f"{interaction.guild.name}({interaction.guild.id})"]
        collection.update_one({"_id": user_id}, {"$set": {"xp": 0, "level": 0}})
        
        await interaction.send(
            "Your XP has been reset.", ephemeral=True
        )

    @commands.hybrid_command("delete_account")
    async def delete_account(self, ctx: commands.context):
        user_id = str(ctx.author.id)
        filter_account = {"_id": user_id}
        collection = self.db[f"{ctx.guild.name}({ctx.guild.id})"]
        result = collection.delete_one(filter_account)
        if result.deleted_count >0 :
            await ctx.send(f"User with name {ctx.author.name} deleted successfully.", ephemeral =True)
        else:
            await ctx.send(f"No user found with ID {ctx.author.name}.", ephemeral=True)
    


    @commands.hybrid_command("add_xp")
    @commands.has_permissions(manage_messages = True)
    async def add_xp(self, ctx: commands.Context, *, xp: int, member: discord.Member = None):
        if member is None:
            member = ctx.author

        user_id = str(member.id)
        collection = self.db[f"{ctx.guild.name}({ctx.guild.id})"]
        user_data = collection.find_one({"_id": user_id})
        if user_data:
            new_level = user_data.get("level", 0)
            collection.update_one(
                {"_id": user_id},
                {"$inc": {"xp": xp}},
                upsert=True
            )
        else:
            collection.update_one(
                {"_id": user_id,},
                {"$inc": {"xp": xp}, "$setOnInsert": {"level": 0, "name": member.name}},
                upsert=True
            )
        
        if user_data:
            if new_level > user_data.get("level", 0):
                collection.update_one(
                    {"_id": user_id},
                    {"$set": {"level": new_level}}
                )
                await ctx.send(
                    f"{member.mention}, you have reached level {new_level} "
                )

        await ctx.send(f"Added {xp} XP to {member.mention}.")

        

async def setup(bot: commands.Bot):
    await bot.add_cog(Level(bot))