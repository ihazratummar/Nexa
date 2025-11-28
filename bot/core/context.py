import discord
from discord.ext import commands
import asyncio

class CustomContext(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.command_config = None

    async def send(self, content=None, **kwargs):
        # Fetch config if not already fetched (it should be fetched by the guard/check)
        if not self.command_config and self.guild and self.command:
             # We can try to fetch it from the bot's cache method
             # But usually, the 'guard' check runs before this and can set it.
             # For now, let's assume the guard sets it on the context or we fetch it here.
             pass

        # Execute the send
        message = await super().send(content, **kwargs)

        # Apply Auto-Delete Logic
        if self.command_config:
            settings = self.command_config.settings
            
            # Auto-delete Bot Response
            if settings.auto_delete_response:
                delay = settings.response_delete_delay
                # We use the loop to schedule deletion without blocking
                self.bot.loop.create_task(self._delete_after_delay(message, delay))

        return message

    async def _delete_after_delay(self, message: discord.Message, delay: int):
        await asyncio.sleep(delay)
        try:
            await message.delete()
        except discord.HTTPException:
            pass

    async def entry_point_cleanup(self):
        """Called after command execution to clean up invocation if needed."""
        if self.command_config and self.command_config.settings.auto_delete_invocation:
            try:
                await self.message.delete()
            except discord.HTTPException:
                pass
