from bot.cogs.welcome.boosts import Boosts
from bot.cogs.welcome.welcomer import Welcomer
from bot.cogs.welcome.welcome_commands import WelcomeCommands


async def setup(bot):
    await bot.add_cog(Welcomer(bot))
    await bot.add_cog(WelcomeCommands(bot))
    await bot.add_cog(Boosts(bot))