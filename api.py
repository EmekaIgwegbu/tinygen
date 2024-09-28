import os
import shutil
import uvicorn
import openai
import git
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from typing import Optional, List, Dict
from fastapi.responses import JSONResponse
from datetime import datetime
from dotenv import load_dotenv

app = FastAPI()

# TODO: Make all this configuration neater. An init function?
load_dotenv()

# OpenAI configuration
openai.api_key = os.getenv("OPENAI_API_KEY")

# Supabase configuration
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

api_port = os.getenv("API_PORT")

supabase: Client = create_client(supabase_url, supabase_key)
open_ai_client = openai.OpenAI()


class Query(BaseModel):
    repo_url: str
    prompt: str
    diff: Optional[str]
    created_utc: datetime
    updated_utc: datetime


class PromptRequest(BaseModel):
    repoUrl: str  # consider changing this to snakecase and figuring out how to convert between the two cases
    prompt: str
    file_paths: Optional[List[str]] = None  # Specific file paths to modify


def clone_repo(repo_url: str, repo_dir: str):
    try:
        git.Repo.clone_from(repo_url, repo_dir)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to clone repository: {e}")


CODE_FILE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".html",
    ".css",
    ".java",
    ".cpp",
    ".c",
    ".go",
    ".rs",
    ".swift",
    ".rb",
}


def is_code_file(file_path: str) -> bool:
    # Check if the file has a valid code extension
    _, ext = os.path.splitext(file_path)
    return ext in CODE_FILE_EXTENSIONS


def should_skip_file(full_path: str, repo_dir: str) -> bool:
    # Skip files based on directory

    # Skip specific folders like 'node_modules' or '.git'
    relative_path = os.path.relpath(full_path, repo_dir)
    skip_folders = ["node_modules", "vendor", ".git", "build", "dist"]
    return any(folder in relative_path for folder in skip_folders)


# Function to read file contents, either from specified files or all files if no files specified
def read_files(file_paths: Optional[List[str]], repo_dir: str) -> Dict[str, str]:
    files_content = {}

    # If file_paths is None or an empty list, read all files in the repo
    if not file_paths:
        for root, dirs, files in os.walk(repo_dir):
            for file in files:
                full_path = os.path.join(root, file)
                if is_code_file(full_path):
                    try:
                        with open(full_path, "r") as f:
                            # Store file content, with path relative to the repo_dir
                            relative_path = os.path.relpath(full_path, repo_dir)
                            files_content[relative_path] = f.read()
                    except Exception as e:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Could not read file {full_path}: {str(e)}",
                        )
    else:
        # Follow original approach if file_paths is provided
        for file_path in file_paths:
            full_path = os.path.join(repo_dir, file_path)
            if os.path.exists(full_path):
                try:
                    with open(full_path, "r") as file:
                        files_content[file_path] = file.read()
                except Exception as e:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Could not read file {full_path}: {str(e)}",
                    )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file_path} does not exist in the repository",
                )

    return files_content


def get_diff(original_file_content: dict, user_prompt: str) -> str:
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

    Please return a unified diff showing any required changes to the files.
    """

    assistant_response, conversation_history = talk_to_assistant([], diff_prompt)

    reflection_prompt = "Are you sure, or would you like to correct your answer? If you're sure say 'y', otherwise give me the revised unified diff."

    assistant_reflection, conversation_history = talk_to_assistant(
        conversation_history, reflection_prompt
    )

    if assistant_reflection.lower() == "y":
        return assistant_response

    return assistant_reflection


def talk_to_assistant(conversation_history: list, prompt: str) -> str:
    conversation_history.append({"role": "user", "content": prompt})

    response = open_ai_client.chat.completions.create(
        model="gpt-4o-mini", messages=conversation_history
    )

    assistant_message = response.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": assistant_message})

    return assistant_message, conversation_history


@app.post("/generate_diff")
async def generate_diff_for_repo(request: PromptRequest):
    repo_dir = f"./repos/{os.path.basename(request.repoUrl).split('.')[0]}"

    # Clean up any previous repository with the same name
    if os.path.exists(repo_dir):
        shutil.rmtree(repo_dir)

    clone_repo(request.repoUrl, repo_dir)

    files_content = read_files(request.file_paths, repo_dir)

    generated_diff = get_diff(files_content, request.prompt)

    # Clean up repo after use
    shutil.rmtree(repo_dir)

    return JSONResponse(content={"diff": generated_diff})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=api_port)
