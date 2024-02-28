import logging
from typing import Generator, Optional

from github.Repository import Repository

from acedev.service.model import File

logger = logging.getLogger(__name__)

# Currently optimized for Python projects
FILES_IGNORE = [
    ".gitignore",
    "Dockerfile",
    ".yaml",
    ".yml",
    ".md",
    ".toml",
    ".txt",
    ".in",
    ".cfg",
    "__init__.py",
    ".ini",
    "poetry.lock",
    ".template",
    ".conf",
    ".xml",
]


class GitRepository:
    def __init__(self, github_repo: Repository) -> None:
        self.github_repo = github_repo
        self.default_branch = github_repo.default_branch
        self.full_name = github_repo.full_name
        self.language = (github_repo.language or
                         max(github_repo.get_languages(), key=github_repo.get_languages().get)).lower()

    def __repr__(self) -> str:
        return f"Project({self.full_name})"

    def get_files(
        self, path: str = "", branch: Optional[str] = None
    ) -> Generator[File, None, None]:
        for file in self.github_repo.get_contents(path, branch or self.default_branch):  # type: ignore[union-attr]
            if file.name.startswith("."):
                continue

            # TODO: handle images and other non-textual files
            if any(pattern in file.name for pattern in FILES_IGNORE):
                continue

            if file.type == "dir":
                yield from self.get_files(path=file.path, branch=branch)
                continue

            logger.info(
                f"Processing file: {file.path}. Encoding: {file.encoding}. Size: {file.size}"
            )
            content = file.decoded_content
            yield File(path=file.path, content=content.decode("utf-8"),)

    def get_file(self, path: str, branch: Optional[str] = None) -> File:
        # TODO: handle missing file
        file = self.github_repo.get_contents(path, branch or self.default_branch)  # type: ignore[union-attr]
        content = file.decoded_content
        return File(path=file.path, content=content.decode("utf-8"),)

    def create_new_branch(self, branch: str) -> str:
        logger.info(f"Creating new branch: {branch}")

        if self.branch_exists(branch):
            raise GitRepositoryException(f"Branch already exists: {branch}")

        git_ref = self.github_repo.create_git_ref(
            ref=f"refs/heads/{branch}",
            sha=self.github_repo.get_branch(self.default_branch).commit.sha,
        )

        return git_ref.ref

    def branch_exists(self, branch: str) -> bool:
        return branch in [_branch.name for _branch in self.github_repo.get_branches()]

    def update_file(self, file: File, branch: str) -> None:
        logger.info(f"Updating file: {file.path}")

        self.github_repo.update_file(
            path=file.path,
            message=f"Update {file.path}",
            content=file.content,
            sha=self.github_repo.get_contents(path=file.path, ref=branch).sha,  # type: ignore[union-attr]
            branch=branch,
        )

    def create_file(self, file: File, branch: str) -> None:
        logger.info(f"Creating file: {file.path}")

        self.github_repo.create_file(
            path=file.path,
            message=f"Create {file.path}",
            content=file.content,
            branch=branch,
        )

    def delete_file(self, file: File, branch: str) -> None:
        logger.info(f"Deleting file: {file.path}")

        self.github_repo.delete_file(
            path=file.path,
            message=f"Delete {file.path}",
            sha=self.github_repo.get_contents(path=file.path, ref=branch).sha,  # type: ignore[union-attr]
            branch=branch,
        )


class GitRepositoryException(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
