from unittest.mock import create_autospec

import pytest

from acedev.agent import AgentRunner
from acedev.agent.github_agent import (
    GitHubAgent,
    ACEBOTS_APP_USERNAME,
)
from acedev.agent.prompts import (
    pull_request_review_comment_prompt,
    issue_assigned_prompt,
)
from acedev.service.github_service import GitHubService
from acedev.service.model import (
    PullRequest,
    FileChange,
    PullRequestReviewThread,
    PullRequestReviewComment,
    AssistantMessage,
    ToolMessage,
    SystemMessage,
    UserMessage,
    Issue,
    IssueComment,
)
from acedev.tools.tool_provider import ToolProvider

ISSUE_NUMBER = 1
PULL_REQUEST_NUMBER = 1
COMMENT_BODY_1 = ""
COMMENT_ID = 2
TOOL_MESSAGE = ToolMessage(content="content", tool_call_id="id")
ASSISTANT_MESSAGE = AssistantMessage(content="content")
COMMENT_BODY = "body"
USERNAME = "user"
ISSUE = Issue(
    id=1,
    number=1,
    title="title",
    body="body",
    comments=[
        IssueComment(user=USERNAME, body=COMMENT_BODY),
        IssueComment(user=ACEBOTS_APP_USERNAME, body=COMMENT_BODY_1),
    ],
)
ROOT_COMMENT_ID = 1
DIFF_HUNK = "diff_hunk"
PULL_REQUEST = PullRequest(
    title="title",
    body="body",
    head_ref="head",
    url="url",
    files=[FileChange(status="status", filename="filename", diff="diff")],
)


@pytest.fixture
def tool_provider() -> ToolProvider:
    return create_autospec(ToolProvider)


@pytest.fixture
def agent_runner() -> AgentRunner:
    return create_autospec(AgentRunner)


@pytest.fixture
def github_service() -> GitHubService:
    return create_autospec(GitHubService)


@pytest.fixture
def github_agent(
    tool_provider: ToolProvider,
    agent_runner: AgentRunner,
    github_service: GitHubService,
) -> GitHubAgent:
    return GitHubAgent(tool_provider, agent_runner, github_service)


def test_tools(github_agent: GitHubAgent, tool_provider: ToolProvider) -> None:
    assert github_agent.tools() == {
        **tool_provider.code_understanding_tools(),
        **tool_provider.code_editing_tools(),
    }


def test_handle_pull_request_review_comment(
    github_agent: GitHubAgent,
    github_service: GitHubService,
    agent_runner: AgentRunner,
) -> None:
    github_service.get_pull_request.return_value = PULL_REQUEST

    github_service.get_pull_request_review_thread.return_value = (
        PullRequestReviewThread(
            diff_hunk=DIFF_HUNK,
            comments=[
                PullRequestReviewComment(
                    id=ROOT_COMMENT_ID, user=USERNAME, body=COMMENT_BODY, diff_hunk=DIFF_HUNK
                ),
                PullRequestReviewComment(
                    id=COMMENT_ID, user=ACEBOTS_APP_USERNAME, body=COMMENT_BODY_1, diff_hunk=DIFF_HUNK
                ),
            ],
        )
    )

    agent_runner.run.return_value = [
        ASSISTANT_MESSAGE,
        TOOL_MESSAGE,
    ]

    github_agent.handle_pull_request_review_comment(
        comment_id=COMMENT_ID, pull_request_number=PULL_REQUEST_NUMBER
    )

    agent_runner.run.assert_called_once_with(
        [
            SystemMessage(
                content=pull_request_review_comment_prompt(pull_request=PULL_REQUEST)
            ),
            UserMessage(name=USERNAME, content=f"{DIFF_HUNK}\n\n{COMMENT_BODY}"),
            AssistantMessage(content=COMMENT_BODY_1),
        ],
        github_agent.tools(),
    )

    github_service.reply_in_pull_request_thread.assert_called_once_with(
        pull_request_number=PULL_REQUEST_NUMBER,
        root_comment_id=ROOT_COMMENT_ID,
        body=ASSISTANT_MESSAGE.content,
    )


def test_handle_issue_comment(
    github_agent: GitHubAgent,
    github_service: GitHubService,
    agent_runner: AgentRunner,
) -> None:
    github_service.get_issue.return_value = ISSUE
    github_service.issue_is_pull_request.return_value = False

    agent_runner.run.return_value = [
        ASSISTANT_MESSAGE,
        TOOL_MESSAGE,
    ]

    github_agent.handle_issue_comment(issue_number=ISSUE_NUMBER)

    agent_runner.run.assert_called_once_with(
        [
            SystemMessage(content=issue_assigned_prompt(issue=ISSUE)),
            UserMessage(name=USERNAME, content=COMMENT_BODY),
            AssistantMessage(content=COMMENT_BODY_1),
        ],
        github_agent.tools(),
    )

    github_service.create_issue_comment.assert_called_once_with(
        issue_number=ISSUE_NUMBER, body=ASSISTANT_MESSAGE.content
    )


def test_handle_pull_request_comment(
    github_agent: GitHubAgent,
    github_service: GitHubService,
    agent_runner: AgentRunner,
) -> None:
    github_service.get_issue.return_value = ISSUE
    github_service.issue_is_pull_request.return_value = True
    github_service.get_pull_request.return_value = PULL_REQUEST

    agent_runner.run.return_value = [
        ASSISTANT_MESSAGE,
        TOOL_MESSAGE,
    ]

    github_agent.handle_issue_comment(issue_number=ISSUE_NUMBER)

    agent_runner.run.assert_called_once_with(
        [
            SystemMessage(
                content=pull_request_review_comment_prompt(pull_request=PULL_REQUEST)
            ),
            UserMessage(name=USERNAME, content=COMMENT_BODY),
            AssistantMessage(content=COMMENT_BODY_1),
        ],
        github_agent.tools(),
    )

    github_service.create_issue_comment.assert_called_once_with(
        issue_number=ISSUE_NUMBER, body=ASSISTANT_MESSAGE.content
    )


def test_handle_issue_assignment(
    github_agent: GitHubAgent,
    github_service: GitHubService,
    agent_runner: AgentRunner,
) -> None:
    github_service.get_issue.return_value = ISSUE
    agent_runner.run.return_value = [
        ASSISTANT_MESSAGE,
        TOOL_MESSAGE,
    ]

    github_agent.handle_issue_assignment(issue_number=ISSUE_NUMBER)

    agent_runner.run.assert_called_once_with(
        [
            SystemMessage(content=issue_assigned_prompt(issue=ISSUE)),
            UserMessage(name=USERNAME, content=COMMENT_BODY),
            AssistantMessage(content=COMMENT_BODY_1),
        ],
        github_agent.tools(),
    )

    github_service.create_issue_comment.assert_called_once_with(
        issue_number=ISSUE_NUMBER, body=ASSISTANT_MESSAGE.content
    )
