from pydantic import BaseModel
from datetime import datetime


class Query(BaseModel):
    repo_url: str
    prompt: str
    diff: str | None
    created_utc: datetime
    updated_utc: datetime
