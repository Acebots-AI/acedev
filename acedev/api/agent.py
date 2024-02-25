import json
from typing import Iterator

import fastapi
from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from github import GithubIntegration
from pydantic import BaseModel
from starlette.responses import StreamingResponse
from tree_sitter_languages import get_parser

from acedev.api.dependencies import get_ghe_client
from acedev.service.agent import Agent
from acedev.service.model import AgentCompletionRequest, AgentAction, AgentObservation, ChatMessage
from acedev.service.project import Project


router = fastapi.APIRouter()


@router.post("/completion", summary="Returns chat completion given a list of messages and context.")
def complete(
        request: AgentCompletionRequest,
        ghe_client: GithubIntegration = Depends(get_ghe_client),
) -> StreamingResponse:
    owner, repo = request.context.owner, request.context.repo

    project = Project(
        ghe_repo=ghe_client.get_repo_installation(owner, repo)
        .get_github_for_installation()
        .get_repo(f"{owner}/{repo}"),
    )

    agent = Agent(tools=project.code_understanding_tools())
    message_stream = agent.stream(request)

    return StreamingResponse(
        jsonify_chunks(message_stream), media_type="application/json"
    )


def jsonify_chunks(
        chunks: Iterator[AgentAction | AgentObservation | ChatMessage],
) -> Iterator[str]:
    for chunk in chunks:
        yield json.dumps(jsonable_encoder(chunk)) + "\n"
