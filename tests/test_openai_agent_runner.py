from unittest.mock import create_autospec

import pytest

from acedev.agent.openai_agent_runner import OpenAIAgentRunner
from acedev.service.model import AssistantMessage, UserMessage, ToolCall, ToolMessage

from acedev.service.openai_service import OpenAIService

MODEL = "gpt-3.5-turbo"
TEMPERATURE = 0.5
TOOL_CALL_ARG = "tool_call1"
TOOL_CALL_ID = "1"
USER_MESSAGE = UserMessage(content="hello")


@pytest.fixture
def openai_service() -> OpenAIService:
    return create_autospec(OpenAIService)


@pytest.fixture
def openai_agent_runner(openai_service) -> OpenAIAgentRunner:
    return OpenAIAgentRunner(
        model=MODEL,
        temperature=TEMPERATURE,
        openai_service=openai_service,
        max_steps=2,
    )


def echo_tool(content: str) -> str:
    return content


TOOLS = {echo_tool.__name__: echo_tool}


def test_agent_exits_the_loop_when_no_tool_calls(
    openai_agent_runner: OpenAIAgentRunner, openai_service: OpenAIService
) -> None:
    assistant_message = AssistantMessage(content="response", tool_calls=[])
    openai_service.invoke_with_tools.return_value = assistant_message
    result = openai_agent_runner.run(messages=[USER_MESSAGE], tools=TOOLS)

    assert result == [assistant_message]


def test_agent_calls_tools(
    openai_agent_runner: OpenAIAgentRunner, openai_service: OpenAIService
) -> None:
    assistant_message_1 = AssistantMessage(
        content="response1",
        tool_calls=[
            ToolCall(
                id=TOOL_CALL_ID, tool="echo_tool", arguments={"content": TOOL_CALL_ARG}
            )
        ],
    )

    assistant_message_2 = AssistantMessage(content="response2", tool_calls=[])

    openai_service.invoke_with_tools.side_effect = [
        assistant_message_1,
        assistant_message_2,
    ]

    result = openai_agent_runner.run(messages=[USER_MESSAGE], tools=TOOLS)

    assert result == [
        assistant_message_1,
        ToolMessage(content=TOOL_CALL_ARG, tool_call_id=TOOL_CALL_ID),
        assistant_message_2,
    ]


def test_agent_exits_the_loop_when_max_steps_reached(
    openai_agent_runner: OpenAIAgentRunner, openai_service: OpenAIService
) -> None:
    assistant_message_1 = AssistantMessage(
        content="response",
        tool_calls=[
            ToolCall(
                id=TOOL_CALL_ID, tool="echo_tool", arguments={"content": TOOL_CALL_ARG}
            )
        ],
    )

    assistant_message_2 = AssistantMessage(
        content="response",
        tool_calls=[
            ToolCall(
                id=TOOL_CALL_ID, tool="echo_tool", arguments={"content": TOOL_CALL_ARG}
            )
        ],
    )

    openai_service.invoke_with_tools.side_effect = [
        assistant_message_1,
        assistant_message_2,
    ]

    result = openai_agent_runner.run(messages=[USER_MESSAGE], tools=TOOLS)

    assert result == [
        assistant_message_1,
        ToolMessage(content=TOOL_CALL_ARG, tool_call_id=TOOL_CALL_ID),
        assistant_message_2,
        ToolMessage(content=TOOL_CALL_ARG, tool_call_id=TOOL_CALL_ID),
        AssistantMessage(content="Help me. I'm stuck 🤖"),
    ]
