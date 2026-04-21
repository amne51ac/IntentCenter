import datetime


def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)
