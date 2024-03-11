from unittest.mock import create_autospec

from acedev.agent import AgentRunner
from acedev.agent.github_agent import GitHubAgent
from acedev.agent.github_agent_factory import GitHubAgentFactory
from acedev.service.github_service import GitHubService
from acedev.service.git_repository import GitRepository


def test_create() -> None:
    mock_git_repo = create_autospec(GitRepository)
    mock_git_repo.language = "python"
    assert isinstance(
        GitHubAgentFactory.create(
            git_repo=mock_git_repo,
            github_service=create_autospec(spec=GitHubService),
            agent_runner=create_autospec(spec=AgentRunner),
        ),
        GitHubAgent,
    )
