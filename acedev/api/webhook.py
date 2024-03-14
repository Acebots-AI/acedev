import logging
import os
from typing import Annotated, Any, Optional

import fastapi
from fastapi import BackgroundTasks, Body, Depends, Header
from github import GithubIntegration
from pydantic import BaseModel

from acedev.agent.github_agent_factory import GitHubAgentFactory
from acedev.agent.openai_agent_runner import OpenAIAgentRunner
from acedev.api.dependencies import (
    get_ghe_client,
    get_openai_agent,
    get_github_agent_factory,
)
from acedev.service.github_service import GitHubService
from acedev.service.gitrepository import GitRepository

router = fastapi.APIRouter()
logger = logging.getLogger(__name__)

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
    openai_agent: OpenAIAgentRunner = Depends(get_openai_agent),
    github_agent_factory: GitHubAgentFactory = Depends(get_github_agent_factory),
) -> fastapi.Response:
    logger.info(f"Received {x_github_event=}")
    logger.debug(f"{payload=}")

    match x_github_event:
        case "pull_request_review_comment":
            review_comment = PullRequestReviewCommentPayload(**payload)
            if review_comment.comment.body.startswith(
                f"@{ACEDEV_USERNAME}"
            ) and review_comment.action in [
                "created",
                "edited",
            ]:
                background_tasks.add_task(
                    handle_pull_request_review_comment,
                    review_comment,
                    ghe_client,
                    openai_agent,
                    github_agent_factory,
                )
        case "issue_comment":
            issue_comment = IssueCommentPayload(**payload)

            if issue_comment.comment.body.startswith(
                f"@{ACEDEV_USERNAME}"
            ) and issue_comment.action in [
                "created",
                "edited",
            ]:
                background_tasks.add_task(
                    handle_issue_comment,
                    issue_comment,
                    ghe_client,
                    openai_agent,
                    github_agent_factory,
                )
        case "issues":
            if payload.get("action", None) == "assigned":
                issue = IssueAssignedPayload(**payload)

                if issue.assignee.login == ACEDEV_USERNAME:
                    background_tasks.add_task(
                        handle_assigned_issue,
                        issue,
                        ghe_client,
                        openai_agent,
                        github_agent_factory,
                    )
        case _:
            logger.warning(f"Unexpected event: {x_github_event}")

    return fastapi.Response(status_code=202)


def handle_pull_request_review_comment(
    payload: PullRequestReviewCommentPayload,
    github_client: GithubIntegration,
    openai_agent: OpenAIAgentRunner,
    github_agent_factory: GitHubAgentFactory,
) -> None:
    try:
        github_repo = github_client.get_github_for_installation(
            payload.installation.id
        ).get_repo(payload.repository.full_name)

        github_agent = github_agent_factory.create(
            git_repo=GitRepository(github_repo),
            github_service=GitHubService(github_repo),
            agent_runner=openai_agent,
        )

        if "@acedev-ai" in payload.comment.body:
            github_agent.github_service.add_reaction_to_comment(
                issue_number=payload.pull_request.number,
                comment_id=payload.comment.id,
                reaction='eyes'
            )
            github_agent.handle_pull_request_review_comment(
                comment_id=payload.comment.id,
                pull_request_number=payload.pull_request.number,
            )
        else:
            github_agent.handle_pull_request_review_comment(
                comment_id=payload.comment.id,
                pull_request_number=payload.pull_request.number,
            )
    except Exception:
        logger.exception(f"Failed to handle pull request review comment: {payload=}")


def handle_issue_comment(
    payload: IssueCommentPayload,
    github_client: GithubIntegration,
    openai_agent: OpenAIAgentRunner,
    github_agent_factory: GitHubAgentFactory,
) -> None:
    try:
        github_repo = github_client.get_github_for_installation(
            payload.installation.id
        ).get_repo(payload.repository.full_name)

        github_agent = github_agent_factory.create(
            git_repo=GitRepository(github_repo),
            github_service=GitHubService(github_repo),
            agent_runner=openai_agent,
        )

        if "@acedev-ai" in payload.comment.body:
            github_agent.github_service.add_reaction_to_comment(
                issue_number=payload.issue.number,
                comment_id=payload.comment.id,
                reaction='eyes'
            )
        else:
            github_agent.handle_issue_comment(
                issue_number=payload.issue.number,
            )
    except Exception:
        logger.exception(f"Failed to handle issue comment: {payload=}")


def handle_assigned_issue(
    payload: IssueAssignedPayload,
    github_client: GithubIntegration,
    openai_agent: OpenAIAgentRunner,
    github_agent_factory: GitHubAgentFactory,
) -> None:
    try:
        github_repo = github_client.get_github_for_installation(
            payload.installation.id
        ).get_repo(payload.repository.full_name)

        github_agent = github_agent_factory.create(
            git_repo=GitRepository(github_repo),
            github_service=GitHubService(github_repo),
            agent_runner=openai_agent,
        )

        github_agent.handle_issue_assignment(
            issue_number=payload.issue.number,
        )
    except Exception:
        logger.exception(f"Failed to handle assigned issue: {payload=}")
