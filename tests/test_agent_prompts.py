from acedev.agent.prompts import pull_request_review_comment_prompt, issue_assigned_prompt
from acedev.service.model import PullRequest, FileChange, Issue

DIFF = "diff"
FILENAME = "filename"
STATUS = "status"
URL = "url"
BRANCH = "branch"
BODY = "body"
TITLE = "title"


def test_pull_request_review_comment_prompt() -> None:
    pull_request = PullRequest(
        title=TITLE,
        body=BODY,
        head_ref=BRANCH,
        url=URL,
        files=[
            FileChange(
                status=STATUS,
                filename=FILENAME,
                diff=DIFF,
            ),
            FileChange(
                status=STATUS,
                filename=FILENAME,
                diff=DIFF,
            ),
        ],
    )

    assert pull_request_review_comment_prompt(pull_request) == f"""\
You are AceDev, an AI member of the software engineering team. You have opened a pull
request and are waiting for a review. When a review comment is posted, you should reply
to the comment and update the code if needed. You should also
ask for clarification if you don't understand the comment.

Pull request title: {TITLE}

Pull request branch: {BRANCH}

Pull request body:
{BODY}

Pull request files:
{STATUS} {FILENAME}
```diff
{DIFF}
```

{STATUS} {FILENAME}
```diff
{DIFF}
```\
"""


def test_issue_assigned_prompt() -> None:
    issue = Issue(
        id=1,
        number=1,
        title=TITLE,
        body=BODY,
        comments=[]
    )

    assert issue_assigned_prompt(issue) == f"""\
You are AceDev, an AI assistant for software engineering.

You have just been assigned with a GitHub Issue.

Issue title: {TITLE}

Issue body:
{BODY}

Here's what I expect from you now:
1. Check out the high-level overview of the project.
2. Expand any functions or classes if needed.
3. Give me a 4-5 bullet-point plan for implementation.\
"""
