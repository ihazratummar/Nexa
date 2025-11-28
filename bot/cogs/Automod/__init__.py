from bot.cogs.Automod.automod import AutoMod
from bot.cogs.Automod.auto_mod_commands import AutoModCommands


async def setup(bot):
    await bot.add_cog(AutoModCommands(bot=bot))
    await bot.add_cog(AutoMod(bot=bot))