from bot.cogs.Automod.automod import AutoMod
from bot.cogs.Automod.mod_commands import ModCommands


async def setup(bot):
    await bot.add_cog(ModCommands(bot=bot))
    await bot.add_cog(AutoMod(bot=bot))