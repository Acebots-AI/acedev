import logging
import os
from typing import Annotated, Any, Optional

import fastapi
from fastapi import BackgroundTasks, Body, Depends, Header
from github import GithubIntegration
from github.Issue import Issue as GithubIssue
from github.PullRequest import PullRequest as GithubPullRequest
from pydantic import BaseModel
from typing_extensions import Sequence

from acedev.api.dependencies import get_ghe_client, get_openai_agent
from acedev.agent.openai_agent import OpenAIAgent
from acedev.service.model import ChatMessage, AgentCompletionRequest, AgentCompletionContext, AssistantMessage, \
    FileChange, \
    SystemMessage, UserMessage, PullRequest as mPullRequest
from acedev.service.project import Project
from acedev.utils.prompts import prompt

router = fastapi.APIRouter()
logger = logging.getLogger(__name__)

ACEBOTS_APP_USERNAME = os.getenv("GITHUB_APP_USERNAME", "acebots-ai[bot]")
ACEDEV_USERNAME = os.getenv("GITHUB_BOT_USERNAME", "acedev-ai")


class User(BaseModel):
    id: int
    login: str


class PullRequestReviewComment(BaseModel):
    id: int
    body: str
    diff_hunk: str
    in_reply_to_id: Optional[int] = None
    commit_id: str
    user: User


class PullRequestHead(BaseModel):
    ref: str


class PullRequest(BaseModel):
    id: int
    number: int
    title: str
    body: Optional[str] = None
    html_url: str
    head: PullRequestHead


class Repository(BaseModel):
    full_name: str


class Installation(BaseModel):
    id: int


class PullRequestReviewCommentPayload(BaseModel):
    """
    Payload for pull_request_review_comment event.
    See https://docs.github.com/en/webhooks/webhook-events-and-payloads?actionType=created#pull_request_review_comment
    """

    action: str
    comment: PullRequestReviewComment
    installation: Installation
    pull_request: PullRequest
    repository: Repository


class PullRequestRef(BaseModel):
    url: str
    html_url: str


class Issue(BaseModel):
    id: int
    number: int
    title: str
    body: str
    pull_request: Optional[PullRequestRef] = None
    html_url: str


class IssueComment(BaseModel):
    id: int
    body: str


class IssueCommentPayload(BaseModel):
    """
    Payload for issue_comment event related to a comment on an issue or pull request.
    See https://docs.github.com/en/webhooks/webhook-events-and-payloads#issue_comment
    """

    action: str
    comment: IssueComment
    installation: Installation
    issue: Issue
    repository: Repository


class Assignee(BaseModel):
    login: str


class IssueAssignedPayload(BaseModel):
    """
    Payload for issue event with action = assigned.
    See https://docs.github.com/en/webhooks/webhook-events-and-payloads#issues
    """

    action: str
    assignee: Assignee
    issue: Issue
    installation: Installation
    repository: Repository


@router.post(
    "/webhook",
    summary="Webhook for Github events.",
    responses={"202": {"description": "Event accepted"}},
)
def webhook(
        x_github_event: Annotated[str, Header()],
        payload: Annotated[dict[Any, Any], Body()],
        background_tasks: BackgroundTasks,
        ghe_client: GithubIntegration = Depends(get_ghe_client),
        openai_agent: OpenAIAgent = Depends(get_openai_agent),
) -> fastapi.Response:
    logger.info(f"Received {x_github_event=}")
    logger.debug(f"{payload=}")

    match x_github_event:
        case "pull_request_review_comment":
            review_comment = PullRequestReviewCommentPayload(**payload)
            if review_comment.comment.body.startswith(f"@{ACEDEV_USERNAME}") and review_comment.action in [
                "created",
                "edited",
            ]:
                background_tasks.add_task(
                    handle_pull_request_review_comment,
                    review_comment,
                    ghe_client,
                    openai_agent
                )
        case "issue_comment":
            issue_comment = IssueCommentPayload(**payload)

            if issue_comment.comment.body.startswith(f"@{ACEDEV_USERNAME}") and issue_comment.action in [
                "created",
                "edited",
            ]:
                background_tasks.add_task(
                    handle_issue_comment, issue_comment, ghe_client, openai_agent
                )
        case "issues":
            if payload.get("action", None) == "assigned":
                issue = IssueAssignedPayload(**payload)

                if issue.assignee.login == ACEDEV_USERNAME:
                    background_tasks.add_task(
                        handle_assigned_issue, issue, ghe_client, openai_agent
                    )
        case _:
            logger.warning(f"Unexpected event: {x_github_event}")

    return fastapi.Response(status_code=202)


