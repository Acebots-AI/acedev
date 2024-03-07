import logging
from dataclasses import dataclass

from github import UnknownObjectException
from github.Repository import Repository

from acedev.service.model import (
    PullRequest,
    PullRequestReviewThread,
    PullRequestReviewComment,
    Issue,
    IssueComment,
)

logger = logging.getLogger(__name__)


@dataclass
class GitHubService:
    github_repo: Repository

    def create_pull_request(self, title: str, body: str, branch: str) -> PullRequest:
        logger.debug(f"Opening Pull Request ({title=}, {branch=})")

        for pull in self.github_repo.get_pulls(state="open"):
            if pull.head.ref == branch:
                raise GitHubServiceException(
                    f"Pull request already exists for {branch=}"
                )

        pull_request = self.github_repo.create_pull(
            title=title, body=body, head=branch, base=self.github_repo.default_branch
        )

        return PullRequest.from_github(pull_request)

    def get_pull_request(self, number: int) -> PullRequest:
        try:
            pull_request = self.github_repo.get_pull(number=number)
            return PullRequest.from_github(pull_request)
        except UnknownObjectException as e:
            error_message = f"PR#{number} not found"
            raise GitHubServiceException(error_message) from e

    def get_pull_request_review_thread(
        self, pull_request_number: int, comment_id: int
    ) -> PullRequestReviewThread:
        # TODO: handle PR not found
        pull_request = self.github_repo.get_pull(number=pull_request_number)
        comment = pull_request.get_review_comment(comment_id)

        root_comment = PullRequestReviewComment.from_github(
            comment
            if comment.in_reply_to_id is None
            else pull_request.get_review_comment(comment.in_reply_to_id)
        )

        response_comments = [
            PullRequestReviewComment.from_github(comment)
            for comment in (
                pull_request.get_review_comments(sort="created", direction="asc")
            )
            if comment.in_reply_to_id == root_comment.id
        ]

        return PullRequestReviewThread(
            diff_hunk=root_comment.diff_hunk,
            comments=[root_comment] + response_comments,
        )

    def reply_in_pull_request_thread(
        self, pull_request_number: int, root_comment_id: int, body: str
    ) -> None:
        # TODO: handle PR not found
        pull_request = self.github_repo.get_pull(number=pull_request_number)
        pull_request.create_review_comment_reply(comment_id=root_comment_id, body=body)

    def get_issue(self, issue_number: int) -> Issue:
        # TODO: handle issue not found
        _issue = self.github_repo.get_issue(number=issue_number)
        return Issue(
            id=_issue.id,
            number=_issue.number,
            title=_issue.title,
            body=_issue.body,
            comments=[
                IssueComment(user=comment.user.login, body=comment.body)
                for comment in _issue.get_comments()
            ],
        )

    def issue_is_pull_request(self, issue_number: int) -> bool:
        # TODO: handle issue not found
        issue = self.github_repo.get_issue(number=issue_number)
        return issue.pull_request is not None

    def create_issue_comment(self, issue_number: int, body: str) -> None:
        # TODO: handle issue not found
        issue = self.github_repo.get_issue(number=issue_number)
        issue.create_comment(body=body)


class GitHubServiceException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
