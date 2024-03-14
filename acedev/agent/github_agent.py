import os
from dataclasses import dataclass
from typing import Sequence

from acedev.agent import AgentRunner
from acedev.agent.prompts import (
    pull_request_review_comment_prompt,
    issue_assigned_prompt,
)
from acedev.service.github_service import GitHubService
from acedev.service.model import (
    ChatMessage,
    SystemMessage,
    UserMessage,
    AssistantMessage,
    PullRequestReviewThread,
    Issue,
)
from acedev.service.tool_provider import ToolProvider

ACEBOTS_APP_USERNAME = os.getenv("GITHUB_APP_USERNAME", "acebots-ai[bot]")


@dataclass
class GitHubAgent:
    tool_provider: ToolProvider
    agent_runner: AgentRunner
    github_service: GitHubService

    def tools(self):
        return {
            **self.tool_provider.code_understanding_tools(),
            **self.tool_provider.code_editing_tools(),
        }

    def handle_pull_request_review_comment(
        self, comment_id: int, pull_request_number: int
    ) -> None:
        """
        Handle a pull request review comment event:
            - Prepare messages for the LLM agent request.
                a. For system message, get pull request title, head, body and files
                b. For other messages, get pull request thread
            - Prepare tools for the LLM agent request.
            - Run the LLM agent and reply in the pull request thread.
        """
        pull_request = self.github_service.get_pull_request(pull_request_number)
        messages: list[ChatMessage] = [
            SystemMessage(
                content=pull_request_review_comment_prompt(pull_request=pull_request)
            )
        ]

        pull_request_thread = self.github_service.get_pull_request_review_thread(
            pull_request_number=pull_request_number, comment_id=comment_id
        )

        messages.extend(self._message_history_from_review_comment(pull_request_thread))

        for message in self.agent_runner.run(messages, self.tools()):
            if isinstance(message, AssistantMessage) and message.content:
                self.github_service.reply_in_pull_request_thread(
                    pull_request_number=pull_request_number,
                    root_comment_id=pull_request_thread.comments[0].id,
                    body=message.content,
                )

    def handle_issue_comment(self, issue_number: int) -> None:
        """
        Handle an issue comment event:
            - Prepare messages for the LLM agent request.
            - Prepare tools for the LLM agent request.
            - Run the agent and reply in the issue.
        """
        issue = self.github_service.get_issue(issue_number)

        if self.github_service.issue_is_pull_request(issue_number):
            pull_request = self.github_service.get_pull_request(issue_number)
            system_message = SystemMessage(
                content=pull_request_review_comment_prompt(pull_request=pull_request)
            )
        else:
            # TODO: use different prompt for not assigned issues
            system_message = SystemMessage(content=issue_assigned_prompt(issue=issue))

        messages: list[ChatMessage] = [system_message] + self._messages_from_issue(
            issue
        )

        for message in self.agent_runner.run(messages, self.tools()):
            if isinstance(message, AssistantMessage) and message.content:
                self.github_service.create_issue_comment(
                    issue_number=issue_number, body=message.content
                )

    def handle_issue_assignment(self, issue_number: int) -> None:
        issue = self.github_service.get_issue(issue_number)
        messages = [
            SystemMessage(content=issue_assigned_prompt(issue=issue))
        ] + self._messages_from_issue(issue)

        for message in self.agent_runner.run(messages, self.tools()):
            if isinstance(message, AssistantMessage) and message.content:
                self.github_service.create_issue_comment(
                    issue_number=issue_number, body=message.content
                )

    def react_to_comment(self, comment_type: str, comment_id: int, reaction_type: str) -> None:
        """
        Add a reaction to a comment.

        :param comment_type: Type of the comment ('issue' or 'pull_request')
        :param comment_id: ID of the comment
        :param reaction_type: Type of reaction (e.g., 'eyes')
        """
        if comment_type == 'issue':
            self.github_service.add_reaction_to_issue_comment(comment_id, reaction_type)
        elif comment_type == 'pull_request':
            self.github_service.add_reaction_to_pull_request_review_comment(comment_id, reaction_type)

    @staticmethod
    def _message_history_from_review_comment(
        thread: PullRequestReviewThread,
    ) -> Sequence[ChatMessage]:
        root_comment = thread.comments[0]
        root_message = UserMessage(
            name=root_comment.user, content=f"{thread.diff_hunk}\n\n{root_comment.body}"
        )
        thread_messages = []
        for _comment in thread.comments[1:]:
            if _comment.user == ACEBOTS_APP_USERNAME:
                thread_messages.append(AssistantMessage(content=_comment.body))
            else:
                thread_messages.append(
                    UserMessage(name=_comment.user, content=_comment.body)
                )
        return [root_message] + thread_messages

    @staticmethod
    def _messages_from_issue(issue: Issue) -> list[ChatMessage]:
        messages = []
        for comment in issue.comments:
            if comment.user == ACEBOTS_APP_USERNAME:
                messages.append(AssistantMessage(content=comment.body))
            else:
                messages.append(UserMessage(content=comment.body, name=comment.user))
        return messages

    def handle_pull_request_review_comment(
        self, comment_id: int, pull_request_number: int
    ) -> None:
        """
        Handle a pull request review comment event:
            - Prepare messages for the LLM agent request.
                a. For system message, get pull request title, head, body and files
                b. For other messages, get pull request thread
            - Prepare tools for the LLM agent request.
            - Run the LLM agent and reply in the pull request thread.
            - React to the comment if AceDev is tagged.
        """
        pull_request = self.github_service.get_pull_request(pull_request_number)
        messages: list[ChatMessage] = [
            SystemMessage(
                content=pull_request_review_comment_prompt(pull_request=pull_request)
            )
        ]

        pull_request_thread = self.github_service.get_pull_request_review_thread(
            pull_request_number=pull_request_number, comment_id=comment_id
        )

        messages.extend(self._message_history_from_review_comment(pull_request_thread))

        for message in self.agent_runner.run(messages, self.tools()):
            if isinstance(message, AssistantMessage) and message.content:
                self.github_service.reply_in_pull_request_thread(
                    pull_request_number=pull_request_number,
                    root_comment_id=pull_request_thread.comments[0].id,
                    body=message.content,
                )
                if "@acedev-ai" in message.content:
                    self.react_to_comment('pull_request', comment_id, 'eyes')

    def handle_issue_comment(self, issue_number: int) -> None:
        """
        Handle an issue comment event:
            - Prepare messages for the LLM agent request.
            - Prepare tools for the LLM agent request.
            - Run the agent and reply in the issue.
            - React to the comment if AceDev is tagged.
        """
        issue = self.github_service.get_issue(issue_number)

        if self.github_service.issue_is_pull_request(issue_number):
            pull_request = self.github_service.get_pull_request(issue_number)
            system_message = SystemMessage(
                content=pull_request_review_comment_prompt(pull_request=pull_request)
            )
        else:
            # TODO: use different prompt for not assigned issues
            system_message = SystemMessage(content=issue_assigned_prompt(issue=issue))

        messages: list[ChatMessage] = [system_message] + self._messages_from_issue(
            issue
        )

        for message in self.agent_runner.run(messages, self.tools()):
            if isinstance(message, AssistantMessage) and message.content:
                self.github_service.create_issue_comment(
                    issue_number=issue_number, body=message.content
                )
                if "@acedev-ai" in message.content:
                    self.react_to_comment('issue', issue.comments[-1].id, 'eyes')

