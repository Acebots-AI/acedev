import pytest

from acedev.service.model import File
from acedev.tools.code_editor import (
    CodeEditor,
    reconcile_subsequence,
)


@pytest.fixture
def code_editor():
    return CodeEditor()


def test_adding_lines_succeeds(code_editor: CodeEditor) -> None:
    file = File(
        path="file.py",
        content="""\
existing line 1
existing line 2
existing line 3
existing line 4
""",
    )

    diff1 = """\
--- file.py
+++ file.py
@@ ... @@
 existing line 1
+new line 1
 existing line 2
"""

    expected1 = File(
        path="file.py",
        content="""\
existing line 1
new line 1
existing line 2
existing line 3
existing line 4
""",
    )

    assert code_editor.apply_diff(diff1, file) == expected1

    diff2 = """\
--- file.py
+++ file.py
@@ ... @@
 existing line 3
+new line 2
+new line 3
 existing line 4
"""

    expected2 = File(
        path="file.py",
        content="""\
existing line 1
existing line 2
existing line 3
new line 2
new line 3
existing line 4
""",
    )

    assert code_editor.apply_diff(diff2, file) == expected2

    diff3 = """\
--- file.py
+++ file.py
@@ ... @@
 existing line 1
+new line 1
 existing line 2

@@ ... @@
 existing line 3
+new line 2
+new line 3
 existing line 4
"""

    expected3 = File(
        path="file.py",
        content="""\
existing line 1
new line 1
existing line 2
existing line 3
new line 2
new line 3
existing line 4
""",
    )

    assert code_editor.apply_diff(diff3, file) == expected3


def test_removing_lines_succeeds(code_editor: CodeEditor) -> None:
    file = File(
        path="file.py",
        content="""\
existing line 1
existing line 2
existing line 3
existing line 4
""",
    )

    diff1 = """\
--- file.py
+++ file.py
@@ ... @@
 existing line 1
-existing line 2
 existing line 3
"""

    expected1 = File(
        path="file.py",
        content="""\
existing line 1
existing line 3
existing line 4
""",
    )

    assert code_editor.apply_diff(diff1, file) == expected1

    diff2 = """\
--- file.py
+++ file.py
@@ ... @@
 existing line 2
-existing line 3
-existing line 4
"""

    expected2 = File(
        path="file.py",
        content="""\
existing line 1
existing line 2
""",
    )

    assert code_editor.apply_diff(diff2, file) == expected2

    diff3 = """\
--- file.py
+++ file.py
@@ ... @@
 existing line 1
-existing line 2
-existing line 3
 existing line 4
"""

    expected3 = File(
        path="file.py",
        content="""\
existing line 1
existing line 4
""",
    )

    assert code_editor.apply_diff(diff3, file) == expected3

    # todo: add a case for multiple hunks


@pytest.mark.skip(reason="not working")
def test_adding_empty_line_at_the_end_succeeds(
    code_editor: CodeEditor,
) -> None:
    file = File(
        path="file.py",
        content="""\
existing line 1
existing line 2
existing line 3
existing line 4""",
    )

    diff = """\
--- file.py
+++ file.py
@@ ... @@
 existing line 4
+"""

    expected = File(
        path="file.py",
        content="""\
existing line 1
existing line 2
existing line 3
existing line 4
""",
    )

    assert code_editor.apply_diff(diff, file) == expected


