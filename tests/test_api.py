from unittest.mock import create_autospec

from fastapi.encoders import jsonable_encoder
from github import GithubIntegration
from github.Repository import Repository as GithubRepository
from starlette.testclient import TestClient

from acedev.agent.github_agent import GitHubAgent
from acedev.agent.github_agent_factory import GitHubAgentFactory
from acedev.api.webhook import (
    PullRequestReviewCommentPayload,
    PullRequestReviewComment,
    User,
    Installation,
    PullRequest,
    PullRequestHead,
    Repository,
    ACEDEV_USERNAME,
    IssueCommentPayload,
    IssueComment,
    Issue,
    IssueAssignedPayload,
    Assignee,
)

ISSUE_ASSIGNED_PAYLOAD = IssueAssignedPayload(
    action="assigned",
    assignee=Assignee(login=ACEDEV_USERNAME),
    issue=Issue(
        id=456,
        number=456,
        title="Hello, world!",
        body="body",
        html_url="url",
    ),
    installation=Installation(id=789),
    repository=Repository(
        full_name="octocat/hello-world",
    ),
)

ISSUE_COMMENT_PAYLOAD = IssueCommentPayload(
    action="created",
    comment=IssueComment(
        id=123,
        body=f"@{ACEDEV_USERNAME} hello!",
    ),
    installation=Installation(id=789),
    issue=Issue(
        id=456,
        number=456,
        title="Hello, world!",
        body="body",
        html_url="url",
    ),
    repository=Repository(
        full_name="octocat/hello-world",
    ),
)

PULL_REQUEST_REVIEW_COMMENT_PAYLOAD = PullRequestReviewCommentPayload(
    action="created",
    comment=PullRequestReviewComment(
        id=123,
        body=f"@{ACEDEV_USERNAME} hello!",
        diff_hunk="diff_hunk",
        commit_id="commit_id",
        user=User(id=1, login="octocat"),
    ),
    installation=Installation(id=789),
    pull_request=PullRequest(
        id=456,
        number=456,
        title="Hello, world!",
        html_url="url",
        head=PullRequestHead(ref="ref"),
    ),
    repository=Repository(
        full_name="octocat/hello-world",
    ),
)


def test_pull_request_review_comment(
    client: TestClient,
    ghe_client: GithubIntegration,
    github_agent_factory: GitHubAgentFactory,
) -> None:
    mock_github_repo = create_autospec(GithubRepository)
    ghe_client.get_github_for_installation.return_value.get_repo.return_value = (
        mock_github_repo
    )
    mock_github_agent = create_autospec(GitHubAgent)
    github_agent_factory.create.return_value = mock_github_agent

    payload = PULL_REQUEST_REVIEW_COMMENT_PAYLOAD

    response = client.post(
        "/v1/webhook",
        headers={"X-GitHub-Event": "pull_request_review_comment"},
        json=jsonable_encoder(payload),
    )

    assert response.status_code == 202
    mock_github_agent.handle_pull_request_review_comment.assert_called_once_with(
        comment_id=payload.comment.id,
        pull_request_number=payload.pull_request.number,
    )


def test_irrelevant_pull_request_review_comment_ignored(
    client: TestClient,
    ghe_client: GithubIntegration,
    github_agent_factory: GitHubAgentFactory,
) -> None:
    payload = PULL_REQUEST_REVIEW_COMMENT_PAYLOAD
    payload.comment.body = "irrelevant comment"

    response = client.post(
        "/v1/webhook",
        headers={"X-GitHub-Event": "pull_request_review_comment"},
        json=jsonable_encoder(payload),
    )

    assert response.status_code == 202
    ghe_client.get_github_for_installation.assert_not_called()
    github_agent_factory.create.assert_not_called()


def test_deleted_pull_request_review_comment_ignored(
    client: TestClient,
    ghe_client: GithubIntegration,
    github_agent_factory: GitHubAgentFactory,
) -> None:
    payload = PULL_REQUEST_REVIEW_COMMENT_PAYLOAD
    payload.action = "deleted"

    response = client.post(
        "/v1/webhook",
        headers={"X-GitHub-Event": "pull_request_review_comment"},
        json=jsonable_encoder(payload),
    )

    assert response.status_code == 202
    ghe_client.get_github_for_installation.assert_not_called()
    github_agent_factory.create.assert_not_called()


