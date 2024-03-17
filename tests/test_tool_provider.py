from unittest.mock import create_autospec

import pytest

from acedev.agent.coding_agent import CodingAgent, CodingAgentException
from acedev.service.github_service import GitHubService
from acedev.service.git_repository import GitRepository
from acedev.service.model import File, Symbol
from acedev.tools.code_editor import CodeEditor
from acedev.tools.symbol_manipulator import SymbolManipulator
from acedev.tools.tool_provider import ToolProvider


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
def code_editor() -> CodeEditor:
    return create_autospec(CodeEditor)


@pytest.fixture
def coding_agent() -> CodingAgent:
    return create_autospec(CodingAgent)


@pytest.fixture
def file_mock() -> File:
    return File(path="test_file.py", content="print('Hello, World!')")


@pytest.fixture
def tool_provider(
    git_repository: GitRepository,
    github_service: GitHubService,
    symbol_manipulator: SymbolManipulator,
    code_editor: CodeEditor,
    coding_agent: CodingAgent,
) -> ToolProvider:
    return ToolProvider(
        git_repository, github_service, symbol_manipulator, code_editor, coding_agent
    )


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


def test_request_edit_happy_path(
    tool_provider: ToolProvider,
    git_repository: GitRepository,
    coding_agent: CodingAgent,
    file_mock: File,
) -> None:
    branch = "feature-branch"
    path = "module/submodule/file.py"
    instruction = "Please update the greeting message."
    git_repository.branch_exists.return_value = True
    git_repository.get_file.return_value = file_mock
    coding_agent.edit_file.return_value = file_mock
    git_repository.update_file.return_value = (
        None  # Assuming update_file returns nothing on success
    )

    result = tool_provider.request_edit(
        branch=branch, path=path, instruction=instruction
    )

    assert result == f"Edited {path}. The new file content is:\n\n{file_mock.content}"
    git_repository.get_file.assert_called_once_with(path=path, branch=branch)
    coding_agent.edit_file.assert_called_once_with(
        instructions=instruction, file=file_mock
    )
    git_repository.update_file.assert_called_once_with(file=file_mock, branch=branch)


def test_request_edit_default_branch(
    tool_provider: ToolProvider,
    git_repository: GitRepository,
) -> None:
    branch = "main"
    path = "module/submodule/file.py"
    instruction = "Please update the greeting message."
    git_repository.default_branch = branch

    result = tool_provider.request_edit(
        branch=branch, path=path, instruction=instruction
    )

    assert result == f"Failed to edit {path}: {branch=} is protected."


def test_request_edit_branch_does_not_exist(
    tool_provider: ToolProvider,
    git_repository: GitRepository,
) -> None:
    branch = "nonexistent-branch"
    path = "module/submodule/file.py"
    instruction = "Please update the greeting message."
    git_repository.branch_exists.return_value = False

    result = tool_provider.request_edit(
        branch=branch, path=path, instruction=instruction
    )

    assert result == f"Failed to edit {path}: {branch=} does not exist."


def test_request_edit_path_does_not_exist(
    tool_provider: ToolProvider,
    git_repository: GitRepository,
) -> None:
    branch = "feature-branch"
    path = "module/submodule/nonexistent_file.py"
    instruction = "Please update the greeting message."
    git_repository.branch_exists.return_value = True
    git_repository.get_file.return_value = None

    result = tool_provider.request_edit(
        branch=branch, path=path, instruction=instruction
    )

    assert result == f"Failed to edit {path}: path does not exist."


def test_request_edit_coding_agent_exception(
    tool_provider: ToolProvider,
    git_repository: GitRepository,
    coding_agent: CodingAgent,
    file_mock: File,
) -> None:
    branch = "feature-branch"
    path = "module/submodule/file.py"
    instruction = "Please update the greeting message."
    git_repository.branch_exists.return_value = True
    git_repository.get_file.return_value = file_mock
    coding_agent.edit_file.side_effect = CodingAgentException("Test Exception")

    result = tool_provider.request_edit(
        branch=branch, path=path, instruction=instruction
    )

    assert "Failed to edit" in result and "Test Exception" in result
    git_repository.get_file.assert_called_once_with(path=path, branch=branch)
    coding_agent.edit_file.assert_called_once_with(
        instructions=instruction, file=file_mock
    )
