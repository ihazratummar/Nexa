
# Database and Collection Analysis

This document outlines the current usage of databases and collections in the project and proposes a unified structure.

## Current Usage

### Databases

- **`BotDatabase`**:
  - `bot/cogs/welcomer.py`
  - `bot/config.py`
  - `bot/cogs/Utility/utility_commands.py`
  - `bot/cogs/logs.py`
- **`User_Database`**:
  - `bot/cogs/Utility/utility_commands.py`
- **Dynamically named databases**: `f"{message.guild.name}({message.guild.id})"`
  - `bot/cogs/Rewards/level.py`

### Collections

- **`guild_settings`**:
  - `bot/cogs/Automod/automod.py`
  - `bot/cogs/Automod/mod_commands.py`
  - `bot/cogs/welcomer.py`
  - `bot/cogs/Utility/utility_commands.py`
  - `bot/cogs/logs.py`
- **`Economy`**:
  - `bot/cogs/Rewards/economy.py`
- **`Reminders`**:
  - `bot/cogs/Utility/utility_commands.py`
- **`LastSeen`**:
  - `bot/cogs/Utility/utility_commands.py`
- **`ScheduledEvents`**:
  - `bot/cogs/Utility/utility_commands.py`
- **Dynamically named collections in `level.py`**:
    - `self.db[f"{message.guild.name}({message.guild.id})"]`

## Proposed Unified Structure

All collections should be moved into a single database named `Nexa`.

### `bot/core/constant.py` collection constants

Here are the proposed constants for `bot/core/constant.py`:

```python
class _DbCons:
    """
    Database Constants
    """

    def __init__(self):
        pass

    # Database Name
    DATABASE_NAME = "Nexa"

    # Collection Names
    GUILD_SETTINGS = "guild_settings"
    ECONOMY = "economy"
    REMINDERS = "reminders"
    LAST_SEEN = "last_seen"
    SCHEDULED_EVENTS = "scheduled_events"
    LEVELS = "levels"


DbCons = _DbCons()
```
