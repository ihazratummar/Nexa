import discord
from discord.ext import commands
from config import Bot
from dotenv import load_dotenv
import asyncio
import requests
import random
import os

load_dotenv()



class Utility(commands.Cog):
    def __init__(self, bot : Bot):
        self.bot = bot

    @commands.hybrid_command(name="help", description= "Get all the commands list")
    async def help(self, interaction: commands.Context):
        embed = discord.Embed(
            title= "Help",
            description= "List of commands all the commands",
            color= 0x00FFFF
        )

        for c in self.bot.cogs:
             cog = self.bot.get_cog(c)
             if any(cog.walk_commands()):
                 embed.add_field(name=cog.qualified_name, value= " , ".join(f"`{i.name}`" for i in cog.walk_commands()), inline= False)
        await interaction.send(embed=embed)


    @commands.hybrid_command(name="ping", description="server ping")
    async def ping(self, interaction: commands.Context):
        await interaction.send(
            f"Ping {round(self.bot.latency * 1000)} ms"
        )

    @commands.hybrid_command(name="invite", description="Invite Link")
    async def invite(self, interaction: commands.Context):
        link = await interaction.channel.create_invite(max_age=0)
        await interaction.send(link)

    @commands.hybrid_command(name='server', description = "Get the server information")
    async def server_Info(self, ctx: commands.Context):
        embed=discord.Embed(title=f"{ctx.guild.name}", description="Information of this Server", color=0x00FFFF)
        embed.add_field(name="👑Owner", value=f"{ctx.guild.owner}", inline=True)
        embed.add_field(name="👥Total members", value=f"{ctx.guild.member_count}", inline=True)
        embed.add_field(name="🧸Categories", value=f"{len(ctx.guild.categories)}", inline=True)
        embed.add_field(name="🔮Total Text Channels", value=f"{len(ctx.guild.text_channels)}", inline=True)
        embed.add_field(name="🎑Total Voice Channels", value=f"{len(ctx.guild.voice_channels)}", inline=True)
        embed.add_field(name="🎐Total Roles", value=f"{len(ctx.guild.roles)}", inline=True)
        embed.set_thumbnail(url= ctx.guild.icon._url)
        embed.set_footer(text= f"ID: {ctx.guild.id} | Server Created - {ctx.guild.created_at.strftime('%A, %d %B %Y %H:%M')}")

        if ctx.guild.banner:
            embed.set_image(url= ctx.guild.banner.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="userinfo", description= "Display a user's info")
    async def userinfo(self, ctx: commands.Context, * , user: discord.Member = None):
        if user is None:
            user = ctx.author

        full_user = await self.bot.fetch_user(user.id)

            # Format the datetime objects
        account_created = user.created_at.strftime("%A, %d %B %Y %H:%M")
        server_joining_date = user.joined_at.strftime("%A, %d %B %Y %H:%M")
        embed=discord.Embed(title=f"{user.name}", description="", color=0x00FFFF)
        embed.add_field(name="ID", value=f"{user.id}", inline=True)
        embed.add_field(name="Nickname", value=f"{user.nick}", inline=True)
        embed.add_field(name="", value=f"", inline=True)
        embed.add_field(name="Account Created", value= f"> `{account_created}`" ,inline= False)
        embed.add_field(name="Server joining Date", value=f"> `{server_joining_date}`", inline=False)
        embed.set_image
        if len(user.roles) >1:
            role_string = '  '.join([r.mention for r in user.roles][1:])
            embed.add_field(name= "Roles[{}]".format(len(user.roles)-1), value=f"{role_string}", inline= False)
        embed.set_author(name=f"{user.name}", icon_url=f"{user.avatar._url}")
        embed.set_thumbnail(url=f"{user.avatar._url}")

        if full_user.banner:
            embed.set_image(url=full_user.banner.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="avatar", description = "Display a User's Avatar")
    async def avatar(self, ctx: commands.Context, user:discord.Member = None):
        if user is None:
            user = ctx.author
        
        embed=discord.Embed(title=f"{user.name}", description=f"[Avatar URL]({user.avatar.url})", color=0x00FFFF)
        embed.set_image(url=f"{user.avatar._url}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name= "channelinfo")
    async def channelinfo(self, ctx: commands.Context, * ,channel: discord.TextChannel = None):
        if channel is None:
            channel = ctx.channel
        embed=discord.Embed(title=f"Channel Info: {channel.name}",color=0x00FFFF)
        embed.add_field(name=f"Channel Name", value=f"<#{channel.id}>", inline=False)
        embed.add_field(name="Channel Topic", value=f"{channel.topic if channel.topic else 'No Topic Set'}", inline= False),
        embed.add_field(name="Channel Category", value=f"{channel.category.name if channel.category else 'No categoty'}", inline= False)
        embed.add_field(name="Position", value=f"{channel.position}", inline=True)
        embed.add_field(name='NSFW', value=f"{channel.is_nsfw()}", inline=True),
        embed.add_field(name="NEWS", value=f"{channel.is_news()}", inline= True)
        embed.set_footer(text=f"ID: {channel.id} | Created At : {channel.created_at.strftime('%A, %d %B %Y %H:%M')}"),
        embed.set_thumbnail(url=f"{ctx.guild.icon._url}")
        await ctx.send(embed=embed)


    @commands.hybrid_command(name="reminder", case_insensitive=True, aliases=['reminde', 'remindme'])
    async def reminder(self, ctx: commands.Context, time, *, reminder: str = None):

        embed = discord.Embed(title=f"Reminder for {ctx.author.name}", description="", color=0x00FFFF)
        seconds = 0

        if reminder is None:
            embed.add_field(name="Warning", value="Your reminder message is empty!")
            await ctx.send(embed=embed)
            return

        try:
            if time.lower().endswith("d"):
                seconds += int(time[:-1]) * 60 * 60 * 24
                counter = f"{seconds // 60 // 60 // 24} days"
            elif time.lower().endswith("h"):
                seconds += int(time[:-1]) * 60 * 60
                counter = f"{seconds // 60 // 60} hours"
            elif time.lower().endswith("m"):
                seconds += int(time[:-1]) * 60
                counter = f"{seconds // 60} minutes"
            elif time.lower().endswith("s"):
                seconds += int(time[:-1])
                counter = f"{seconds} seconds"
            else:
                embed.add_field(name="Error", value="> **Invalid time format**! Please use `'1d'` for days, `'1h'` for hours, `'1m'` for minutes, or `'1s'` for seconds.")
                await ctx.send(embed=embed, ephemeral=True)
                return

            if seconds == 0:
                embed.add_field(name="Warning", value="Please provide a proper duration.")
            elif seconds < 5:
                embed.add_field(name="Warning", value="Duration is too short. Minimum is 5 seconds.")
            elif seconds > 7776000:  # 90 days
                embed.add_field(name="Warning", value="Duration is too long. Maximum is 90 days.")
            else:
                embed.add_field(name="Reminder Created",value=f"> Alright, I will remind you about {reminder} in {counter}.")
                await ctx.send(embed=embed)
                await asyncio.sleep(seconds)
                reminder_embed = discord.Embed(title=f"Reminder for {ctx.author.name}", color=0x00FFFF)
                reminder_embed.add_field(name="Reminder",value=f"Hi{ctx.author.mention}, you asked me to remind you about {reminder} {counter} ago.")
                await ctx.send( f"{ctx.author.mention}" ,embed=reminder_embed)
                return

        except ValueError:
            embed.add_field(name="Error", value="> **Invalid time format**! Please provide a valid number. Ex:`'1d'`, `'1h'`, `'1m'`, or `'1s'`.")
        
        await ctx.send(embed=embed, ephemeral=True)


    @commands.hybrid_command(name="quota", description="Display quota")
    async def quota(self, interaction: commands.Context):
        responses = requests.get("https://api.quotable.io/random")
        data = responses.json()
        quota = data["content"]
        author = data["author"]
        await interaction.send(f"{author}:\n\n━━━━{quota}")


    @commands.hybrid_command(name="emojis", description="Displays all the emojis in the server.")
    async def emojis(self, ctx: commands.Context):
        emojis = ctx.guild.emojis
        if not emojis:
            await ctx.send("This server has no custom emojis.")
            return

        emoji_list = " ".join(str(emoji) for emoji in emojis)
        embed = discord.Embed(title=f"Emojis in {ctx.guild.name}", description=emoji_list, color=0x00FFFF)
        await ctx.send(embed=embed)


    @commands.hybrid_command(name="clear")
    @commands.has_permissions(manage_messages = True)
    async def clear(self, ctx: commands.Context, number: int = 20):
        deleted = await ctx.channel.purge(limit= number +2)
        await ctx.send(f"Deleted {len(deleted)-2} messages.", delete_after=5, ephemeral= True)


    @commands.hybrid_command(name="urban", description = "Get the definition of a term(word) from Urban Dictionary.")
    async def urbun(self, ctx:commands.Context, *, word:str):
        response = requests.get(f"http://api.urbandictionary.com/v0/define?term={word}")
        data = response.json()

        result = [item for item in data["list"]]
        random_choice = random.choice(result)

        embed = discord.Embed(title=f"{word.capitalize()}", description= None ,color= 0x00FFFF)
        embed.add_field(name="Definition", value=f">>> {random_choice["definition"]}", inline= False)
        embed.add_field(name="Example", value=f"{random_choice["example"]}", inline= False)
        embed.add_field(name=f"🖒 {random_choice["thumbs_up"]}", value="", inline=True)
        embed.add_field(name=f"🖓 {random_choice["thumbs_down"]}", value="", inline=True)
        embed.set_footer(text=f"{random_choice["written_on"]}")
        embed.set_author(name=f"Author: {random_choice["author"]}")

        button = discord.ui.Button(
            label= "Check Out",
            url= random_choice["permalink"],
            style= discord.ButtonStyle.link
        )

        view = discord.ui.View()
        view.add_item(button)

        await ctx.send(embed=embed, view= view)

    @commands.hybrid_command(name="antonym", description="Provides antonyms for the specified word.")
    async def antonym(self, ctx: commands.Context, word: str):
        api_url = f'https://api.api-ninjas.com/v1/thesaurus?word={word}'
        api_key = os.getenv("API_NINJA")

        # Check if API key is available
        if not api_key:
            await ctx.send("API key is not set. Please configure the API key.")
            return

        response = requests.get(api_url, headers={'X-Api-Key': api_key})

        if response.status_code == 200:
            data = response.json()
            antonyms = data.get("antonyms", [])
            if antonyms:
                antonyms_list = ' | '.join(antonyms).capitalize()
                
                embed = discord.Embed(title=f"{word.capitalize()}", description=None, color=0x00FFFF)
                
                # Ensure the antonyms list is split correctly if it exceeds 1024 characters
                max_length = 1024 - 4  # account for the '>>>' formatting
                antonym_chunks = [antonyms_list[i:i+max_length] for i in range(0, len(antonyms_list), max_length)]
                
                for i, chunk in enumerate(antonym_chunks):
                    embed.add_field(name=f"Antonyms (Part {i+1})", value=f">>> {chunk}", inline=False)
                
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"No antonyms found for '{word}'.")
        else:
            await ctx.send(f"Error: {response.status_code}")

    @commands.hybrid_command(name="synonym", description="Provides synonyms for the specified word")
    async def synonym(self, ctx: commands.Context, word: str):
        api_url = f'https://api.api-ninjas.com/v1/thesaurus?word={word}'
        api_key = os.getenv("API_NINJA")

        # Check if API key is available
        if not api_key:
            await ctx.send("API key is not set. Please configure the API key.")
            return

        response = requests.get(api_url, headers={'X-Api-Key': api_key})

        if response.status_code == 200:
            data = response.json()
            antonyms = data.get("synonyms", [])
            if antonyms:
                antonyms_list = ' | '.join(antonyms).capitalize()
                
                embed = discord.Embed(title=f"{word.capitalize()}", description=None, color=0x00FFFF)
                
                # Ensure the antonyms list is split correctly if it exceeds 1024 characters
                max_length = 1024 - 4  # account for the '>>>' formatting
                antonym_chunks = [antonyms_list[i:i+max_length] for i in range(0, len(antonyms_list), max_length)]
                
                for i, chunk in enumerate(antonym_chunks):
                    embed.add_field(name=f"Antonyms (Part {i+1})", value=f">>> {chunk}", inline=False)
                
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"No antonyms found for '{word}'.")
        else:
            await ctx.send(f"Error: {response.status_code}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Utility(bot))
        