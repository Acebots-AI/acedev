import pytest
from unittest.mock import MagicMock, create_autospec

from github import UnknownObjectException
from github.Issue import Issue as GitHubIssue
from github.PullRequestComment import PullRequestComment
from github.Repository import Repository
from github.PullRequest import PullRequest as GitHubPullRequest

from acedev.service.github_service import GitHubService, GitHubServiceException
from acedev.service.model import (
    PullRequest,
    Issue,
    FileChange,
    PullRequestReviewComment,
    PullRequestReviewThread,
    IssueComment,
)

BODY = "PR Body"
BRANCH = "feature-branch"
TITLE = "PR Title"
URL = "url"


@pytest.fixture
def github_repo() -> Repository:
    return create_autospec(Repository)


@pytest.fixture
def github_service(github_repo: Repository) -> GitHubService:
    return GitHubService(github_repo)


def test_create_pull_request_success(
    github_service: GitHubService, github_repo: Repository
) -> None:
    pull_request = PullRequest(
        title=TITLE,
        body=BODY,
        head_ref=BRANCH,
        url=URL,
        files=[FileChange(status="status", filename="filename", diff="diff")],
    )

    github_repo.create_pull.return_value = mock_github_pull_request(pull_request)
    result = github_service.create_pull_request(TITLE, BODY, BRANCH)

    assert result == pull_request


def test_create_pull_request_branch_exists(
    github_service: GitHubService, github_repo: Repository
) -> None:
    github_repo.get_pulls.return_value = [MagicMock(head=MagicMock(ref=BRANCH))]

    with pytest.raises(GitHubServiceException):
        github_service.create_pull_request(TITLE, BODY, BRANCH)


def test_get_pull_request_success(
    github_service: GitHubService, github_repo: Repository
) -> None:
    pull_request = PullRequest(
        title=TITLE,
        body=BODY,
        head_ref=BRANCH,
        url=URL,
        files=[FileChange(status="status", filename="filename", diff="diff")],
    )

    github_repo.get_pull.return_value = mock_github_pull_request(pull_request)

    result = github_service.get_pull_request(1)

    assert result == pull_request


def test_get_pull_request_not_found(
    github_service: GitHubService, github_repo: Repository
) -> None:
    github_repo.get_pull.side_effect = UnknownObjectException(404, "Not found")

    with pytest.raises(GitHubServiceException):
        github_service.get_pull_request(1)


def test_get_pull_request_review_thread_for_root_comment(
    github_service: GitHubService, github_repo: Repository
) -> None:
    root_comment = review_comment(1)
    response_comment = review_comment(2)
    irrelevant_comment = review_comment(3)

    pull_request = mock_github_pull_request(
        PullRequest(
            title=TITLE,
            body=BODY,
            head_ref=BRANCH,
            url=URL,
            files=[FileChange(status="status", filename="filename", diff="diff")],
        )
    )

    pull_request.get_review_comment.side_effect = lambda comment_id: {
        root_comment.id: mock_github_comment(
            comment=root_comment,
            in_reply_to_id=None,
        )
    }.get(comment_id, None)

    pull_request.get_review_comments.return_value = [
        mock_github_comment(
            comment=root_comment,
            in_reply_to_id=None,
        ),
        mock_github_comment(
            comment=response_comment,
            in_reply_to_id=1,
        ),
        mock_github_comment(
            comment=irrelevant_comment,
            in_reply_to_id=99,
        ),
    ]

    github_repo.get_pull.return_value = pull_request

    result = github_service.get_pull_request_review_thread(1, 1)

    assert result == PullRequestReviewThread(
        diff_hunk=root_comment.diff_hunk, comments=[root_comment, response_comment]
    )


