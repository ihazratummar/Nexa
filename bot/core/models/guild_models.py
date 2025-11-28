from datetime import datetime

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
    
    is_premium: bool = Field(default=False)

class AutoModGlobal(BaseModel):
    is_enabled: bool = True
    ignored_channels: List[str] = Field(default_factory=list)
    ignored_roles: List[str] = Field(default_factory=list)
    media_only_channels: List[str] = Field(default_factory=list)
    youtube_only_channels: List[str] = Field(default_factory=list)
    twitch_only_channels: List[str] = Field(default_factory=list)

class FilterConfig(BaseModel):
    enabled: bool = False
    actions: List[str] = Field(default_factory=list)
    timeout_duration: int = 60
    ignored_roles: List[str] = Field(default_factory=list)
    ignored_channels: List[str] = Field(default_factory=list)
    custom_config: Dict = Field(default_factory=dict)

class AutoModFilters(BaseModel):
    spam: FilterConfig = Field(default_factory=FilterConfig)
    bad_words: FilterConfig = Field(default_factory=FilterConfig)
    duplicate_text: FilterConfig = Field(default_factory=FilterConfig)
    repeated_messages: FilterConfig = Field(default_factory=FilterConfig)
    discord_invites: FilterConfig = Field(default_factory=FilterConfig)
    links: FilterConfig = Field(default_factory=FilterConfig)
    spammed_caps: FilterConfig = Field(default_factory=FilterConfig)
    emoji_spam: FilterConfig = Field(default_factory=FilterConfig)
    mass_mention: FilterConfig = Field(default_factory=FilterConfig)
    ai_moderation: FilterConfig = Field(default_factory=FilterConfig)

class AutoModRule(BaseModel):
    threshold: int
    action: str
    duration: Optional[int] = None

class AutoModSettings(BaseModel):
    guild_id: str
    global_settings: AutoModGlobal = Field(alias="global", default_factory=AutoModGlobal)
    filters: AutoModFilters = Field(default_factory=AutoModFilters)
    automod_rules: List[AutoModRule] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ModerationSettings(BaseModel):
    is_moderation_settings_enabled: bool = Field(default=True)
    guild_id: str
    mode_roles : List[Dict[str, str]] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)



class CommandSettings(BaseModel):
    max_limit: int = Field(default=4)
    auto_delete_invocation: bool = Field(default=False)
    auto_delete_response: bool = Field(default=False)
    auto_delete_with_invocation: bool = Field(default=False)
    response_delete_delay: int = Field(default=5)


class CommandConfig(BaseModel):
    guild_id: str
    command: str
    description: Optional[str] = None
    category: str = "General"
    enabled: bool = True

    aliases: List[str] = Field(default_factory=list)

    enabled_roles: List[str] = Field(default_factory=list)
    disabled_roles: List[str] = Field(default_factory=list)

    enabled_channels: List[str] = Field(default_factory=list)
    disabled_channels: List[str] = Field(default_factory=list)

    roles_skip_limit: List[str] = Field(default_factory=list)

    settings: CommandSettings = Field(default_factory=CommandSettings)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
