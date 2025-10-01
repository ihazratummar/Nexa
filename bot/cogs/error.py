import discord
from discord.ext import commands
from discord import app_commands
from bot.config import Bot

from bot.core.embed.embed_builder import log_embed


class ErrorCog(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        bot.tree.on_error = self.on_command_error

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if hasattr(ctx.command, 'on_error'):
            return

        cog = ctx.cog
        if cog and cog._get_overridden_method(cog.cog_command_error) is not None:
            return

        error = getattr(error, 'original', error)

        error_map = {
            commands.CommandNotFound: ("Command Not Found", "The command you tried to use does not exist."),
            commands.RoleNotFound: "One or more roles were not found. Make sure you mention or pass valid roles.",
            commands.DisabledCommand: ("Command Disabled", f"The command `{ctx.command}` is currently disabled."),
            commands.NoPrivateMessage: ("Server Only Command", f"The command `{ctx.command}` cannot be used in private messages."),
            commands.PrivateMessageOnly: ("DM Only Command", f"The command `{ctx.command}` can only be used in private messages."),
            commands.NotOwner: ("Owner Only Command", f"The command `{ctx.command}` can only be used by the bot owner."),
            commands.MissingPermissions: ("Missing Permissions","You do not have the required permissions to run this command."),
            commands.BotMissingPermissions: ("Bot Missing Permissions", "I do not have the required permissions to run this command."),
            commands.CheckFailure: ("Permission Denied", "You do not have permission to use this command."),
            app_commands.CommandNotFound: ("App Command Not Found", "The application command you tried to use does not exist."),
            app_commands.MissingPermissions: ("Missing App Permissions", "You do not have the required permissions to run this application command."),
            app_commands.BotMissingPermissions: ("Bot Missing App Permissions","I do not have the required permissions to run this application command."),
            app_commands.MissingRole: "One or more roles were not found."
        }

        error_type = type(error)
        if error_type in error_map:
            title, description = error_map[error_type]
            embed = log_embed(title=title, description=description, color=discord.Color.orange())
            await ctx.send(embed=embed, ephemeral=True)
        elif isinstance(error, commands.CommandOnCooldown):
            embed = log_embed(
                title="Command on Cooldown",
                description=f"This command is on cooldown. Please try again in {error.retry_after:.2f}s.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed, ephemeral=True)
        else:
            embed = log_embed(
                title="An Unexpected Error Occurred",
                description="An unexpected error has occurred. The developers have been notified.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            print(error)


async def setup(bot: commands.Bot):
    await bot.add_cog(ErrorCog(bot))
