from github import GithubIntegration
from starlette.requests import Request

from acedev.service.agent.openai_agent import OpenAIAgent
from acedev.service.openai_service import OpenAIService


def get_ghe_client(request: Request) -> GithubIntegration:
    return request.app.state.ghe_client  # type: ignore[no-any-return]


def get_openai_service(request: Request) -> OpenAIService:
    return request.app.state.openai_service  # type: ignore[no-any-return]


def get_openai_agent(request: Request) -> OpenAIAgent:
    return request.app.state.openai_agent  # type: ignore[no-any-return]
