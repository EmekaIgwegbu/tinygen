import os
import uvicorn
import logging
import openai
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from fastapi.responses import JSONResponse
from app.entities.queries import Query, Queries
from app.helpers.assistant import Assistant
from app.helpers.environment import getenv
from app.helpers.repo import Repo

app = FastAPI()


class ServiceDependencies:
    def __init__(self, assistant: Assistant, queries: Queries, logger: logging.Logger):
        self.assistant = assistant
        self.queries = queries
        self.logger = logger


class PromptRequest(BaseModel):
    repoUrl: str
    prompt: str


def configure_service() -> ServiceDependencies:
    # Configure openai client
    openai.api_key = getenv("OPENAI_API_KEY")

    # Configure supabase db client
    supabase_client: Client = create_client(
        getenv("SUPABASE_URL"), getenv("SUPABASE_KEY")
    )

    # Configure global root logger
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log format
        handlers=[
            logging.FileHandler("logs/app.log"),
            logging.StreamHandler(),
        ],
    )

    # Configure app root logger
    logging.getLogger("app").setLevel(getenv("LOG_LEVEL", logging.INFO).upper())

    # Instantiate dependencies
    assistant = Assistant()
    logger = logging.getLogger(__name__)
    queries = Queries(supabase_client)

    return ServiceDependencies(assistant, queries, logger)


# TODO: Consider refactoring this somewhere else
def generate_code_changes(
    original_file_content: dict,
    user_prompt: str,
    assistant: Assistant,
    logger: logging.Logger,
) -> str:
    file_text = "\n\n".join(
        [
            f"### {file_name}\n{content}"
            for file_name, content in original_file_content.items()
        ]
    )

    diff_prompt = f"""
        You are working on the following repository files:
        {file_text}

        The user has said the following:
        {user_prompt}

        Make any required changes to the files. Return your answer as a JSON-formatted string where the filepath (relative to the repo root) is mapped to the resulting code."""

    reflection_prompt = """Would you like to improve on the generated code? Any bug fixes or optimizations? If not say 'n'. Otherwise, make any required changes to your original output."""

    assistant_response = assistant.chat(diff_prompt)

    logger.debug(f"Original assistant response: {assistant_response}")

    assistant_reflection = assistant.chat(reflection_prompt)

    if assistant_reflection.lower() == "n":
        return assistant_response

    return assistant_reflection


# TODO: Include any HTTPExceptions?
@app.post("/generate_diff")
async def generate_diff(
    request: PromptRequest,
    dependencies: ServiceDependencies = Depends(configure_service),
):
    assistant = dependencies.assistant
    queries = dependencies.queries
    logger = dependencies.logger

    # Store query inputs
    # query = queries.insert(Query(repo_url=request.repoUrl, prompt=request.prompt))

    # Pull latest changes from remote repo and write to file system
    repo = Repo(request.repoUrl)

    file_content = repo.read_all_files()

    code_changes = generate_code_changes(
        file_content, request.prompt, assistant, logger
    )

    repo.write_to_files(code_changes)
    diff = repo.get_diff()

    # Store query output (diff)
    # queries.update_diff_by_id(diff, query.id)

    return JSONResponse(content={"diff": diff})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(getenv("TINYGEN_API_PORT", 8000)))
