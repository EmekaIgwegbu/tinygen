import os
import shutil
import openai
import git
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase_py import create_client, Client
from typing import Optional, List
from fastapi.responses import JSONResponse

app = FastAPI()

# OpenAI configuration
openai.api_key = os.getenv("OPENAI_API_KEY")

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project-ref.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "your-anon-key")

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


class Result(BaseModel):
    repoUrl: str
    prompt: str
    diff: str


class PromptRequest(BaseModel):
    repoUrl: str
    prompt: str
    file_paths: Optional[List[str]] = None  # Specific file paths to modify


# Helper function to clone a GitHub repository
def clone_repo(repo_url: str, repo_dir: str):
    try:
        git.Repo.clone_from(repo_url, repo_dir)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to clone repository: {e}")


# Function to read file contents
def read_files(file_paths: List[str], repo_dir: str) -> dict:
    files_content = {}
    for file_path in file_paths:
        full_path = os.path.join(repo_dir, file_path)
        if os.path.exists(full_path):
            with open(full_path, "r") as file:
                files_content[file_path] = file.read()
        else:
            raise HTTPException(
                status_code=400,
                detail=f"File {file_path} does not exist in the repository",
            )
    return files_content


# Function to interact with GPT to generate the diff directly
def ask_gpt_for_diff(original_file_contents: dict, prompt: str) -> str:
    file_texts = "\n\n".join(
        [
            f"### {file_name}\n{content}"
            for file_name, content in original_file_contents.items()
        ]
    )

    # Prompt GPT to return a diff
    gpt_prompt = f"""
    You are working on the following repository files:
    {file_texts}

    The user has requested the following changes:
    {prompt}

    Please return a unified diff showing the changes to the files.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4", messages=[{"role": "user", "content": gpt_prompt}]
    )
    return response.choices[0].message["content"]


@app.post("/generate_diff")
async def generate_diff_for_repo(request: PromptRequest):
    repo_dir = f"./repos/{os.path.basename(request.repoUrl).split('.')[0]}"

    # Clean up any previous repository with the same name
    if os.path.exists(repo_dir):
        shutil.rmtree(repo_dir)

    clone_repo(request.repoUrl, repo_dir)

    file_paths = (
        request.file_paths if request.file_paths else ["README.md"]
    )  # Default file as an example
    files_content = read_files(file_paths, repo_dir)

    generated_diff = ask_gpt_for_diff(files_content, request.prompt)

    # Clean up repo after use
    shutil.rmtree(repo_dir)

    return JSONResponse(content={"diff": generated_diff})


# Run the FastAPI app using Uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