def test_issue_comment(
    client: TestClient,
    ghe_client: GithubIntegration,
    github_agent_factory: GitHubAgentFactory,
) -> None:
    mock_github_repo = create_autospec(GithubRepository)
    ghe_client.get_github_for_installation.return_value.get_repo.return_value = (
        mock_github_repo
    )
    mock_github_agent = create_autospec(GitHubAgent)
    github_agent_factory.create.return_value = mock_github_agent

    payload = ISSUE_COMMENT_PAYLOAD

    response = client.post(
        "/v1/webhook",
        headers={"X-GitHub-Event": "issue_comment"},
        json=jsonable_encoder(payload),
    )

    assert response.status_code == 202
    mock_github_agent.handle_issue_comment.assert_called_once_with(
        issue_number=payload.issue.number,
    )


def test_irrelevant_issue_comment_ignored(
    client: TestClient,
    ghe_client: GithubIntegration,
    github_agent_factory: GitHubAgentFactory,
) -> None:
    payload = ISSUE_COMMENT_PAYLOAD
    payload.comment.body = "irrelevant comment"

    response = client.post(
        "/v1/webhook",
        headers={"X-GitHub-Event": "issue_comment"},
        json=jsonable_encoder(payload),
    )

    assert response.status_code == 202
    ghe_client.get_github_for_installation.assert_not_called()
    github_agent_factory.create.assert_not_called()


def test_deleted_issue_comment_ignored(
    client: TestClient,
    ghe_client: GithubIntegration,
    github_agent_factory: GitHubAgentFactory,
) -> None:
    payload = ISSUE_COMMENT_PAYLOAD
    payload.action = "deleted"

    response = client.post(
        "/v1/webhook",
        headers={"X-GitHub-Event": "issue_comment"},
        json=jsonable_encoder(payload),
    )

    assert response.status_code == 202
    ghe_client.get_github_for_installation.assert_not_called()
    github_agent_factory.create.assert_not_called()


def test_issue_assigned(
    client: TestClient,
    ghe_client: GithubIntegration,
    github_agent_factory: GitHubAgentFactory,
) -> None:
    mock_github_repo = create_autospec(GithubRepository)
    ghe_client.get_github_for_installation.return_value.get_repo.return_value = (
        mock_github_repo
    )
    mock_github_agent = create_autospec(GitHubAgent)
    github_agent_factory.create.return_value = mock_github_agent

    payload = ISSUE_ASSIGNED_PAYLOAD

    response = client.post(
        "/v1/webhook",
        headers={"X-GitHub-Event": "issues"},
        json=jsonable_encoder(payload),
    )

    assert response.status_code == 202
    mock_github_agent.handle_issue_assignment.assert_called_once_with(
        issue_number=payload.issue.number,
    )


def test_irrelevant_issue_event_ignored(
    client: TestClient,
    ghe_client: GithubIntegration,
    github_agent_factory: GitHubAgentFactory,
) -> None:
    payload = ISSUE_ASSIGNED_PAYLOAD
    payload.action = "unassigned"

    response = client.post(
        "/v1/webhook",
        headers={"X-GitHub-Event": "issues"},
        json=jsonable_encoder(payload),
    )

    assert response.status_code == 202
    ghe_client.get_github_for_installation.assert_not_called()
    github_agent_factory.create.assert_not_called()


def test_issue_assigned_to_different_user_ignored(
    client: TestClient,
    ghe_client: GithubIntegration,
    github_agent_factory: GitHubAgentFactory,
) -> None:
    payload = ISSUE_ASSIGNED_PAYLOAD
    payload.assignee.login = "different_user"

    response = client.post(
        "/v1/webhook",
        headers={"X-GitHub-Event": "issues"},
        json=jsonable_encoder(payload),
    )

    assert response.status_code == 202
    ghe_client.get_github_for_installation.assert_not_called()
    github_agent_factory.create.assert_not_called()


def test_unexpected_event_ignored(
    client: TestClient,
    ghe_client: GithubIntegration,
    github_agent_factory: GitHubAgentFactory,
) -> None:
    response = client.post(
        "/v1/webhook",
        headers={"X-GitHub-Event": "unexpected_event"},
        json={},
    )

    assert response.status_code == 202
    ghe_client.get_github_for_installation.assert_not_called()
    github_agent_factory.create.assert_not_called()
