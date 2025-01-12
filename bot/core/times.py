from datetime import datetime, time, timedelta
from pytz import timezone


def get_next_week_day(now: datetime, target_day: int, target_time: time, local_tz: timezone) -> datetime:
    today_target = datetime.combine(now.date(), target_time, tzinfo=local_tz)

    if now.weekday() == target_day and now < today_target:
        return today_target
    else:
        days_until_target = (target_day - now.weekday()) % 7
        if days_until_target == 0:
            days_until_target = 7
        next_date = now.date() + timedelta(days=days_until_target)
        return datetime.combine(next_date, target_time, tzinfo=local_tz)