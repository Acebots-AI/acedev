import pytest
from jinja2 import UndefinedError

from acedev.utils.prompts import prompt, render


def test_clean() -> None:
    tpl = """
    A test string"""
    assert render(tpl) == "A test string"

    tpl = """
    A test string
    """
    assert render(tpl) == "A test string"

    tpl = """
        A test
        Another test
    """
    assert render(tpl) == "A test\nAnother test"

    tpl = """A test
        Another test
    """
    assert render(tpl) == "A test\nAnother test"

    tpl = """
        A test line
            An indented line
    """
    assert render(tpl) == "A test line\n    An indented line"

    tpl = """
        A test line
            An indented line

    """
    assert render(tpl) == "A test line\n    An indented line"


def test_clean_escaped_linebreak() -> None:
    tpl = """
        A long test \
        that we break \
        in several lines
    """
    assert render(tpl) == "A long test that we break in several lines"

    tpl = """
        Break in \
        several lines \
        But respect the indentation
            on line breaks.
        And after everything \
        Goes back to normal
    """
    assert (
            render(tpl)
            == "Break in several lines But respect the indentation\n    on line breaks.\nAnd after everything Goes back to normal"  # noqa: E501
    )


def test_render_with_values() -> None:
    template = "Hello, {{ name }}!"
    values = {"name": "Spotify"}
    assert render(template, **values) == "Hello, Spotify!"


def test_render_without_values() -> None:
    template = "Hello, {{ name }}!"
    with pytest.raises(UndefinedError):
        render(template)


def test_render_jinja() -> None:
    """Make sure that we can use basic Jinja2 syntax, and give examples
    of how we can use it for basic use cases.
    """

    examples = ["one", "two"]
    prompt = render(
            """
        {% for e in examples %}
        Example: {{e}}
        {% endfor %}""",
        examples=examples,
    )
    assert prompt == "Example: one\nExample: two"

    examples = ["one", "two"]
    prompt = render(
        """
        {% for e in examples %}
        Example: {{e}}
        {% endfor -%}

        Final""",
        examples=examples,
    )
    assert prompt == "Example: one\nExample: two\nFinal"

    tpl = """
        {% if is_true %}
        true
        {% endif -%}

        final
        """
    assert render(tpl, is_true=True) == "true\nfinal"
    assert render(tpl, is_true=False) == "final"


def test_prompt_basic() -> None:
    @prompt
    def test_tpl(variable: str) -> None:
        """{{variable}} test"""

    assert test_tpl.template == "{{variable}} test"
    assert test_tpl.parameters == ["variable"]

    with pytest.raises(TypeError):
        test_tpl(v="test")

    p = test_tpl("test")
    assert p == "test test"

    p = test_tpl(variable="test")
    assert p == "test test"

    @prompt
    def test_single_quote_tpl(variable: str) -> None:
        "${variable} test"

    p = test_tpl("test")
    assert p == "test test"


def test_prompt_kwargs() -> None:
    @prompt
    def test_kwarg_tpl(var: str, other_var: str = "other") -> None:
        """{{var}} and {{other_var}}"""

    assert test_kwarg_tpl.template == "{{var}} and {{other_var}}"
    assert test_kwarg_tpl.parameters == ["var", "other_var"]

    p = test_kwarg_tpl("test")
    assert p == "test and other"

    p = test_kwarg_tpl("test", other_var="kwarg")
    assert p == "test and kwarg"

    p = test_kwarg_tpl("test", "test")
    assert p == "test and test"


def test_no_prompt() -> None:
    with pytest.raises(TypeError, match="template"):

        @prompt
        def test_empty(variable: str) -> None:
            pass

    with pytest.raises(TypeError, match="template"):

        @prompt
        def test_only_code(variable: str) -> str:
            return variable