def handle_pull_request_review_comment(
        payload: PullRequestReviewCommentPayload,
        ghe_client: GithubIntegration,
        openai_agent: OpenAIAgent,
) -> None:
    try:
        repo = ghe_client.get_github_for_installation(
            payload.installation.id
        ).get_repo(payload.repository.full_name)
        project = Project(repo)
        pull_request_number = payload.pull_request.number
        pull_request = repo.get_pull(pull_request_number)
        pull_request_files = project.get_pull_request_files(pull_request_number)
        messages: list[ChatMessage] = [SystemMessage(
            content=_pull_request_review_comment_prompt(project.get_pull_request(pull_request_number),
                                                        pull_request_files))]
        messages.extend(_message_history_from_review_comment(payload.comment, pull_request))

        logger.info(
            f"Replying to PR comment for PR#{pull_request_number} in {repo.full_name}. Current thread: \n{messages}"
        )

        completion_request = AgentCompletionRequest(
            messages=messages,
            context=AgentCompletionContext(repo=repo.full_name, owner=repo.owner.login))

        tools = {**project.code_understanding_tools(), **project.code_editing_tools()}

        for message in openai_agent.run(completion_request, tools):
            logger.info(f"\nMessage from agent:\n{message}")
            if isinstance(message, AssistantMessage) and message.content:
                pull_request.create_review_comment_reply(
                    comment_id=payload.comment.in_reply_to_id or payload.comment.id,
                    body=message.content,
                )
    except Exception:
        logger.exception(
            f"Failed to handle pull request review comment: {payload=}"
        )


def handle_issue_comment(
        payload: IssueCommentPayload,
        ghe_client: GithubIntegration,
        openai_agent: OpenAIAgent,
) -> None:
    try:
        repo = ghe_client.get_github_for_installation(
            payload.installation.id
        ).get_repo(payload.repository.full_name)

        project = Project(repo)
        issue = repo.get_issue(payload.issue.number)
        messages: list[ChatMessage] = []

        if payload.issue.pull_request:
            pull_request_number = payload.issue.number
            pull_request = repo.get_pull(pull_request_number)
            pull_request_files = project.get_pull_request_files(pull_request_number)
            messages.append(SystemMessage(
                content=_pull_request_review_comment_prompt(project.get_pull_request(pull_request_number),
                                                            pull_request_files)))
            messages.extend(_messages_from_pull_request(pull_request))
        else:
            messages.append(SystemMessage(content=_issue_assigned_prompt(payload)))
            messages.extend(_messages_from_issue(issue))

        logger.info(
            f"Replying to Issue#{payload.issue.number} in {repo.full_name}. Message history: \n{messages}"
        )

        completion_request = AgentCompletionRequest(
            messages=messages,
            context=AgentCompletionContext(repo=repo.full_name, owner=repo.owner.login))

        tools = {**project.code_understanding_tools(), **project.code_editing_tools()}

        for message in openai_agent.run(completion_request, tools):
            logger.info(f"\nMessage from agent:\n{message}")
            if isinstance(message, AssistantMessage) and message.content:
                issue.create_comment(
                    body=message.content
                )
    except Exception:
        logger.exception(f"Failed to handle issue comment: {payload=}")


