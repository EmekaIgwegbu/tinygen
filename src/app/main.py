import uvicorn
import logging
import openai
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from app.enums.tinygen_environments import TinygenEnvironment
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
    # TODO: Will have to figure out where to set this env var
    tinygen_environment = TinygenEnvironment(
        getenv("TINYGEN_ENVIRONMENT", default=TinygenEnvironment.Production.value)
    )

    # Load environment variables and secrets from .env files
    load_dotenv()
    load_dotenv(dotenv_path=".env.secrets")
    if tinygen_environment == TinygenEnvironment.Development:
        load_dotenv(dotenv_path=".env.development", override=True)

    # Configure openai client
    openai.api_key = getenv("OPENAI_API_KEY")

    # Configure supabase db client
    supabase_client: Client = create_client(getenv("SUPABASE_URL"), getenv("SUPABASE_KEY"))

    # Configure global root logger
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
async def generate_diff(
    request: PromptRequest,
    dependencies: ServiceDependencies = Depends(configure_service),
):
    assistant = dependencies.assistant
    queries = dependencies.queries

    # Store query inputs
    query = queries.insert(Query(repo_url=request.repoUrl, prompt=request.prompt))

    # Pull latest from remote repo and store on local disk
    repo = Repo(request.repoUrl)

    file_content = repo.read_all_files()

    generated_diff = get_diff(file_content, request.prompt, assistant)

    # Store query output (diff)
    queries.update_diff_by_id(generated_diff, query.id)

    return JSONResponse(content={"diff": generated_diff})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(getenv("TINYGEN_API_PORT", 8000)))
