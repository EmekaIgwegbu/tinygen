from pydantic import BaseModel
from datetime import datetime
from supabase import Client
from app.exceptions.database_error import DatabaseError
import logging

logger = logging.getLogger(__name__)


class Query(BaseModel):
    id: int = 0
    repo_url: str
    prompt: str
    diff: str | None = None
    created_utc: datetime = None
    updated_utc: datetime = None


class Queries:
    """Interacts with the Queries supabase table."""

    def __init__(self, client: Client):
        self.supabase_client = client

    def insert(self, query: Query) -> Query:
        """Insert an entry in the Queries table then return the resulting record."""
        logger.debug(f"Inserting a query entry")

        try:
            response = (
                self.supabase_client.table(Queries.__name__)
                .insert(
                    {
                        "repo_url": query.repo_url,
                        "prompt": query.prompt,
                        "diff": query.diff,
                    }
                )
                .execute()
            )

            logger.debug(f"Entry successfully inserted")
            return Query.model_validate(response.data[0])

        except Exception as e:
            raise DatabaseError(
                message=f"Failed to insert entry: {e}",
                table_name=Queries.__name__,
            )

    def update_diff_by_id(self, diff: str, id: int) -> Query:
        """Update query output (diff) and return the result."""
        logger.debug(f"Updating query diff")

        try:
            response = (
                self.supabase_client.table(Queries.__name__)
                .update(
                    {
                        "diff": diff,
                    }
                )
                .eq("id", id)
                .execute()
            )

            logger.debug(f"Diff successfully updated")
            return Query.model_validate(response.data[0])

        except Exception as e:
            raise DatabaseError(
                message=f"Failed to update diff for query {id}: {e}",
                table_name=Queries.__name__,
            )
