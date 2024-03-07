import inspect
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from jinja2 import Environment, StrictUndefined


@dataclass
class Prompt:
    template: str
    signature: inspect.Signature

    def __post_init__(self) -> None:
        self.parameters: List[str] = list(self.signature.parameters.keys())

    def __call__(self, *args: Any, **kwargs: Any) -> str:
        """Render and return the template.

        Returns
        -------
        The rendered template as a Python ``str``.

        """
        bound_arguments = self.signature.bind(*args, **kwargs)
        bound_arguments.apply_defaults()
        return render(self.template, **bound_arguments.arguments)

    def __str__(self) -> str:
        return self.template


def prompt(fn: Callable[..., None]) -> Prompt:
    """Decorate a function that contains a prompt template.

    This allows to define prompts in the docstring of a function and simplify their
    manipulation by providing some degree of encapsulation. It uses the `render`
    function internally to render templates.

    >>> @prompt
    >>> def my_prompt(name):
    ...    "Hello ${name}!"
    ...
    >>> prompt = my_prompt("world")

    Returns
    -------
    A `Prompt` callable class which will render the template when called.

    """

    signature = inspect.signature(fn)

    # The docstring contains the template that will be rendered to be used
    # as a prompt to the language model.
    docstring = fn.__doc__
    if docstring is None:
        raise TypeError("Could not find a template in the function's docstring.")

    return Prompt(docstring, signature)


def render(template: str, **values: Optional[Dict[str, Any]]) -> str:
    """Parse a Jinja2 template.

    This function removes extra whitespaces and linebreaks from templates to
    allow users to enter prompts more naturally than if they used Python's
    constructs directly.

    Parameters
    ----------
    template
        A string that contains a template written with the Jinja2 syntax.
    **values
        Map from the variables in the template to their value.

    Returns
    -------
    A string that contains the rendered template.

    """
    # Dedent, and remove extra linebreak
    cleaned_template = inspect.cleandoc(template)

    # Remove extra whitespaces, except those that immediately follow a newline symbol.
    # This is necessary to avoid introducing whitespaces after backslash `\` characters
    # used to continue to the next line without linebreak.
    cleaned_template = re.sub(r"(?![\r\n])(\b\s+)", " ", cleaned_template)

    env = Environment(
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        undefined=StrictUndefined,
    )

    jinja_template = env.from_string(cleaned_template)

    return jinja_template.render(**values).rstrip()
