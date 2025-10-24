from enum import  Enum


class _Color:
    """
    Enum for color codes used in embeds.
    """

    def __init__(self):
        pass

    PRIMARY_COLOR = "0x00FFFF"


Color = _Color()


## Database Constants

class DbCons(Enum):
    """
    Database Constants
    """

    #Database Name
    DATABASE_NAME = "Nexa"


    #Collection Name
    LEVEL_COLLECTION = "level"
    ECONOMY_COLLECTION = "Economy"
    GUILD_SETTINGS_COLLECTION = "guild_settings"
    LAST_SEEN_COLLECTION = "last_seen"
    SCHEDULE_EVENTS_COLLECTION = "scheduled_events"
    EMBED_COLLECTION = "embeds"


class _Channel:
    def __init__(self):
        pass

    DEV_NOTIFICATION_CHANNEL = 1246450850000539678

Channel = _Channel()