from unittest.mock import create_autospec

import pytest
from tree_sitter_languages import get_parser, get_language

from acedev.service.gitrepository import GitRepository
from acedev.service.model import File, Symbol
from acedev.service.symbol_manipulator import (
    SymbolManipulator,
    SymbolManipulatorException,
)


@pytest.fixture
def git_repository() -> GitRepository:
    return create_autospec(GitRepository)


@pytest.fixture
def symbol_manipulator(git_repository: GitRepository) -> SymbolManipulator:
    return SymbolManipulator(
        git_repository, get_parser("python"), get_language("python")
    )


@pytest.fixture
def file1() -> File:
    return File(
        path="file1.py",
        content="""\
import logging

logger = logging.getLogger(__name__)

CONSTANT = "constant"

def my_func():
    pass

class MyClass:
    def my_method(self):
        pass

    def my_method2(self):
        pass
""",
    )


@pytest.fixture
def file2() -> File:
    return File(
        path="file2.py",
        content="""\
from datetime import datetime

@my_decorator
def my_func(param1: str, param2: int) -> None:
    pass
""",
    )


def test_get_project_outline(
    symbol_manipulator: SymbolManipulator, file1: File, file2: File
) -> None:
    assert (
        symbol_manipulator.get_project_outline([file1, file2])
        == """\
file1.py:
import logging
logger = logging.getLogger(__name__)
CONSTANT = "constant"
def my_func()
class MyClass:
    def my_method(self)
    def my_method2(self)

file2.py:
from datetime import datetime
@my_decorator
def my_func(param1: str, param2: int) -> None\
"""
    )


def test_get_symbol_class(symbol_manipulator: SymbolManipulator, file1: File) -> None:
    result = symbol_manipulator.get_symbol("MyClass", file1)

    assert result == Symbol(
        content="""\
class MyClass:
    def my_method(self):
        pass

    def my_method2(self):
        pass\
""",
        path="file1.py",
    )


def test_get_symbol_function(
    symbol_manipulator: SymbolManipulator, file1: File
) -> None:
    result = symbol_manipulator.get_symbol("my_func", file1)

    assert result == Symbol(
        content="""\
def my_func():
    pass\
""",
        path="file1.py",
    )


# Fixme: The indentation of the symbol below is wrong, it should be indented by 4 spaces
def test_get_symbol_method(symbol_manipulator: SymbolManipulator, file1: File) -> None:
    result = symbol_manipulator.get_symbol("my_method", file1)

    assert result == Symbol(
        content="""\
def my_method(self):
        pass\
""",
        path="file1.py",
    )


# Fixme: The returned function has no decorator
def test_get_symbol_function_with_decorator(
    symbol_manipulator: SymbolManipulator, file2: File
) -> None:
    result = symbol_manipulator.get_symbol("my_func", file2)

    assert result == Symbol(
        content="""\
def my_func(param1: str, param2: int) -> None:
    pass\
""",
        path="file2.py",
    )


def test_get_symbol_not_found(
    symbol_manipulator: SymbolManipulator, file2: File
) -> None:
    assert symbol_manipulator.get_symbol("non_existing_symbol", file2) is None


def test_update_symbol_in_file_function(
    symbol_manipulator: SymbolManipulator, file1: File
) -> None:
    expected = File(
        path="file1.py",
        content="""\
import logging

logger = logging.getLogger(__name__)

CONSTANT = "constant"

def my_func():
    print("Hello, World!")

class MyClass:
    def my_method(self):
        pass

    def my_method2(self):
        pass
""",
    )

    new_symbol = """\
def my_func():
    print("Hello, World!")\
"""
    result = symbol_manipulator.update_symbol("my_func", new_symbol, file1)

    assert result == expected


def test_update_symbol_in_file_class(
    symbol_manipulator: SymbolManipulator, file1: File
) -> None:
    expected = File(
        path="file1.py",
        content="""\
import logging

logger = logging.getLogger(__name__)

CONSTANT = "constant"

def my_func():
    pass

class MyClass:
    def my_method(self):
        print("Hello, World!")

    def my_method2(self):
        print("Hello, World!")
        
    def my_method3(self):
        print("Hello, World!")
""",
    )

    new_symbol = """\
class MyClass:
    def my_method(self):
        print("Hello, World!")

    def my_method2(self):
        print("Hello, World!")
        
    def my_method3(self):
        print("Hello, World!")\
"""
    result = symbol_manipulator.update_symbol("MyClass", new_symbol, file1)

    assert result == expected


# Fixme: The indentation of the method body is wrong, it should be indented by 8 spaces
def test_update_symbol_in_file_method(
    symbol_manipulator: SymbolManipulator, file1: File
) -> None:
    expected = File(
        path="file1.py",
        content="""\
import logging

logger = logging.getLogger(__name__)

CONSTANT = "constant"

def my_func():
    pass

class MyClass:
    def my_method(self):
        pass

    def my_method2(self):
    print("Hello, World!")
""",
    )

    new_symbol = """\
def my_method2(self):
    print("Hello, World!")\
"""
    result = symbol_manipulator.update_symbol("my_method2", new_symbol, file1)

    assert result == expected


