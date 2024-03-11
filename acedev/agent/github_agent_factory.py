from diff_match_patch import diff_match_patch
from tree_sitter_languages import get_parser, get_language

from acedev.agent import AgentRunner
from acedev.agent.github_agent import GitHubAgent
from acedev.service.github_service import GitHubService
from acedev.service.git_repository import GitRepository
from acedev.tools.code_editor import CodeEditor
from acedev.tools.symbol_manipulator import SymbolManipulator
from acedev.tools.tool_provider import ToolProvider


class GitHubAgentFactory:

    @staticmethod
    def create(
        git_repo: GitRepository,
        github_service: GitHubService,
        agent_runner: AgentRunner,
    ) -> GitHubAgent:
        symbol_manipulator = SymbolManipulator(
            git_repository=git_repo,
            parser=get_parser(git_repo.language),
            language=get_language(git_repo.language),
        )

        code_editor = CodeEditor(
            git_repository=git_repo,
            dmp=diff_match_patch()
        )

        tool_provider = ToolProvider(
            git_repository=git_repo,
            github_service=github_service,
            symbol_manipulator=symbol_manipulator,
            code_editor=code_editor,
        )

        return GitHubAgent(
            tool_provider=tool_provider,
            agent_runner=agent_runner,
            github_service=github_service,
        )
