import discord
from discord.ext import commands, tasks
from bot.config import Bot
from dotenv import load_dotenv
import asyncio
import requests
import random
import os
from datetime import datetime, timedelta
import parsedatetime
import openai
from bot.core.constant import Color


load_dotenv()

cal = parsedatetime.Calendar()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)


class Utility(commands.Cog):
    def __init__(self, bot : Bot):
        self.bot = bot
        self.db = self.bot.mongo_client["User_Database"]
        self.collection = self.db["Reminders"]
        self.check_reminders.start()
        self.check_event.start()
        self.last_seen_collection = self.db["LastSeen"]
        self.event_collection = self.db["ScheduledEvents"]


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        data = {
            "user_id": message.author.id,
            "channel_id" : message.channel.id,
            "last_seen": datetime.now()
        }

        self.last_seen_collection.update_one(
            {"user_id": message.author.id},
            {"$set": data},
            upsert=True
        )

        await self.bot.process_commands(message)

    @commands.hybrid_command(name="help", description= "Get all the commands list")
    async def help(self, interaction: commands.Context):
        embed = discord.Embed(
            title= "Help",
            description= "List of commands all the commands",
            color= discord.Color.from_str(Color.PRIMARY_COLOR)
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



    @commands.hybrid_command(name="remider", description="Set a reminder")
    async def reminder(self, ctx: commands.Context, *, message: str):
        time_struct , parse_status = cal.parse(message)

        if parse_status == 0:
            await ctx.send("I couldn't understand the time format. Please use a valid format.")
            return
        
        reminder_time = datetime(*time_struct[:6])
        print(reminder_time)
        now = datetime.now()

        if reminder_time < now:
            await ctx.send("The reminder time must be in the future.")
            return
        
        reminder = {
            "user_id": ctx.author.id,
            "channel_id": ctx.channel.id,
            "message": message,
            "reminder_at": reminder_time,
            "created_at": now
        }
        await ctx.send(f"✅ Reminder set for <t:{int(reminder_time.timestamp())}:R>!")
        if (reminder_time - now).total_seconds() < 30:
            await asyncio.sleep((reminder_time - now).total_seconds())
            await ctx.send(f"⏰ Hey {ctx.author.mention}, reminder: **{message}**")
        else:
            self.collection.insert_one(reminder)

        
        
    @tasks.loop(seconds=30)
    async def check_reminders(self):
        now = datetime.now()
        due_reminders = list(self.collection.find({"reminder_at": {"$lte": now}}))

        for reminder in due_reminders:
            user = await self.bot.fetch_user(reminder["user_id"])
            channel = self.bot.get_channel(reminder["channel_id"])
            
            # Fallback in case channel is not found
            if not channel:
                channel = await user.create_dm()

            await channel.send(
                f"⏰ Hey {user.mention}, reminder: **{reminder['message']}**"
            )
            self.collection.delete_one({"_id": reminder["_id"]})

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


    @commands.hybrid_command(name="summarize", description="Summarize discord channel text")
    @commands.cooldown(1, 600,  commands.BucketType.user)
    async def summarize(self, ctx: commands.Context, limit: int = 20):
        if limit > 50:
            await ctx.send("Limit should be less than 50")
            return
        
        await ctx.defer()

        messages = [msg async for msg in ctx.channel.history(limit=limit)]
        messages = list(reversed(messages))  # Oldest to newest
        content = "\n".join([
            f"{msg.author.display_name}: {msg.content}" 
            for msg in messages 
            if msg.content and not msg.author.bot and not msg.content.startswith(ctx.prefix)
            ])

        promt = f"Summarize the following Discord conversation:\n\n{content}\n\nSummary in bullet points:"

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": promt}
            ],
            temperature=0.7,
            max_tokens=500,
        )

        summary = response.choices[0].message.content
        embed = discord.Embed(title="Summary", description=summary, color=0x00FFFF)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="seen", description="Check when a user was last seen")
    async def seen (self, ctx: commands.Context, member: discord.Member = None):

        member = member or ctx.author

        data = self.last_seen_collection.find_one({"user_id": member.id})

        if not data:
            await ctx.send(f"No data found for {member.name}.")
            return
        
        last_seen = data["last_seen"]
        channel_id = data["channel_id"]
        channel = self.bot.get_channel(channel_id)

        timestamp = int(last_seen.timestamp())
        channel_mention = channel.mention if channel else "Unknown Channel"

        embed = discord.Embed(
            title=f"{member.name}'s Last Seen",
            description=f"Last seen in {channel_mention}",
            color=0x00FFFF
        )
        embed.add_field(name="Last Seen", value=f"<t:{timestamp}:R>", inline=False)
        embed.set_footer(text=f"User ID: {member.id}")
        embed.set_thumbnail(url=member.avatar.url)
        await ctx.send(embed=embed)


    @commands.hybrid_command(name="schedule", description="Schedule a message")
    async def schedule(self, ctx: commands.Context, *, message: str):
        if not message:
            await ctx.send("Please provide a message to schedule.")
            return
        
        if " at " in message:
            title, time_str = message.split(" at ", 1)
        elif " on " in message:
            title, time_str = message.split(" on ", 1)
        else:
            title, time_str = message, ""

        time_struct, parse_status = cal.parse(time_str)
        if parse_status == 0:
            await ctx.send("I couldn't understand the time format. Please use a valid format.")
            return
        
        scheduled_for = datetime(*time_struct[:6])
        now = datetime.now()

        if scheduled_for < now:
            await ctx.send("The scheduled time must be in the future.")
            return
        
        event = {
            "user_id": ctx.author.id,
            "channel_id": ctx.channel.id,
            "event_title": title.strip().capitalize(),
            "scheduled_for": scheduled_for,
            "created_at": now
        }

        self.event_collection.insert_one(event)

        await ctx.send(f"✅ Event '**{event['event_title']}**' scheduled for <t:{int(scheduled_for.timestamp())}:F> (<t:{int(scheduled_for.timestamp())}:R>)")


    @tasks.loop(seconds=30)
    async def check_event(self):
        now  = datetime.now()

        due_events = list(self.event_collection.find({"scheduled_for": {"$lte": now}}))

        for event in due_events:
            channel = self.bot.get_channel(event["channel_id"])
            user = await self.bot.fetch_user(event["user_id"])

            if not channel:
                channel = await user.create_dm()

            await channel.send(f"⏰ Event: **{event['event_title']}** is happening now!")
            self.event_collection.delete_one({"_id": event["_id"]})


    @commands.hybrid_command(name="my_events", description="Get all your scheduled events")
    async def my_events(self, ctx: commands.Context):
        user_id = ctx.author.id
        events = list(self.event_collection.find({"user_id": user_id}))
        if not events:
            await ctx.send("You have no scheduled events.")
            return
        
        embed = discord.Embed(title="Your Scheduled Events", color= discord.Color.from_str(Color.PRIMARY_COLOR))
        for event in events:
            event_time = event["scheduled_for"].strftime("%A, %d %B %Y %H:%M")
            embed.add_field(name=event["event_title"], value=f"Scheduled for: {event_time}", inline=False)
        embed.set_footer(text=f"Total Events: {len(events)}")
        await ctx.send(embed=embed)




async def setup(bot: commands.Bot):
    await bot.add_cog(Utility(bot))
        