def test_adding_empty_line_in_the_middle_succeeds(code_editor: CodeEditor) -> None:
    file = File(
        path="file.py",
        content="""\
existing line 1
existing line 2
existing line 3
existing line 4
""",
    )

    diff1 = """\
--- file.py
+++ file.py
@@ ... @@
 existing line 3
+
 existing line 4
"""

    expected1 = File(
        path="file.py",
        content="""\
existing line 1
existing line 2
existing line 3

existing line 4
""",
    )

    assert code_editor.apply_diff(diff1, file) == expected1

    diff2 = """\
--- file.py
+++ file.py
@@ ... @@
 existing line 3
+
+
 existing line 4
"""

    expected2 = File(
        path="file.py",
        content="""\
existing line 1
existing line 2
existing line 3


existing line 4
""",
    )

    assert code_editor.apply_diff(diff2, file) == expected2

    diff3 = """\
--- file.py
+++ file.py
@@ ... @@
 existing line 2
+
 existing line 3
+
 existing line 4
"""

    expected3 = File(
        path="file.py",
        content="""\
existing line 1
existing line 2

existing line 3

existing line 4
""",
    )

    assert code_editor.apply_diff(diff3, file) == expected3


def test_removing_empty_line_in_the_middle_succeeds(code_editor: CodeEditor) -> None:
    file = File(
        path="file.py",
        content="""\
existing line 1
existing line 2
existing line 3

existing line 4
""",
    )

    diff = """\
--- file.py
+++ file.py
@@ ... @@
 existing line 3
-
 existing line 4
"""

    expected = File(
        path="file.py",
        content="""\
existing line 1
existing line 2
existing line 3
existing line 4
""",
    )

    assert code_editor.apply_diff(diff, file) == expected


def test_adding_new_line_succeeds_when_suffix_context_is_missing(
    code_editor: CodeEditor,
) -> None:
    file = File(
        path="file.py",
        content="""\
existing line 1
existing line 2
existing line 3
existing line 4
""",
    )

    diff1 = """\
--- file.py
+++ file.py
@@ ... @@
 existing line 3
+new line 1
"""

    expected1 = File(
        path="file.py",
        content="""\
existing line 1
existing line 2
existing line 3
new line 1
existing line 4
""",
    )

    assert code_editor.apply_diff(diff1, file) == expected1

    diff2 = """\
--- file.py
+++ file.py
@@ ... @@
 existing line 2
+new line 1
"""

    expected2 = File(
        path="file.py",
        content="""\
existing line 1
existing line 2
new line 1
existing line 3
existing line 4
""",
    )

    assert code_editor.apply_diff(diff2, file) == expected2

    diff3 = """\
--- file.py
+++ file.py
@@ ... @@
 existing line 2
+new line 1
+new line 2
"""

    expected3 = File(
        path="file.py",
        content="""\
existing line 1
existing line 2
new line 1
new line 2
existing line 3
existing line 4
""",
    )

    assert code_editor.apply_diff(diff3, file) == expected3

    diff4 = """\
--- file.py
+++ file.py
@@ ... @@
 existing line 2
+new line 1
 existing line 3
+new line 2
"""

    expected4 = File(
        path="file.py",
        content="""\
existing line 1
existing line 2
new line 1
existing line 3
new line 2
existing line 4
""",
    )

    assert code_editor.apply_diff(diff4, file) == expected4


def test_removing_line_succeeds_when_suffix_context_is_missing(
    code_editor: CodeEditor,
) -> None:
    file = File(
        path="file.py",
        content="""\
existing line 1
existing line 2
existing line 3
existing line 4
""",
    )

    diff = """\
--- file.py
+++ file.py
@@ ... @@
 existing line 2
-existing line 3
"""

    expected = File(
        path="file.py",
        content="""\
existing line 1
existing line 2
existing line 4
""",
    )

    assert code_editor.apply_diff(diff, file) == expected


