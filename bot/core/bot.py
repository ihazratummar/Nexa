import discord
from discord.ext.commands import AutoShardedBot


class Bot(AutoShardedBot):
    def __init__(self):
        intents =  discord.Intents.all()
        super().__init__(
            command_prefix="n!",
            help_command=None,
            intents= intents,
            owner_id=475357995367137282
        )


    async def setup_hook(self) -> None:
        """Called when the bot has successfully been initialized."""

        ## Connect to Database

        ## Load Modules





