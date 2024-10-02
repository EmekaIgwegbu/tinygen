import os
from typing import Optional


def getenv(key: str, default=None) -> Optional[str]:
    env = os.getenv(key)
    if env == "" or env is None:
        return default
    return env
