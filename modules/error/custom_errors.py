from discord.ext import  commands
from discord import  app_commands


class BaseBotError(commands.CheckFailure, app_commands.CheckFailure):
    def __init__(self, message: str, title: str = "Error") -> None:
        super().__init__(message)
        self.title = title


class ModerationDisabled(BaseBotError):
    def __init__(self, message: str):
        super().__init__("⚠️ Moderation system is disabled in this server.", title="Moderation Disabled")

class HierarchyError(BaseBotError):
    def __init__(self, message):
        super().__init__(message, title="Hierarchy Error")