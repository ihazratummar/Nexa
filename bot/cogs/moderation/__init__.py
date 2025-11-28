from bot.cogs.moderation.moderation_commands import ModerationCommands


async def setup(bot):
    await bot.add_cog(ModerationCommands(bot=bot))