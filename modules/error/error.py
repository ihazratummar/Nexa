import discord
from discord.ext import commands
from discord import app_commands

from core.embed.embed_builder import embed_builder
from modules.error.custom_errors import HierarchyError, BaseBotError, ModerationDisabled, GenericError


class ErrorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.tree.on_error = self.on_app_command_error

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if hasattr(ctx.command, 'on_error'):
            return

        cog = ctx.cog
        if cog and cog._get_overridden_method(cog.cog_command_error) is not None:
            return

        await self._handle_error(ctx, error)

    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        await self._handle_error(interaction, error)

    async def _handle_error(self, ctx_or_interaction: commands.Context | discord.Interaction, error):
        # Recursively unwrap the error to find the root cause (e.g., CommandInvokeError -> GenericError)
        while hasattr(error, 'original') and error.original:
            error = error.original

        error_map = {
            commands.CommandNotFound: ("Command Not Found", "The command you tried to use does not exist."),
            commands.RoleNotFound: "One or more roles were not found. Make sure you mention or pass valid roles.",
            commands.DisabledCommand: ("Command Disabled", "The command is currently disabled."),
            commands.NoPrivateMessage: ("Server Only Command", "The command cannot be used in private messages."),
            commands.PrivateMessageOnly: ("DM Only Command", "The command can only be used in private messages."),
            commands.NotOwner: ("Owner Only Command", "The command can only be used by the bot owner."),
            commands.MissingPermissions: ("Missing Permissions", "You do not have the required permissions to run this command."),
            commands.BotMissingPermissions: ("Bot Missing Permissions", "I do not have the required permissions to run this command."),
            commands.CheckFailure: ("Permission Denied", "You do not have permission to use this command."),
            app_commands.CommandNotFound: ("App Command Not Found", "The application command you tried to use does not exist."),
            app_commands.MissingPermissions: ("Missing App Permissions", "You do not have the required permissions to run this application command."),
            app_commands.BotMissingPermissions: ("Bot Missing App Permissions", "I do not have the required permissions to run this application command."),
            app_commands.MissingRole: "One or more roles were not found.",
        }

        description = None
        title = "An Error Occurred"

        # Check if it's one of our custom errors (BaseBotError or subclasses like GenericError)
        if hasattr(error, 'title') or isinstance(error, BaseBotError):
            title = getattr(error, 'title', "Error")
            description = str(error)

        elif type(error) in error_map:
            result = error_map[type(error)]
            if isinstance(result, tuple):
                title, description = result
            else:
                description = result
        elif isinstance(error, (commands.CommandOnCooldown, app_commands.CommandOnCooldown)):
            title = "Command on Cooldown"
            description = f"This command is on cooldown. Please try again in {error.retry_after:.2f}s."
        else:
            title = "An Unexpected Error Occurred"
            description = "An unexpected error has occurred. The developers have been notified."
            print(f"Unexpected Error: {error}")

        if description:
            embed = embed_builder(title=title, description=description, color=discord.Color.orange() if "Unexpected" not in title else discord.Color.red())
            await self._send_error(ctx_or_interaction, embed)

    async def _send_error(self, ctx_or_interaction: commands.Context | discord.Interaction, embed: discord.Embed):
        try:
            if isinstance(ctx_or_interaction, discord.Interaction):
                if ctx_or_interaction.response.is_done():
                    await ctx_or_interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await ctx_or_interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await ctx_or_interaction.send(embed=embed)
        except Exception as e:
            print(f"Failed to send error message: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(ErrorCog(bot))
