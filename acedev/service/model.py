import json
from typing import Sequence, Any, Optional

from github.PullRequest import PullRequest as GitHubPullRequest
from github.PullRequestComment import PullRequestComment
from litellm.utils import ChatCompletionMessageToolCall
from pydantic import BaseModel, Field, ConfigDict


class File(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: str = Field(description="Path to the file in the repository")
    content: str = Field(description="Content of the file")


class FileChange(BaseModel):
    status: str
    filename: str
    diff: str


class PullRequest(BaseModel):
    title: str
    body: str
    head_ref: str
    url: str
    files: Sequence[FileChange]

    @staticmethod
    def from_github(pull_request: GitHubPullRequest):
        return PullRequest(
            title=pull_request.title,
            body=pull_request.body,
            head_ref=pull_request.head.ref,
            url=pull_request.html_url,
            files=[
                FileChange(
                    status=file.status, filename=file.filename, diff=file.patch
                )
                for file in pull_request.get_files()
            ],
        )


class PullRequestReviewComment(BaseModel):
    id: int
    user: str
    body: str
    diff_hunk: str

    @classmethod
    def from_github(cls, comment: PullRequestComment) -> "PullRequestReviewComment":
        return PullRequestReviewComment(
            id=comment.id,
            user=comment.user.login,
            body=comment.body,
            diff_hunk=comment.diff_hunk
        )


class PullRequestReviewThread(BaseModel):
    diff_hunk: str
    comments: list[PullRequestReviewComment]


class IssueComment(BaseModel):
    user: str
    body: str


class Issue(BaseModel):
    id: int
    number: int
    title: str
    body: str
    comments: Sequence[IssueComment]


class Symbol(BaseModel):
    model_config = ConfigDict(frozen=True)

    content: str
    path: str


class ToolCall(BaseModel):
    id: str
    tool: str
    arguments: dict[str, Any]
    type: str = "function"

    def to_openai_format(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "function": {
                "name": self.tool,
                "arguments": json.dumps(self.arguments)
            }
        }

    @classmethod
    def from_openai_format(cls, data: dict[str, Any]) -> "ToolCall":
        return ToolCall(
            id=data["id"],
            tool=data["function"]["name"],
            arguments=json.loads(data["function"]["arguments"])
        )

    @classmethod
    def from_litellm_format(cls, data: ChatCompletionMessageToolCall) -> "ToolCall":
        return ToolCall(
            id=data.id,
            tool=data.function.name,
            arguments=json.loads(data.function.arguments)
        )

    def __str__(self):
        indented_arguments = "\n    ".join(json.dumps(self.arguments, indent=4).splitlines())
        return f"Calling {BOLD}{self.tool}{RESET} with {indented_arguments}"


# ANSI escape codes for formatting and color
GREEN = '\033[92m'  # Green text
BOLD = '\033[1m'   # Bold text
RESET = '\033[0m'  # Reset to default


class ChatMessage(BaseModel):
    role: str
    content: str

    def to_openai_format(self) -> dict:
        raise NotImplementedError

    @classmethod
    def from_openai_format(cls, data: dict[str, Any]) -> "ChatMessage":
        raise NotImplementedError

    def __str__(self):
        indented_content = "\n    ".join(self.content.splitlines())
        return f"{BOLD}{GREEN}{self.role}{RESET}: {indented_content}"


class SystemMessage(ChatMessage):
    role: str = "system"

    def to_openai_format(self) -> dict:
        return {
            "role": self.role,
            "content": self.content
        }

    @classmethod
    def from_openai_format(cls, data: dict[str, Any]) -> "SystemMessage":
        return SystemMessage(
            role=data["role"],
            content=data["content"]
        )


class UserMessage(ChatMessage):
    name: Optional[str] = None

    role: str = "user"

    def to_openai_format(self) -> dict:
        output = {
            "role": self.role,
            "content": self.content
        }

        if self.name is not None:
            output["name"] = self.name

        return output

    @classmethod
    def from_openai_format(cls, data: dict[str, Any]) -> "UserMessage":
        return UserMessage(
            role=data["role"],
            content=data["content"],
            name=data.get("name")
        )


class AssistantMessage(ChatMessage):
    content: Optional[str] = None
    tool_calls: Optional[list[ToolCall]] = None

    role: str = "assistant"

    def to_openai_format(self) -> dict:
        output = {
            "role": self.role,
            "content": self.content
        }

        if self.tool_calls is not None:
            output["tool_calls"] = [tool_call.to_openai_format() for tool_call in self.tool_calls]

        return output

    @classmethod
    def from_openai_format(cls, data: dict[str, Any]) -> "AssistantMessage":
        return AssistantMessage(
            role=data["role"],
            content=data["content"],
            tool_calls=[ToolCall.from_openai_format(tool_call) for tool_call in data["tool_calls"]] if data.get("tool_calls") else None,
        )

    def __str__(self):
        indented_content = "\n    ".join(self.content.splitlines()) if self.content else "Calling tools..."
        tool_calls = "\n    ".join(str(tool_call) for tool_call in self.tool_calls) if self.tool_calls else ""
        return f"{BOLD}{GREEN}{self.role}{RESET}: {indented_content + ' ' + tool_calls}"


class ToolMessage(ChatMessage):
    tool_call_id: str

    role: str = "tool"

    def to_openai_format(self) -> dict:
        return {
            "tool_call_id": self.tool_call_id,
            "role": self.role,
            "content": self.content
        }

    @classmethod
    def from_openai_format(cls, data: dict[str, Any]) -> "ToolMessage":
        return ToolMessage(
            tool_call_id=data["tool_call_id"],
            role=data["role"],
            content=data["content"]
        )


class AgentCompletionContext(BaseModel):
    repo: str
    owner: str


class AgentCompletionRequest(BaseModel):
    messages: list[ChatMessage]
    # context: AgentCompletionContext
