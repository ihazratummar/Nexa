from builtins import int
import discord
from discord.ext import commands
from bot.config import Bot
from typing import Dict
from bot.core.constant import Color


class Economy(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.currency_icon = "💰"
        self.db = bot.mongo_client["User_Database"]
        self.collection =self.db["Economy"]
 

    @commands.hybrid_command(name="balance", with_app_command=True)
    async def balance(self, ctx: commands.Context):
        user_id = str(ctx.author.id)
        user_data = self.collection.find_one({"_id": user_id})

        if user_data:
            wallet = user_data.get("wallet", 0)
            bank = user_data.get("bank", 0)

            embed = discord.Embed(
                title=f"{ctx.author.name}'s Balance",
                description=f"Wallet -{self.currency_icon} {wallet}\nBank -{self.currency_icon} {bank}",
                color=discord.Color.from_str(Color.PRIMARY_COLOR),
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("You don't have an account yet. Use `/create_account` to create one.")

    @commands.hybrid_command(name="create_account", with_app_command=True)
    async def create_account(self, ctx: commands.Context):
        user_id = str(ctx.author.id)
        user_data = self.collection.find_one({"_id": user_id})

        if user_data:
            await ctx.send("You already have an account.")
        else:
            self.collection.insert_one(
                {"_id": user_id, "wallet": 500, "bank":0, "inventory": [], "last_crime": 0, "last_rob": 0, "last_daily":0 }
            )
            await ctx.send("Account created successfully!")

    @commands.hybrid_command(name="daily", with_app_command=True)
    async def daily(self, ctx: commands.Context):
        user_id = str(ctx.author.id)
        user_data = self.collection.find_one({"_id": user_id})

        if not user_data:
            await ctx.send("You don't have an account yet. Use `/create_account` to create one.")
            return

        last_daily = user_data.get("last_daily", 0)
        current_time = int(discord.utils.utcnow().timestamp())

        if current_time - last_daily < 86400:
            await ctx.send("You can only claim your daily reward once every 24 hours.")
            return

        reward = 1000
        self.collection.update_one(
            {"_id": user_id},
            {"$inc": {"wallet": reward}, "$set": {"last_daily": current_time}},
        )
        await ctx.send(f"You have received {self.currency_icon} {reward} as your daily reward!")

    @commands.hybrid_command(name="deposit", with_app_command=True)
    async def deposit(self, ctx: commands.Context, amount: int):
        user_id = str(ctx.author.id)
        user_data = self.collection.find_one({"_id": user_id})

        if not user_data:
            await ctx.send("You don't have an account yet. Use `/create_account` to create one.")
            return

        wallet = user_data.get("wallet", 0)

        if amount > wallet:
            await ctx.send("You don't have enough money in your wallet.")
            return

        self.collection.update_one(
            {"_id": user_id},
            {"$inc": {"wallet": -amount, "bank": +amount}},
        )
        await ctx.send(f"You have deposited {self.currency_icon} {amount} into your bank.")


    @commands.hybrid_command(name="withdraw", with_app_command=True)
    async def withdraw(self, ctx: commands.Context, amount: int):
        user_id  = str(ctx.author.id)
        user_data = self.collection.find_one({"_id": user_id})
        if not user_data:
            await ctx.send("You don't have an account yet. Use `/create_account` to create one.")
            return
        
        bank = user_data.get("bank", 0)
        if amount > bank:
            await ctx.send("You don't have enough money in your bank.")
            return
        self.collection.update_one(
            {"_id": user_id},
            {"$inc": {"wallet": +amount, "bank": -amount}},
        )
        await ctx.send(f"You have withdrawn {self.currency_icon} {amount} from your bank.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
