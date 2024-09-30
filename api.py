# import os
# import shutil
import uvicorn
import logging
import openai
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from tinygen.enums.tinygen_environments import TinygenEnvironment
from tinygen.entities.queries import Query, Queries
from tinygen.helpers.assistant import Assistant
from tinygen.helpers.environment import getenv
from tinygen.helpers.repo import Repo

app = FastAPI()


class ServiceDependencies:
    def __init__(self, assistant: Assistant, queries: Queries, logger: logging.Logger):
        self.assistant = assistant
        self.queries = queries
        self.logger = logger


class PromptRequest(BaseModel):
    repoUrl: str  # consider changing this to snakecase and figuring out how to convert between the two cases
    prompt: str
    file_paths: list[str] | None = None  # Specific file paths to modify


def configure_service() -> ServiceDependencies:
    tinygen_environment = getenv(
        "TINYGEN_ENVIRONMENT", default=TinygenEnvironment.Production
    )

    # Load environment variables and secrets from .env files
    load_dotenv()
    load_dotenv(dotenv_path=".env.secrets")
    if tinygen_environment == TinygenEnvironment.Development:
        load_dotenv(dotenv_path=".env.development", override=True)

    # Configure openai client
    openai.api_key = getenv("OPENAI_API_KEY")

    # Configure supabase db client
    supabase_url = getenv("SUPABASE_URL")
    supabase_key = getenv("SUPABASE_KEY")
    supabase_client: Client = create_client(supabase_url, supabase_key)

    # Configure logging
    log_level = getenv("LOG_LEVEL", logging.INFO).upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log format
        handlers=[
            logging.FileHandler("api.log"),
            logging.StreamHandler(),
        ],
    )

    # Instantiate dependencies
    assistant = Assistant()
    logger = logging.getLogger(__name__)
    queries = Queries(supabase_client)

    return ServiceDependencies(assistant, queries, logger)


# TODO: Consider refactoring this somewhere else
def get_diff(
    original_file_content: dict, user_prompt: str, assistant: Assistant
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

        Please return a unified diff showing any required changes to the files."""

    reflection_prompt = """Are you sure, or would you like to correct your answer? If you're sure say 'y', otherwise give me the revised unified diff.
        If you revise your answer then don't include an apology - aim to keep your response concise."""

    assistant_response = assistant.chat(diff_prompt)

    assistant_reflection = assistant.chat(reflection_prompt)

    if assistant_reflection.lower() == "y":
        return assistant_response

    return assistant_reflection


# TODO: Include any HTTPExceptions?
@app.post("/generate_diff")
async def generate_diff_for_repo(
    request: PromptRequest,
    dependencies: ServiceDependencies = Depends(configure_service),
):
    assistant = dependencies.assistant
    queries = dependencies.queries

    # repo_dir = f"./repos/{os.path.basename(request.repoUrl).split('.')[0]}"

    # TODO: Store inputs and outputs
    queries.insert()

    repo = Repo(request.repoUrl)

    # Clean up any previous repository with the same name
    # if os.path.exists(repo.repo_dir):
    #     shutil.rmtree(repo.repo_dir)

    # clone_repo(request.repoUrl, repo_dir)

    file_content = repo.read_files(request.file_paths)

    generated_diff = get_diff(file_content, request.prompt, assistant)

    # Clean up repo after use
    # shutil.rmtree(repo.repo_dir)

    return JSONResponse(content={"diff": generated_diff})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(getenv("TINYGEN_API_PORT", 8000)))
