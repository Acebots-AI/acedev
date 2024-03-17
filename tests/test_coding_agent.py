import pytest
from unittest.mock import create_autospec
from acedev.agent.coding_agent import CodingAgent, CodingAgentException
from acedev.service.model import File, AssistantMessage
from acedev.tools.code_editor import CodeEditor, CodeEditorException
from acedev.service.openai_service import OpenAIService


@pytest.fixture
def code_editor_mock() -> CodeEditor:
    return create_autospec(CodeEditor)


@pytest.fixture
def openai_service_mock() -> OpenAIService:
    return create_autospec(OpenAIService)


@pytest.fixture
def file_mock() -> File:
    return File(path="test_file.py", content="print('Hello, World!')")


@pytest.fixture
def coding_agent(
    code_editor_mock: CodeEditor, openai_service_mock: OpenAIService
) -> CodingAgent:
    return CodingAgent(
        code_editor=code_editor_mock,
        openai_service=openai_service_mock,
        model="test-model",
        temperature=0.7,
        max_retries=3,
    )


def test_edit_file_happy_path(
    coding_agent: CodingAgent,
    openai_service_mock: OpenAIService,
    code_editor_mock: CodeEditor,
    file_mock: File,
) -> None:
    openai_service_mock.invoke.return_value = AssistantMessage(
        content="```diff\n+ print('Goodbye, World!')\n```"
    )
    code_editor_mock.apply_diff.return_value = File(
        path="test_file.py", content="print('Goodbye, World!')"
    )

    edited_file = coding_agent.edit_file(
        "Change greeting to 'Goodbye, World!'", file_mock
    )

    assert edited_file.content == "print('Goodbye, World!')"
    openai_service_mock.invoke.assert_called_once()
    code_editor_mock.apply_diff.assert_called_once_with(
        "\n+ print('Goodbye, World!')\n", file_mock
    )


def test_edit_file_no_diff_found(
    coding_agent: CodingAgent, openai_service_mock: OpenAIService, file_mock: File
) -> None:
    openai_service_mock.invoke.return_value = AssistantMessage(content="No diff found.")

    with pytest.raises(CodingAgentException):
        coding_agent.edit_file("Change greeting to 'Goodbye, World!'", file_mock)

    assert openai_service_mock.invoke.call_count == coding_agent.max_retries


def test_edit_file_multiple_diffs_found(
    coding_agent: CodingAgent, openai_service_mock: OpenAIService, file_mock: File
) -> None:
    openai_service_mock.invoke.return_value = AssistantMessage(
        content="```diff\n+ print('Goodbye, World!')\n```\n```diff\n- print('Hello, World!')\n```"
    )

    with pytest.raises(CodingAgentException):
        coding_agent.edit_file("Change greeting to 'Goodbye, World!'", file_mock)

    assert openai_service_mock.invoke.call_count == coding_agent.max_retries


def test_edit_file_code_editor_exception(
    coding_agent: CodingAgent,
    openai_service_mock: OpenAIService,
    code_editor_mock: CodeEditor,
    file_mock: File,
) -> None:
    openai_service_mock.invoke.return_value = AssistantMessage(
        content="```diff\n+ print('Goodbye, World!')\n```"
    )
    code_editor_mock.apply_diff.side_effect = CodeEditorException("Test Exception")

    with pytest.raises(CodingAgentException):
        coding_agent.edit_file("Change greeting to 'Goodbye, World!'", file_mock)

    assert openai_service_mock.invoke.call_count == coding_agent.max_retries
    assert code_editor_mock.apply_diff.call_count == coding_agent.max_retries
