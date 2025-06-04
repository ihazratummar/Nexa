class _Color:
    """
    Enum for color codes used in embeds.
    """

    def __init__(self):
        pass

    PRIMARY_COLOR = "0x00FFFF"


Color = _Color()


## Database Constants

class _DbCons:
    """
    Database Constants
    """

    def __init__(self):
        pass

    #Database Name
    LEVEL_DATABASE = "Level_Database"
    USER_DATABASE = "User_Database"
    BOT_DATABASE = "BotDatabase"


    #Collection Name
    LEVEL_COLLECTION = "level"
    ECONOMY_COLLECTION = "Economy"
    GUILD_SETTINGS_COLLECTION = "guild_settings"


DbCons = _DbCons()


class _Channel:
    def __init__(self):
        pass

    DEV_NOTIFICATION_CHANNEL = 1246450850000539678

Channel = _Channel()