def test_adding_lines_succeeds_when_context_is_incomplete(
    code_editor: CodeEditor,
) -> None:
    file = File(
        path="file.py",
        content="""\
existing line 1
existing line 2
existing line 3
existing line 4
existing line 5
existing line 6
existing line 7
existing line 8
existing line 9
existing line 10
""",
    )

    diff1 = """\
--- file.py
+++ file.py
@@ ... @@
 existing line 1
+new line 1
 existing line 3
"""

    expected1 = File(
        path="file.py",
        content="""\
existing line 1
existing line 2
new line 1
existing line 3
existing line 4
existing line 5
existing line 6
existing line 7
existing line 8
existing line 9
existing line 10
""",
    )

    assert code_editor.apply_diff(diff1, file) == expected1

    diff2 = """\
--- file.py
+++ file.py
@@ ... @@
 existing line 1
+new line 1
 existing line 10
"""

    expected2 = File(
        path="file.py",
        content="""\
existing line 1
existing line 2
existing line 3
existing line 4
existing line 5
existing line 6
existing line 7
existing line 8
existing line 9
new line 1
existing line 10
""",
    )

    assert code_editor.apply_diff(diff2, file) == expected2


def test_adding_lines_at_eof_succeeds_with_fallback(code_editor: CodeEditor) -> None:
    diff = """\
--- file.py
+++ file.py
@@ ... @@
 def test_func():
     assert True
 
+def test_func2():
+    assert True
+    assert True
"""

    file = File(
        path="file.py",
        content="""\
def test_func():
    assert True
""",
    )

    expected = File(
        path="file.py",
        content="""\
def test_func():
    assert True

def test_func2():
    assert True
    assert True
""",
    )

    assert code_editor.apply_diff(diff, file) == expected

    diff = """\
--- file.py
+++ file.py
@@ ... @@
 def test_func():
     assert True
 
 def test_func1():
     assert True
 
+def test_func2():
+    assert True
+    assert True
+
"""

    file = File(
        path="file.py",
        content="""\
def test_func():
    assert True

def test_func1():
    assert True
""",
    )

    expected = File(
        path="file.py",
        content="""\
def test_func():
    assert True

def test_func1():
    assert True

def test_func2():
    assert True
    assert True

""",
    )

    assert code_editor.apply_diff(diff, file) == expected


