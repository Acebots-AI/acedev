import pytest

from acedev.service.model import File
from acedev.tools.code_editor import CodeEditor


@pytest.fixture
def code_editor():
    return CodeEditor()


def test_apply_diff_succeeds_for_ideal_diff(code_editor: CodeEditor) -> None:
    file = File(path="file.py", content='''\
existing line 1
existing line 2
existing line 3
''')

    diff = '''\
--- file.py
+++ file.py
@@ ... @@
 existing line 1
+new line 1
 existing line 2
'''

    expected = File(path="file.py", content='''\
existing line 1
new line 1
existing line 2
existing line 3
''')

    assert code_editor.apply_diff(diff, file) == expected


def test_apply_diff_succeeds_for_another_ideal_diff(code_editor: CodeEditor) -> None:
    file = File(path="file.py", content='''\
existing line 1
existing line 2
existing line 3
existing line 4
''')

    diff = '''\
--- file.py
+++ file.py
@@ ... @@
 existing line 3
+new line 2
 existing line 4
'''

    expected = File(path="file.py", content='''\
existing line 1
existing line 2
existing line 3
new line 2
existing line 4
''')

    assert code_editor.apply_diff(diff, file) == expected


def test_apply_diff_succeeds_for_multiple_hunks(code_editor: CodeEditor) -> None:
    file = File(path="file.py", content='''\
existing line 1
existing line 2
existing line 3
existing line 4
''')

    diff = '''\
--- file.py
+++ file.py
@@ ... @@
 existing line 1
+new line 1
 existing line 2

@@ ... @@
 existing line 3
+new line 2
 existing line 4
'''

    expected = File(path="file.py", content='''\
existing line 1
new line 1
existing line 2
existing line 3
new line 2
existing line 4
''')

    assert code_editor.apply_diff(diff, file) == expected


def test_apply_diff_succeeds_for_adding_empty_line(code_editor: CodeEditor) -> None:
    file = File(path="file.py", content='''\
existing line 1
existing line 2
existing line 3
existing line 4''')

    diff = '''\
--- file.py
+++ file.py
@@ ... @@
 existing line 4
+'''

    expected = File(path="file.py", content='''\
existing line 1
existing line 2
existing line 3
existing line 4
''')

    assert code_editor.apply_diff(diff, file) == expected