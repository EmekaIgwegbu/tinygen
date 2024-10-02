import git
import hashlib
import logging
import os
from tinygen.exceptions.repo_error import RepoError

logger = logging.getLogger(__name__)

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

IGNORED_DIRECTORIES = {"node_modules", "vendor", ".git", "build", "dist"}


class Repo:
    def __init__(self, repo_url: str):
        self.repo_url = repo_url
        # Generate a unique hash to avoid clashing repo directory names
        url_hash = hashlib.sha256(repo_url.encode()).hexdigest()[:6]
        self.repo_dir = f"./repos/{os.path.basename(repo_url).split('.')[0]}_{url_hash}"
        self.repo = self.pull_latest(repo_url)

    @staticmethod
    def __ignore_dir_path(dir_path: str) -> bool:
        _, dir_name = os.path.split(dir_path)
        return dir_name in IGNORED_DIRECTORIES

    def pull_latest(self, repo_url: str) -> git.Repo:
        if not os.path.exists(self.repo_dir):
            try:
                return git.Repo.clone_from(repo_url, self.repo_dir)
            except Exception as e:
                raise RepoError(
                    message=f"Failed to clone repository {self.repo_url}: {e}"
                )
        else:
            try:
                repo = git.Repo(self.repo_dir)
                repo.remotes.origin.pull()
            except Exception as e:
                raise RepoError(
                    message=f"Failed to pull from remote {self.repo_url}: {e}"
                )

    @staticmethod
    def is_code_file(file_path: str) -> bool:
        # Check if the file has a valid code extension
        _, ext = os.path.splitext(file_path)
        return ext in CODE_FILE_EXTENSIONS

    def read_all_files(self) -> dict[str, str]:
        """Reads all code files within the repo."""
        file_content = {}

        for dir_path, sub_dir_names, file_names in os.walk(self.repo_dir):
            if Repo.__ignore_dir_path(dir_path):
                continue

            for file in file_names:
                full_path = os.path.join(dir_path, file)
                if Repo.is_code_file(full_path):
                    try:
                        with open(full_path, "r") as file:
                            # Store file content, with path relative to the repo_dir
                            relative_path = os.path.relpath(full_path, self.repo_dir)
                            file_content[relative_path] = file.read()
                    except Exception as e:
                        raise RepoError(
                            message=f"Could not read file {full_path}: {str(e)}",
                        )

        return file_content

    def read_files(self, file_paths: list[str] | None) -> dict[str, str]:
        """Reads the files specified in file_paths. If file_paths is empty or None then
        all code files in the repo are read."""
        file_content = {}

        # Real all relevant files in the repo
        if not file_paths:
            return self.read_all_files()

        # Read only specified files
        else:
            for file_path in file_paths:
                full_path = os.path.join(self.repo_dir, file_path)
                if os.path.exists(full_path):
                    try:
                        with open(full_path, "r") as file:
                            file_content[file_path] = file.read()
                    except Exception as e:
                        raise RepoError(
                            message=f"Could not read file {file_path}: {str(e)}",
                        )
                else:
                    raise RepoError(
                        message=f"File {file_path} does not exist in the repository",
                    )

        return file_content
