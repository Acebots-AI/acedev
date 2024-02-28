from github import GithubIntegration
from starlette.requests import Request

from acedev.agent.github_agent_factory import GitHubAgentFactory
from acedev.api.settings import ApiSettings
from acedev.agent.openai_agent_runner import OpenAIAgentRunner
from acedev.service.openai_service import OpenAIService


def get_ghe_client(request: Request) -> GithubIntegration:
    return request.app.state.ghe_client  # type: ignore[no-any-return]


def get_openai_service(request: Request) -> OpenAIService:
    return request.app.state.openai_service  # type: ignore[no-any-return]


def get_openai_agent(request: Request) -> OpenAIAgentRunner:
    return request.app.state.openai_agent  # type: ignore[no-any-return]


def get_api_settings(request: Request) -> ApiSettings:
    return request.app.state.api_settings  # type: ignore[no-any-return]


def get_github_agent_factory(request: Request) -> GitHubAgentFactory:
    return request.app.state.github_agent_factory  # type: ignore[no-any-return]