def handle_assigned_issue(
        payload: IssueAssignedPayload,
        ghe_client: GithubIntegration,
        openai_agent: OpenAIAgent,
) -> None:
    try:
        repo = ghe_client.get_github_for_installation(
            payload.installation.id
        ).get_repo(payload.repository.full_name)
        project = Project(repo)
        issue = repo.get_issue(payload.issue.number)

        messages = [SystemMessage(content=_issue_assigned_prompt(payload))] + _messages_from_issue(issue)

        logger.info(
            f"Handling assigned issue#{payload.issue.number} in {repo.full_name}. Messages: \n{messages}"
        )

        completion_request = AgentCompletionRequest(
            messages=messages,
            context=AgentCompletionContext(repo=repo.full_name, owner=repo.owner.login))

        for message in openai_agent.run(completion_request, project.code_understanding_tools()):
            logger.info(f"\nMessage from agent:\n{message}")
            if isinstance(message, AssistantMessage) and message.content:
                issue.create_comment(
                    body=message.content
                )
    except Exception:
        logger.exception(f"Failed to handle assigned issue: {payload=}")


@prompt
def _issue_assigned_prompt(payload: IssueAssignedPayload) -> None:
    """
    You are AceDev, an AI assistant for software engineering.

    You have just been assigned with a GitHub Issue.

    Issue title: {{ payload.issue.title }}

    Issue body:
    {{ payload.issue.body }}

    Here's what I expect from you now:
    1. Check out the high-level overview of the project.
    2. Expand any functions or classes if needed.
    3. Give me a 4-5 bullet-point plan for implementation.
    """


@prompt
def _pull_request_review_comment_prompt(pull_request: mPullRequest, files: Sequence[FileChange]) -> None:
    """
    You are AceDev, an AI member of the software engineering team. You have opened a pull
    request and are waiting for a review. When a review comment is posted, you should reply
    to the comment and update the code if needed. You should also
    ask for clarification if you don't understand the comment.

    Pull request title: {{ pull_request.title }}

    Pull request branch: {{ pull_request.head_ref }}

    Pull request body:
    {{ pull_request.body }}

    Pull request files:
    {% for file in files %}
    {{ file.status }} {{ file.filename }}
    ```diff
    {{ file.diff }}
    ```
    {% endfor %}
    """


# TODO: move to Project
def _message_history_from_review_comment(
        comment: PullRequestReviewComment,
        pull_request: GithubPullRequest
) -> Sequence[ChatMessage]:
    if comment.in_reply_to_id is None:
        return [UserMessage(name=comment.user.login, content=comment.body)]

    root_comment_id = comment.in_reply_to_id
    root_comment = pull_request.get_review_comment(root_comment_id)
    review_comments = pull_request.get_review_comments(sort="created", direction="asc")
    response_comments = [comment for comment in review_comments if comment.in_reply_to_id == root_comment_id]
    root_comment_message = UserMessage(name=root_comment.user.login, content=f"{comment.diff_hunk}\n\n{comment.body}")
    thread_messages = []
    for _comment in response_comments:
        if _comment.user.login == ACEBOTS_APP_USERNAME:
            thread_messages.append(AssistantMessage(content=_comment.body))
        else:
            thread_messages.append(UserMessage(name=_comment.user.login, content=_comment.body))
    return [root_comment_message] + thread_messages


# TODO: move to Project
def _messages_from_pull_request(
        pull_request: GithubPullRequest
) -> list[ChatMessage]:
    comments = pull_request.get_issue_comments()
    messages = []
    for comment in comments:
        if comment.user.login == ACEBOTS_APP_USERNAME:
            messages.append(AssistantMessage(content=comment.body))
        else:
            messages.append(UserMessage(content=comment.body, name=comment.user.login))
    return messages


def _messages_from_issue(issue: GithubIssue) -> list[ChatMessage]:
    comments = issue.get_comments()
    messages = []
    for comment in comments:
        if comment.user.login == ACEBOTS_APP_USERNAME:
            messages.append(AssistantMessage(content=comment.body))
        else:
            messages.append(UserMessage(content=comment.body, name=comment.user.login))
    return messages