def test_case_for_removing_lines_eof(code_editor: CodeEditor) -> None:
    diff = """\
--- tests/test_api.py
+++ tests/test_api.py
@@ ... @@
     # THEN the result should be 8
     assert response.json().get("result") == 8
 
-
-The test fixture "client" is defined in conftest.py
-These tests are trivial examples, they are not meant as an introduction to
-proper testing.
"""

    file = File(
        path="tests/test_api.py",
        content='''\
"""Examples testing the api using the starlette TestClient.

The test fixture "client" is defined in conftest.py
These tests are trivial examples, they are not meant as an introduction to
proper testing.

Read more about testing in the FastAPI docs:
https://fastapi.tiangolo.com/tutorial/testing/
"""

import starlette.testclient


def test_read_root(client: starlette.testclient.TestClient) -> None:
    """Test that the root path can be read."""

    # GIVEN the root path
    path = "/"

    # WHEN calling the api
    response = client.get(path)

    # THEN status_code should be 200
    assert response.status_code == 200


def test_addition(client: starlette.testclient.TestClient) -> None:
    """Test that the addition endpoint correctly sums two numbers."""

    # GIVEN the addition path and two numbers to sum
    path = "/v1/maths/addition"
    body = {"number1": 2, "number2": 3}

    # WHEN calling the api
    response = client.post(path, json=body)

    # THEN the sum should be 5
    assert response.json().get("result") == 5


def test_divide_by_zero(client: starlette.testclient.TestClient) -> None:
    """Test that the division endpoint returns a 400 when dividing by 0."""

    # GIVEN the division path and two numbers to divide
    path = "/v1/maths/division"
    body = {"number1": 2, "number2": 0}

    # WHEN calling the api
    response = client.post(path, json=body)

    # THEN the status code should be 400 (Bad request)
    assert response.status_code == 400


def test_exponentiation(client: starlette.testclient.TestClient) -> None:
    """Test that the exponentiation endpoint correctly calculates A^B."""
    # GIVEN the exponentiation path and two numbers to exponentiate
    path = "/exponentiation"
    body = {"number1": 2, "number2": 3}

    # WHEN calling the api
    response = client.post(path, json=body)

    # THEN the result should be 8
    assert response.json().get("result") == 8


The test fixture "client" is defined in conftest.py
These tests are trivial examples, they are not meant as an introduction to
proper testing.
''',
    )

    expected = File(
        path="tests/test_api.py",
        content='''\
"""Examples testing the api using the starlette TestClient.

The test fixture "client" is defined in conftest.py
These tests are trivial examples, they are not meant as an introduction to
proper testing.

Read more about testing in the FastAPI docs:
https://fastapi.tiangolo.com/tutorial/testing/
"""

import starlette.testclient


def test_read_root(client: starlette.testclient.TestClient) -> None:
    """Test that the root path can be read."""

    # GIVEN the root path
    path = "/"

    # WHEN calling the api
    response = client.get(path)

    # THEN status_code should be 200
    assert response.status_code == 200


def test_addition(client: starlette.testclient.TestClient) -> None:
    """Test that the addition endpoint correctly sums two numbers."""

    # GIVEN the addition path and two numbers to sum
    path = "/v1/maths/addition"
    body = {"number1": 2, "number2": 3}

    # WHEN calling the api
    response = client.post(path, json=body)

    # THEN the sum should be 5
    assert response.json().get("result") == 5


def test_divide_by_zero(client: starlette.testclient.TestClient) -> None:
    """Test that the division endpoint returns a 400 when dividing by 0."""

    # GIVEN the division path and two numbers to divide
    path = "/v1/maths/division"
    body = {"number1": 2, "number2": 0}

    # WHEN calling the api
    response = client.post(path, json=body)

    # THEN the status code should be 400 (Bad request)
    assert response.status_code == 400


def test_exponentiation(client: starlette.testclient.TestClient) -> None:
    """Test that the exponentiation endpoint correctly calculates A^B."""
    # GIVEN the exponentiation path and two numbers to exponentiate
    path = "/exponentiation"
    body = {"number1": 2, "number2": 3}

    # WHEN calling the api
    response = client.post(path, json=body)

    # THEN the result should be 8
    assert response.json().get("result") == 8

''',
    )

    assert code_editor.apply_diff(diff, file) == expected


def test_reconcile_subsequence() -> None:
    subsequence = ["line 1", "line 3", "line 4"]
    superset = [
        "line 1",
        "line 2",
        "line 3",
        "line 4",
        "line 5",
        "line 6",
        "line 7",
        "line 8",
        "line 9",
        "line 10",
    ]

    expected = ["line 1", "line 2", "line 3", "line 4"]
    result = reconcile_subsequence(subsequence, superset, 0)

    assert result == expected, f"Expected {expected}, but got {result}"

    subsequence = ["line 1", "line 2", "foo", "line 3", "line 4"]
    superset = [
        "line 1",
        "line 2",
        "line 3",
        "line 4",
        "line 5",
        "line 6",
        "line 7",
        "line 8",
        "line 9",
        "line 10",
    ]

    expected = ["line 1", "line 2", "line 3", "line 4"]
    result = reconcile_subsequence(subsequence, superset, 0)

    assert result == expected, f"Expected {expected}, but got {result}"

    subsequence = ["line 1", "line 3", "line 4"]
    superset = [
        "line 1",
        "line 2",
        "line 1",
        "line 2",
        "line 3",
        "line 4",
        "line 5",
    ]

    # Despite having more elements, this subsequence is valid
    expected = ["line 1", "line 2", "line 1", "line 2", "line 3", "line 4"]
    result = reconcile_subsequence(subsequence, superset, 0)

    assert result == expected, f"Expected {expected}, but got {result}"

    subsequence = ["line 1", "foo", "line 3", "line 4"]
    superset = [
        "line 1",
        "line 2",
        "line 3",
        "line 4",
        "line 5",
        "line 6",
        "line 7",
        "line 8",
        "line 9",
        "line 10",
    ]

    expected = ["line 1", "line 2", "line 3", "line 4"]
    result = reconcile_subsequence(subsequence, superset, 0)

    assert result == expected, f"Expected {expected}, but got {result}"

    subsequence = ["line 0", "line 1", "line 2", "line 3", "line 4"]
    superset = [
        "line 1",
        "line 2",
        "line 3",
        "line 4",
        "line 5",
        "line 6",
        "line 7",
        "line 8",
        "line 9",
        "line 10",
    ]

    expected = ["line 1", "line 2", "line 3", "line 4"]
    result = reconcile_subsequence(subsequence, superset, 0)

    assert result == expected, f"Expected {expected}, but got {result}"

    subsequence = ["line 1", "foo", "line 3", "line 4"]
    superset = [
        "line 1",
        "line 2",
        "line 3",
        "line 4",
        "line 5",
        "line 6",
        "line 7",
        "line 8",
        "line 9",
        "line 10",
    ]

    expected = ["line 1", "line 2", "line 3", "line 4", "line 5", "line 6", "line 7"]
    result = reconcile_subsequence(subsequence, superset, 3)

    assert result == expected, f"Expected {expected}, but got {result}"

    subsequence = ["line 1", "foo", "line 3", "line 4"]
    superset = [
        "line 1",
        "line 2",
        "line 3",
        "line 4",
    ]

    expected = ["line 1", "line 2", "line 3", "line 4"]
    result = reconcile_subsequence(subsequence, superset, 3)

    assert result == expected, f"Expected {expected}, but got {result}"


