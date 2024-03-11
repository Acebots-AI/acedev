import pytest
from unittest.mock import MagicMock, create_autospec

from github.Branch import Branch
from github.ContentFile import ContentFile
from github.Repository import Repository

from acedev.service.git_repository import GitRepository, GitRepositoryException
from acedev.service.model import File


@pytest.fixture
def github_repo() -> Repository:
    mock = create_autospec(spec=Repository)
    mock.default_branch = "main"
    mock.full_name = "octocat/Hello-World"
    mock.language = "python"
    return mock


@pytest.fixture
def gitrepo(github_repo: Repository) -> GitRepository:
    return GitRepository(github_repo)


def test_init(gitrepo: GitRepository, github_repo: Repository) -> None:
    assert gitrepo.github_repo is github_repo
    assert gitrepo.default_branch == "main"
    assert gitrepo.full_name == "octocat/Hello-World"
    assert gitrepo.language == "python"


def test_init_no_language(github_repo: Repository) -> None:
    github_repo.language = None
    github_repo.get_languages.return_value = {"python": 100, "javascript": 50}
    gitrepo = GitRepository(github_repo)
    assert gitrepo.language == "python"


def test_get_files_default_branch(
    gitrepo: GitRepository, github_repo: Repository
) -> None:
    file = File(path="file1.py", content="content")
    ignored_file = File(path=".gitignore", content="content")

    github_repo.get_contents.return_value = [
        mock_file(file),
        mock_file(ignored_file),
    ]

    files = list(gitrepo.get_files())

    github_repo.get_contents.assert_called_with("", gitrepo.default_branch)
    assert files == [file]


def test_get_files_custom_branch(
    gitrepo: GitRepository, github_repo: Repository
) -> None:
    file = File(path="file1.py", content="content")
    ignored_file = File(path=".gitignore", content="content")

    github_repo.get_contents.return_value = [
        mock_file(file),
        mock_file(ignored_file),
    ]

    files = list(gitrepo.get_files(branch="dev"))

    github_repo.get_contents.assert_called_with("", "dev")
    assert files == [file]


def test_get_files_from_subdir(gitrepo: GitRepository, github_repo: Repository) -> None:
    file = File(path="subdir/file3.py", content="content")
    github_repo.get_contents.side_effect = lambda path, branch: {
        "": [
            mock_dir("subdir"),
        ],
        "subdir": [
            mock_file(file),
        ],
    }.get(path, [])

    files = list(gitrepo.get_files(path=""))

    github_repo.get_contents.assert_any_call("", gitrepo.default_branch)
    github_repo.get_contents.assert_any_call("subdir", gitrepo.default_branch)

    assert files == [file]


def test_get_file(gitrepo: GitRepository, github_repo: Repository) -> None:
    file = File(path="file1.py", content="content")

    github_repo.get_contents.return_value = mock_file(file)

    result = gitrepo.get_file("file1.py")

    github_repo.get_contents.assert_called_with("file1.py", gitrepo.default_branch)
    assert result == file


def test_get_file_custom_branch(
    gitrepo: GitRepository, github_repo: Repository
) -> None:
    file = File(path="file1.py", content="content")

    github_repo.get_contents.return_value = mock_file(file)

    result = gitrepo.get_file("file1.py", branch="dev")

    github_repo.get_contents.assert_called_with("file1.py", "dev")
    assert result == file


def test_create_new_branch(gitrepo: GitRepository, github_repo: Repository) -> None:
    github_repo.get_branch.return_value = MagicMock(commit=MagicMock(sha="sha"))
    gitrepo.create_new_branch("dev")

    github_repo.create_git_ref.assert_called_with(ref="refs/heads/dev", sha="sha")


def test_create_new_branch_exists(
    gitrepo: GitRepository, github_repo: Repository
) -> None:
    mock_branch = create_autospec(Branch)
    mock_branch.name = "dev"
    github_repo.get_branches.return_value = [mock_branch]
    with pytest.raises(GitRepositoryException):
        gitrepo.create_new_branch("dev")


def test_branch_exists(gitrepo: GitRepository, github_repo: Repository) -> None:
    mock_branch = create_autospec(Branch)
    mock_branch.name = "dev"
    github_repo.get_branches.return_value = [mock_branch]

    assert gitrepo.branch_exists("dev")
    assert not gitrepo.branch_exists("main")


def test_update_file(gitrepo: GitRepository, github_repo: Repository) -> None:
    file = File(path="file1.py", content="content")
    github_repo.get_contents.return_value = MagicMock(sha="sha")
    gitrepo.update_file(file, "dev")

    github_repo.update_file.assert_called_with(
        path="file1.py",
        message="Update file1.py",
        content="content",
        sha="sha",
        branch="dev",
    )


def test_create_file(gitrepo: GitRepository, github_repo: Repository) -> None:
    file = File(path="file1.py", content="content")
    gitrepo.create_file(file, "dev")

    github_repo.create_file.assert_called_with(
        path="file1.py",
        message="Create file1.py",
        content="content",
        branch="dev",
    )


def test_delete_file(gitrepo: GitRepository, github_repo: Repository) -> None:
    file = File(path="file1.py", content="content")
    github_repo.get_contents.return_value = MagicMock(sha="sha")
    gitrepo.delete_file(file, "dev")

    github_repo.delete_file.assert_called_with(
        path="file1.py",
        message="Delete file1.py",
        sha="sha",
        branch="dev",
    )


def mock_file(file: File) -> ContentFile:
    mock = create_autospec(ContentFile)
    mock.path = file.path
    mock.name = file.path.split("/")[-1]
    mock.type = "file"
    mock.decoded_content = file.content.encode("utf-8")
    return mock


def mock_dir(path: str) -> ContentFile:
    mock = create_autospec(ContentFile)
    mock.type = "dir"
    mock.path = path
    mock.name = path.split("/")[-1]
    return mock
