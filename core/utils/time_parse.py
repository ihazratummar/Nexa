import re
from datetime import datetime, timedelta

from loguru import logger

from modules.error.custom_errors import GenericError


def parse_duration(duration_str: str) -> timedelta:
    """
        Parses a string like '1d', '2w', '30m', '10s' into a timedelta object.
        Raises ValueError on invalid format.
        """
    try:
        duration_str = duration_str.lower().strip()
        match = re.match(r'^(\d+)\s*([a-z]+)$', duration_str, re.IGNORECASE)
        if not match:
            raise GenericError(f"Invalid duration format: '{duration_str}'. Example format: '30d' or '1m'")

        value, unit = int(match.group(1)), match.group(2)

        # Check prefixes
        if unit in ('s', 'sec', 'seconds'):
            return timedelta(seconds=value)
        elif unit in ('m', 'min', 'minutes'):
            return timedelta(minutes=value)
        elif unit in ('h', 'hr', 'hours'):
            return timedelta(hours=value)
        elif unit in ('d', 'day', 'days'):
            return timedelta(days=value)
        elif unit in ('w', 'week', 'weeks'):
            return timedelta(weeks=value)
        elif unit in ('mo', 'month', 'months'):
            return timedelta(days=value * 30)  # approximate
        else:
            raise GenericError(f"Unknown time unit: '{unit}'")
    except Exception as e:
        logger.error(f"Failed to parse time format: {duration_str}")
        raise GenericError(f"Invalid time format: {duration_str}")
