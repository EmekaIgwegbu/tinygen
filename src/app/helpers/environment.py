import os


def getenv(key: str, default=None) -> str | None:
    env = os.getenv(key)
    if env == "" or env is None:
        return default
    return env
