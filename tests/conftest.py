from unittest.mock import create_autospec

import fastapi
import pytest
from github import GithubIntegration
from starlette.testclient import TestClient

from acedev.agent.github_agent_factory import GitHubAgentFactory
from acedev.agent.openai_agent_runner import OpenAIAgentRunner
from acedev.api.api import get_api
from acedev.service.openai_service import OpenAIService


@pytest.fixture()
def ghe_client() -> GithubIntegration:
    return create_autospec(GithubIntegration)


@pytest.fixture()
def openai_service() -> OpenAIService:
    return create_autospec(OpenAIService)


@pytest.fixture()
def openai_agent() -> OpenAIAgentRunner:
    return create_autospec(OpenAIAgentRunner)


@pytest.fixture()
def github_agent_factory() -> GitHubAgentFactory:
    return create_autospec(GitHubAgentFactory)


@pytest.fixture()
def api(
    ghe_client: GithubIntegration,
    openai_service: OpenAIService,
    openai_agent: OpenAIAgentRunner,
    github_agent_factory: GitHubAgentFactory,
) -> fastapi.FastAPI:
    """Fixture for the initialized API.

    It is useful to be able to access the api e.g., when doing dependency
    overrides.
    https://fastapi.tiangolo.com/advanced/testing-dependencies/
    """
    return get_api(
        ghe_client=ghe_client,
        openai_service=openai_service,
        openai_agent=openai_agent,
        github_agent_factory=github_agent_factory,
    )


@pytest.fixture()
def client(
    api: fastapi.FastAPI,
) -> TestClient:
    """Fixture for returning a starlette test client."""
    return TestClient(api)
