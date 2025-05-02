from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict


class EmbedField(BaseModel):
    name: str = Field(..., description="Name of the embed field")
    value: str = Field(..., description="Value of the embed field")
    inline: bool = Field(default=True, description="Whether the field is inline")


class WelcomeEmbed(BaseModel):
    title: Optional[str] = "Welcome!"
    description: Optional[str] = "Glad to have you here!"
    color: Optional[str] = None  # Hex color code as a string (e.g., "#FF5733")
    thumbnail_url: Optional[str] = None
    image_url: Optional[str] = None
    footer: Optional[str] = None
    fields: List[EmbedField] = Field(default_factory=list)

    @validator("color")
    def validate_color(cls, value):
        if value and not value.startswith("#"):
            raise ValueError("Color must be a hex string starting with '#'")
        return value


class LogChannel(BaseModel):
    mod_logs: Optional[str] = None
    message_logs: Optional[str] = None
    join_leave_logs: Optional[str] = None
    command_logs: Optional[str] = None


class GuildSettings(BaseModel):
    guild_id: int
    prefix: str = "!"

    # Welcome settings
    welcome_enabled: bool = False
    welcome_channel_id: Optional[str] = None
    welcome_embed: Optional[WelcomeEmbed] = None 
    # AutoMod settings
    automod_enabled: bool = False
    banned_words: List[str] = Field(default_factory=list)
    spam_protection_enabled: bool = False

    # Logging settings
    logging_enabled: bool = False
    log_channel: Optional[LogChannel] = None

    # Leveling settings
    leveling_enabled: bool = False
    leveling_channel_id: Optional[str] = None
    level_roles: Dict[int, str] = Field(default_factory=dict)

    # Economy settings
    economy_enabled: bool = False
    economy_channel_id: Optional[str] = None
    starting_balance: int = 100

    # Notification settings
    notify_channel_id: Optional[str] = None
    notify_role_id: Optional[str] = None

    # Miscellaneous
    timezone: Optional[str] = None
    language: Optional[str] = None

    #Roles
    new_member_join_role: Optional[str] = None  # Role to assign to new members
    bot_role: Optional[str] = None  # Role for the bot itself