def test_reconcile_subsequence_with_extra_new_line() -> None:
    subsequence = """\
def func():
    pass

"""
    superset = """\
def func():
    pass
"""

    expected = """\
def func():
    pass
"""

    result = reconcile_subsequence(
        subsequence.splitlines(keepends=True), superset.splitlines(keepends=True), 3
    )

    assert result == expected.splitlines(
        keepends=True
    ), f"Expected {expected}, but got {result}"


def test_reconcile_subsequence_with_non_existing_line() -> None:
    subsequence = """\
def func1():
    pass

foo
def func2():
    pass
"""
    superset = """\
def func1():
    pass

def func2():
    pass
"""

    expected = """\
def func1():
    pass

def func2():
    pass
"""

    result = reconcile_subsequence(
        subsequence.splitlines(keepends=True), superset.splitlines(keepends=True), 3
    )

    assert result == expected.splitlines(
        keepends=True
    ), f"Expected {expected}, but got {result}"


def test_case_for_missing_suffix_context(code_editor: CodeEditor) -> None:
    file = File(
        path="file.py",
        content="""\
@dataclass
class GitHubService:
    github_repo: Repository

    def create_issue_comment(self, issue_number: int, body: str) -> None:
        # TODO: handle issue not found
        issue = self.github_repo.get_issue(number=issue_number)
        issue.create_comment(body=body)


class GitHubServiceException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
""",
    )

    diff = """\
--- file.py
+++ file.py
@@ ... @@
     def create_issue_comment(self, issue_number: int, body: str) -> None:
         # TODO: handle issue not found
         issue = self.github_repo.get_issue(number=issue_number)
         issue.create_comment(body=body)
+
+    def add_reaction_to_comment(self, reaction: str) -> None:
+        pass
+
"""

    expected = File(
        path="file.py",
        content="""\
@dataclass
class GitHubService:
    github_repo: Repository

    def create_issue_comment(self, issue_number: int, body: str) -> None:
        # TODO: handle issue not found
        issue = self.github_repo.get_issue(number=issue_number)
        issue.create_comment(body=body)

    def add_reaction_to_comment(self, reaction: str) -> None:
        pass



class GitHubServiceException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
""",
    )

    assert code_editor.apply_diff(diff, file) == expected
