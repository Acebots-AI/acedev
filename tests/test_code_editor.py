import pytest

from acedev.service.model import File
from acedev.tools.code_editor import (
    CodeEditor,
    add_missing_lines,
    remove_non_existing_lines,
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

    # not working
    # assert code_editor.apply_diff(diff2, file) == expected2

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


@pytest.mark.skip(reason="not working")
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


def test_add_missing_lines() -> None:
    content_lines1 = [
        "existing line 1",
        "existing line 4",
    ]

    existing_content_lines1 = [
        "existing line 1",
        "existing line 2",
        "existing line 3",
        "existing line 4",
    ]

    assert (
        add_missing_lines(content_lines1, existing_content_lines1)
        == existing_content_lines1
    )

    content_lines2 = [
        "existing line 1",
        "existing line 3",
    ]

    existing_content_lines2 = [
        "existing line 1",
        "existing line 2",
        "existing line 3",
        "existing line 4",
    ]

    assert add_missing_lines(content_lines2, existing_content_lines2) == [
        "existing line 1",
        "existing line 2",
        "existing line 3",
    ]

    content_lines3 = [
        "existing line 1",
        "existing line 3",
    ]

    existing_content_lines3 = [
        "existing line 1",
        "existing line 2",
        "existing line 3",
        "existing line 4",
    ]

    assert add_missing_lines(content_lines3, existing_content_lines3) == content_lines3


def test_removing_non_existing_lines() -> None:
    existing_content_lines = [
        "existing line 1",
        "existing line 2",
        "existing line 3",
        "existing line 4",
    ]

    content_lines1 = [
        "existing line 1",
        "existing line 2",
        "non existing line 1",
        "existing line 3",
        "existing line 4",
    ]

    assert (
        remove_non_existing_lines(content_lines1, existing_content_lines)
        == existing_content_lines
    )

    content_lines2 = [
        "existing line 1",
        "existing line 2",
        "non existing line 1",
    ]

    assert remove_non_existing_lines(content_lines2, existing_content_lines) == [
        "existing line 1",
        "existing line 2",
    ]

    content_lines3 = [
        "non existing line 1",
        "existing line 1",
        "existing line 2",
    ]

    assert remove_non_existing_lines(content_lines3, existing_content_lines) == [
        "existing line 1",
        "existing line 2",
    ]


def test_case(code_editor: CodeEditor) -> None:
    diff = '''\
--- tests/test_api.py
+++ tests/test_api.py
@@ ... @@
 def test_divide_by_zero(client: starlette.testclient.TestClient) -> None:
     """Test that the division endpoint returns a 400 when dividing by 0."""

     # GIVEN the division path and two numbers to divide
     path = "/v1/maths/division"
     body = {"number1": 2, "number2": 0}

     # WHEN calling the api
     response = client.post(path, json=body)

     # THEN the status code should be 400 (Bad request)
     assert response.status_code == 400

+def test_exponentiation(client: starlette.testclient.TestClient) -> None:
+    """Test that the exponentiation endpoint correctly calculates A^B."""
+    response = client.post("/exponentiation", json={"A": 2, "B": 3})
+    assert response.status_code == 200
+    assert response.json() == {"result": 8}
+
+
'''

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
    response = client.post("/exponentiation", json={"A": 2, "B": 3})
    assert response.status_code == 200
    assert response.json() == {"result": 8}


''',
    )

    assert code_editor.apply_diff(diff, file) == expected


def test_case1(code_editor: CodeEditor) -> None:
    diff = '''\
--- tests/test_api.py
+++ tests/test_api.py
@@ ... @@
 def test_divide_by_zero(client: starlette.testclient.TestClient) -> None:
     """Test that the division endpoint returns a 400 when dividing by 0."""
 
     # GIVEN the division path and two numbers to divide
     path = "/v1/maths/division"
     body = {"number1": 2, "number2": 0}
 
     # WHEN calling the api
     response = client.post(path, json=body)
 
     # THEN the status code should be 400 (Bad request)
     assert response.status_code == 400
 
+def test_exponentiation(client: starlette.testclient.TestClient) -> None:
+    """Test that the exponentiation endpoint correctly calculates A^B."""
+    # GIVEN the exponentiation path and two numbers to exponentiate
+    path = "/exponentiation"
+    body = {"number1": 2, "number2": 3}
+
+    # WHEN calling the api
+    response = client.post(path, json=body)
+
+    # THEN the result should be 8
+    assert response.json().get("result") == 8
+
+
'''

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


def test_case2(code_editor: CodeEditor) -> None:
    diff = '''\
--- tests/test_api.py
+++ tests/test_api.py
@@ ... @@
     # THEN the result should be 8
     assert response.json().get("result") == 8
 
-
-The test fixture "client" is defined in conftest.py
-These tests are trivial examples, they are not meant as an introduction to
-proper testing.
'''

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
