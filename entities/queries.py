from pydantic import BaseModel
from datetime import datetime
from supabase import Client
from tinygen.exceptions.database_error import DatabaseError
import logging

logger = logging.getLogger(__name__)


class Query(BaseModel):
    id: int
    repo_url: str
    prompt: str
    diff: str | None
    created_utc: datetime
    updated_utc: datetime


class Queries:
    """Interacts with the Queries supabase table."""

    def __init__(self, client: Client):
        self.supabase_client = client

    def insert(self, query: Query) -> Query:
        """Insert an entry in the Queries table then return the resulting record."""
        logger.debug(f"Inserting a query entry")

        try:
            response = (
                self.supabase_client.table("users")
                .insert(
                    {
                        "repo_url": query.repo_url,
                        "prompt": query.prompt,
                        "diff": query.diff,
                    }
                )
                .execute()
            )

            logger.debug(f"Query added successfully: {response.data}")
            # TODO: Remove two lines below when done debugging
            result = Query.model_validate_json(response.data)
            logger.debug(f"Result is {result}")
            return Query.model_validate_json(response.data)

        except Exception as e:
            raise DatabaseError(
                message=f"Failed to insert entry {query.model_dump_json()}",
                table_name=Queries.__name__,
            )

    def update_diff_by_id(self, diff: str, id: int) -> Query:
        """Update query output (diff) and return the result."""
        logger.debug(f"Updating a query entry")

        try:
            response = (
                self.supabase_client.table("users")
                .update(
                    {
                        "diff": diff,
                    }
                )
                .eq("id", id)
                .execute()
            )

            logger.debug(f"Diff updated successfully: {response.data}")
            # TODO: Remove two lines below when done debugging
            result = Query.model_validate_json(response.data)
            logger.debug(f"Result is {result}")
            return Query.model_validate_json(response.data)

        except Exception as e:
            raise DatabaseError(
                message=f"Failed to update diff for query {id}",
                table_name=Queries.__name__,
            )
