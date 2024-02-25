import logging

import fastapi
from fastapi import Depends
from github import GithubIntegration
from pydantic import BaseModel, Field
from tree_sitter_languages import get_parser

from acedev.api.dependencies import get_coding_service, get_ghe_client
from acedev.service.coding import CodingService
from acedev.service.model import PullRequest
from acedev.service.project import Project

router = fastapi.APIRouter()
logger = logging.getLogger(__name__)


class CreatePullRequestRequest(BaseModel):
    task: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    repo: str = Field(min_length=1)


class UpdatePullRequestRequest(BaseModel):
    task: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    repo: str = Field(min_length=1)
    pull_request_number: int = Field(ge=1)


@router.post(
    "/pull_request",
    summary="Implements the task and opens pull request.",
)
def create_pull_request(
    request: CreatePullRequestRequest,
    ghe_client: GithubIntegration = Depends(get_ghe_client),
    coding_service: CodingService = Depends(get_coding_service),
) -> PullRequest:
    owner = request.owner
    repo = request.repo
    project = Project(
        ghe_repo=ghe_client.get_repo_installation(owner, repo)
        .get_github_for_installation()
        .get_repo(f"{owner}/{repo}"),
        parser=get_parser('python'),
    )
    return coding_service.create_pull_request(request.task, project)


@router.patch(
    "/pull_request",
    summary="Updates the pull request.",
)
def update_pull_request(
    request: UpdatePullRequestRequest,
    ghe_client: GithubIntegration = Depends(get_ghe_client),
    coding_service: CodingService = Depends(get_coding_service),
) -> PullRequest:
    owner = request.owner
    repo = request.repo
    project = Project(
        ghe_repo=ghe_client.get_repo_installation(owner, repo)
        .get_github_for_installation()
        .get_repo(f"{owner}/{repo}"),
        parser=get_parser('python'),
    )
    return coding_service.update_pull_request(
        request.pull_request_number, request.task, project
    )
