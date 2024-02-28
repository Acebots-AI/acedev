from unittest.mock import create_autospec

import pytest

from acedev.service.github_service import GitHubService
from acedev.service.gitrepository import GitRepository
from acedev.service.model import Symbol
from acedev.service.symbol_manipulator import SymbolManipulator
from acedev.service.tool_provider import ToolProvider


@pytest.fixture
def git_repository() -> GitRepository:
    mock = create_autospec(GitRepository)
    mock.default_branch = "main"
    return mock


@pytest.fixture
def github_service() -> GitHubService:
    return create_autospec(GitHubService)


@pytest.fixture
def symbol_manipulator() -> SymbolManipulator:
    return create_autospec(SymbolManipulator)


@pytest.fixture
def tool_provider(
    git_repository: GitRepository,
    github_service: GitHubService,
    symbol_manipulator: SymbolManipulator,
) -> ToolProvider:
    return ToolProvider(git_repository, github_service, symbol_manipulator)


def test_get_default_branch(
    tool_provider: ToolProvider, git_repository: GitRepository
) -> None:
    assert tool_provider.get_default_branch() == "main"


def test_get_project_outline(
    tool_provider: ToolProvider,
    git_repository: GitRepository,
    symbol_manipulator: SymbolManipulator,
) -> None:
    git_repository.branch_exists.return_value = True
    symbol_manipulator.get_project_outline.return_value = "project_outline"
    assert tool_provider.get_project_outline() == "project_outline"


def test_get_project_outline_branch_does_not_exist(
    tool_provider: ToolProvider,
    git_repository: GitRepository,
    symbol_manipulator: SymbolManipulator,
) -> None:
    git_repository.branch_exists.return_value = False
    branch = "dev"
    assert (
        tool_provider.get_project_outline(branch=branch)
        == f"Failed to get project outline: {branch=} does not exist."
    )


def test_get_symbol(
    tool_provider: ToolProvider,
    git_repository: GitRepository,
    symbol_manipulator: SymbolManipulator,
) -> None:
    symbol_manipulator.get_symbol.return_value = Symbol(content="symbol", path="path")
    assert tool_provider.get_symbol("symbol", "path") == "symbol"


def test_get_symbol_branch_does_not_exist(
    tool_provider: ToolProvider,
    git_repository: GitRepository,
    symbol_manipulator: SymbolManipulator,
) -> None:
    git_repository.branch_exists.return_value = False
    branch = "dev"
    symbol = "symbol"
    path = "path"
    assert (
        tool_provider.get_symbol(symbol, path, branch=branch)
        == f"Failed to get {symbol} from {path}: {branch=} does not exist."
    )