class RepoError(Exception):
    def __init__(self, message):
        super().__init__(f"{message}: {self.repo_url}")
