from typing import Sequence, Iterator, Callable

from litellm import completion
from litellm.utils import function_to_dict

from acedev.service.model import ChatMessage, ToolCall, AssistantMessage


class OpenAIService:
    @staticmethod
    def invoke(
        messages: Sequence[ChatMessage],
        model: str = "gpt-4",
        temperature: float = 0,
    ) -> ChatMessage:
        response = completion(
            model=model,
            messages=[message.to_openai_format() for message in messages],
            temperature=temperature,
        )

        message = response.choices[0].message

        return AssistantMessage(
            content=message.content,
        )

    def stream(self, messages: Sequence[ChatMessage]) -> Iterator[ChatMessage]:
        pass

    @staticmethod
    def invoke_with_tools(
        messages: Sequence[ChatMessage],
        tools: dict[str, Callable[[str], str]],
        model: str = "gpt-4",
        temperature: float = 0,
    ) -> AssistantMessage:
        response = completion(
            model=model,
            messages=[message.to_openai_format() for message in messages],
            temperature=temperature,
            tools=[
                {
                    "type": "function",
                    "function": OpenAIService._convert_tools(name, tool),
                }
                for name, tool in tools.items()
            ],
            tool_choice="auto",
        )

        message = response.choices[0].message

        return AssistantMessage(
            content=message.content,
            tool_calls=(
                [
                    ToolCall.from_litellm_format(tool_call)
                    for tool_call in message.tool_calls
                ]
                if message.get("tool_calls") is not None
                else None
            ),
        )

    def stream_with_tools(
        self, messages: Sequence[ChatMessage], tools: dict[str, Callable[[str], str]]
    ) -> Iterator[ChatMessage]:
        pass

    @staticmethod
    def _convert_tools(name: str, func: Callable[[str], str]) -> dict:
        if name == "add_imports":
            return {
                "name": "add_imports",
                "description": "Add import statements in the project file.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "import_statements": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": 'List of import statements, e.g. ["import os", "from datetime import datetime"].',
                        },
                        "path": {"type": "string", "description": "Path to the file."},
                        "branch": {
                            "type": "string",
                            "description": "Name of the branch.",
                        },
                    },
                    "required": ["import_statements", "path", "branch"],
                },
            }

        if name == "replace_imports":
            return {
                "name": "replace_imports",
                "description": "Replace import statements in the project file.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "old_import_statement": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": 'List of old import statements, e.g. ["import os", "from datetime import datetime"].',
                        },
                        "new_import_statements": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": 'List of new import statements, e.g. ["import os", "from datetime import datetime"].',
                        },
                        "path": {"type": "string", "description": "Path to the file."},
                        "branch": {
                            "type": "string",
                            "description": "Name of the branch.",
                        },
                    },
                    "required": [
                        "old_import_statement",
                        "new_import_statements",
                        "path",
                        "branch",
                    ],
                },
            }
        return function_to_dict(func)
