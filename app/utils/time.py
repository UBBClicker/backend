from datetime import datetime, timezone


def datetime_now_sec():
    return datetime.now(tz=timezone.utc)


__all__ = [
    "datetime_now_sec",
]