# Fixme: The update files has 2 decorators and an extra newline at the end
def test_update_symbol_in_file_function_with_decorator(
    symbol_manipulator: SymbolManipulator, file2: File
) -> None:
    expected = File(
        path="file2.py",
        content="""\
from datetime import datetime

@my_decorator
@my_decorator
def my_func(param1: str, param2: int) -> None:
    print("Hello, World!")
\
""",
    )

    new_symbol = """\
@my_decorator
def my_func(param1: str, param2: int) -> None:
    print("Hello, World!")\
"""
    result = symbol_manipulator.update_symbol("my_func", new_symbol, file2)

    assert result == expected


def test_update_symbol_not_found(
    symbol_manipulator: SymbolManipulator, file2: File
) -> None:
    with pytest.raises(SymbolManipulatorException):
        symbol_manipulator.update_symbol("non_existing_symbol", "new_content", file2)


def test_update_symbol_fails_to_parse(
    symbol_manipulator: SymbolManipulator, file1: File
) -> None:
    with pytest.raises(SymbolManipulatorException):
        symbol_manipulator.update_symbol(
            "my_func",
            """\
def my_func():
    print("Hello, World!"\
""",
            file1,
        )


def test_update_symbol_multiple_expressions(
    symbol_manipulator: SymbolManipulator, file1: File
) -> None:
    with pytest.raises(SymbolManipulatorException):
        symbol_manipulator.update_symbol(
            "my_func",
            """\
import os

def my_func():
    print("Hello, World!")\
    """,
            file1,
        )


def test_update_symbol_wrong_type(
    symbol_manipulator: SymbolManipulator, file1: File
) -> None:
    with pytest.raises(SymbolManipulatorException):
        symbol_manipulator.update_symbol(
            "my_func",
            """\
class MyNewClass:
    pass\
""",
            file1,
        )


def test_update_symbol_wrong_name(
    symbol_manipulator: SymbolManipulator, file1: File
) -> None:
    with pytest.raises(SymbolManipulatorException):
        symbol_manipulator.update_symbol(
            "my_func",
            """\
def my_new_func():
    pass\
""",
            file1,
        )


def test_add_symbol_class(symbol_manipulator: SymbolManipulator, file1: File) -> None:
    expected = File(
        path="file1.py",
        content="""\
import logging

logger = logging.getLogger(__name__)

CONSTANT = "constant"

def my_func():
    pass

class MyClass:
    def my_method(self):
        pass

    def my_method2(self):
        pass


class MyNewClass:
    pass
""",
    )

    new_symbol = """\
class MyNewClass:
    pass\
"""
    result = symbol_manipulator.add_symbol("MyNewClass", new_symbol, file1)

    assert result == expected


def test_add_symbol_function(
    symbol_manipulator: SymbolManipulator, file2: File
) -> None:
    expected = File(
        path="file2.py",
        content="""\
from datetime import datetime

@my_decorator
def my_func(param1: str, param2: int) -> None:
    pass


def my_new_func():
    pass
""",
    )

    new_symbol = """\
def my_new_func():
    pass\
"""
    result = symbol_manipulator.add_symbol("my_new_func", new_symbol, file2)

    assert result == expected


def test_add_fails_if_symbol_exists(
    symbol_manipulator: SymbolManipulator, file2: File
) -> None:
    with pytest.raises(SymbolManipulatorException):
        symbol_manipulator.add_symbol("my_func", "content", file2)


def test_add_symbol_fails_to_parse(
    symbol_manipulator: SymbolManipulator, file2: File
) -> None:
    with pytest.raises(SymbolManipulatorException):
        symbol_manipulator.add_symbol(
            "my_new_func",
            """\
def my_new_func():
    print("Hello, World!"\
""",
            file2,
        )


def test_add_symbol_multiple_expressions(
    symbol_manipulator: SymbolManipulator, file2: File
) -> None:
    with pytest.raises(SymbolManipulatorException):
        symbol_manipulator.add_symbol(
            "my_new_func",
            """\
import os
            
def my_new_func():
    print("Hello, World!")\
""",
            file2,
        )


def test_add_symbol_fails_if_name_does_not_match(
    symbol_manipulator: SymbolManipulator, file2: File
) -> None:
    with pytest.raises(SymbolManipulatorException):
        symbol_manipulator.add_symbol(
            "my_new_func",
            """\
def another_func():
    pass\
""",
            file2,
        )


def test_add_imports(symbol_manipulator: SymbolManipulator, file2: File) -> None:
    expected = File(
        path="file2.py",
        content="""\
import os
import sys
from datetime import datetime

@my_decorator
def my_func(param1: str, param2: int) -> None:
    pass
""",
    )

    result = symbol_manipulator.add_imports(["import os", "import sys"], file2)

    assert result == expected


def test_replace_imports(symbol_manipulator: SymbolManipulator, file2: File) -> None:
    expected = File(
        path="file2.py",
        content="""\
import os

@my_decorator
def my_func(param1: str, param2: int) -> None:
    pass
""",
    )

    result = symbol_manipulator.replace_imports(
        ["from datetime import datetime"], ["import os"], file2
    )

    assert result == expected