def test_get_pull_request_review_thread_for_response_comment(
    github_service: GitHubService, github_repo: Repository
) -> None:
    root_comment = review_comment(1)
    response_comment = review_comment(2)
    irrelevant_comment = review_comment(3)

    pull_request = mock_github_pull_request(
        PullRequest(
            title=TITLE,
            body=BODY,
            head_ref=BRANCH,
            url=URL,
            files=[FileChange(status="status", filename="filename", diff="diff")],
        )
    )

    pull_request.get_review_comment.side_effect = lambda comment_id: {
        response_comment.id: mock_github_comment(
            comment=response_comment,
            in_reply_to_id=1,
        ),
        root_comment.id: mock_github_comment(
            comment=root_comment,
            in_reply_to_id=None,
        ),
    }.get(comment_id, None)

    pull_request.get_review_comments.return_value = [
        mock_github_comment(
            comment=root_comment,
            in_reply_to_id=None,
        ),
        mock_github_comment(
            comment=response_comment,
            in_reply_to_id=1,
        ),
        mock_github_comment(
            comment=irrelevant_comment,
            in_reply_to_id=99,
        ),
    ]

    github_repo.get_pull.return_value = pull_request

    result = github_service.get_pull_request_review_thread(1, 2)

    assert result == PullRequestReviewThread(
        diff_hunk=root_comment.diff_hunk, comments=[root_comment, response_comment]
    )


def test_reply_in_pull_request_thread_success(
    github_service: GitHubService, github_repo: Repository
) -> None:
    pull_request = mock_github_pull_request(
        PullRequest(
            title=TITLE,
            body=BODY,
            head_ref=BRANCH,
            url=URL,
            files=[FileChange(status="status", filename="filename", diff="diff")],
        )
    )

    github_repo.get_pull.return_value = pull_request

    github_service.reply_in_pull_request_thread(
        pull_request_number=1, root_comment_id=1, body="reply"
    )

    pull_request.create_review_comment_reply.assert_called_once_with(
        comment_id=1, body="reply"
    )


def test_get_issue_success(
    github_service: GitHubService, github_repo: Repository
) -> None:
    issue = Issue(
        id=1,
        number=1,
        title="title",
        body="body",
        comments=[IssueComment(user="user", body="body") for _ in range(3)],
    )

    github_repo.get_issue.return_value = mock_github_issue(issue)

    result = github_service.get_issue(1)

    assert result == issue


def test_issue_is_pull_request(
    github_service: GitHubService, github_repo: Repository
) -> None:
    github_repo.get_issue.return_value = MagicMock(pull_request=1)

    assert github_service.issue_is_pull_request(1)


def test_issue_is_not_pull_request(
    github_service: GitHubService, github_repo: Repository
) -> None:
    github_repo.get_issue.return_value = MagicMock(pull_request=None)

    assert not github_service.issue_is_pull_request(1)


def test_create_issue_comment_success(
    github_service: GitHubService, github_repo: Repository
) -> None:
    issue = mock_github_issue(
        Issue(id=1, number=1, title="title", body="body", comments=[])
    )
    github_repo.get_issue.return_value = issue

    github_service.create_issue_comment(1, "comment")

    issue.create_comment.assert_called_once_with("comment")


def review_comment(_id: int) -> PullRequestReviewComment:
    return PullRequestReviewComment(
        id=_id, user="user", body="body", diff_hunk="diff_hunk"
    )


def mock_github_pull_request(pull_request: PullRequest) -> GitHubPullRequest:
    mock_pull_request = create_autospec(GitHubPullRequest)
    mock_pull_request.title = pull_request.title
    mock_pull_request.body = pull_request.body
    mock_pull_request.head.ref = pull_request.head_ref
    mock_pull_request.html_url = pull_request.url
    mock_pull_request.get_files.return_value = [
        MagicMock(status=file.status, filename=file.filename, patch=file.diff)
        for file in pull_request.files
    ]
    return mock_pull_request


def mock_github_comment(
    comment: PullRequestReviewComment, in_reply_to_id: int = None
) -> PullRequestComment:
    mock_comment = create_autospec(PullRequestComment)
    mock_comment.id = comment.id
    mock_comment.user.login = comment.user
    mock_comment.body = comment.body
    mock_comment.diff_hunk = comment.diff_hunk
    mock_comment.in_reply_to_id = in_reply_to_id
    return mock_comment


def mock_github_issue(issue: Issue) -> GitHubIssue:
    mock_issue = create_autospec(GitHubIssue)
    mock_issue.id = issue.id
    mock_issue.number = issue.number
    mock_issue.title = issue.title
    mock_issue.body = issue.body
    mock_issue.get_comments.return_value = [
        MagicMock(user=MagicMock(login=comment.user), body=comment.body)
        for comment in issue.comments
    ]
    return mock_issue
