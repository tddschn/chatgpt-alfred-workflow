from datetime import datetime


def date_from_chatgpt_unix_timestamp(ts: str) -> datetime:
    # ts is like 1682000887.0
    return datetime.fromtimestamp(float(ts))
