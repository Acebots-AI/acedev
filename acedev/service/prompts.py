from typing import Sequence

from acedev.service.model import File, PullRequest, Symbol
from acedev.utils.prompts import prompt


@prompt
def create_pull_request_prompt(
    task: str, project_files: set[File], output_format_instruction: str
) -> None:
    """
    Update the project to implement the task.

    Project files:
    {% for file in project_files %}
    {{ file.path }}
    ```
    {{ file.content }}
    ```
    ---------------------
    {% endfor %}

    Task:
    {{ task }}
    ---------------------

    Output format:
    {{ output_format_instruction }}
    ---------------------
    """


@prompt
def update_pull_request_prompt(
    comment: str,
    pull_request: PullRequest,
    project_files: Sequence[File],
    output_format_instruction: str,
) -> None:
    """
    Update the pull request to address the comment.

    Project files:
    {% for file in project_files %}
    {{ file.path }}
    ```
    {{ file.content }}
    ```
    ---------------------
    {% endfor %}

    Comment:
    {{ comment }}
    ---------------------

    Pull request:
    {% for file in pull_request.files %}
    {{ file.status }} {{ file.filename }}
    {{ file.diff }}
    ---------------------
    {% endfor %}

    Output format:
    {{ output_format_instruction }}
    ---------------------
    """


@prompt
def plan_symbol_lookup_prompt(task: str, project_outline: str, output_format_instruction: str,) -> None:
    """
    {{ task }}

    Here's the high-level overview of the project. The implementation details are omitted for brevity:
    {{ project_outline }}
    ---------------------

    Which functions or classes do you want to expand before jumping to implementation?

    Output format:
    {{ output_format_instruction }}
    ---------------------
    """


@prompt
def create_plan(symbols: set[Symbol], output_format_instruction: str) -> None:
    """
    Expanded symbols:
    {% for symbol in symbols %}
    {{ symbol.path }}
    ```
    ...
    {{ symbol.content }}
    ...
    ```
    ---------------------
    {% endfor %}

    Describe your plan for implementation. List all the files that you would like to add, update or remove.

    Output format:
    {{ output_format_instruction }}
    ---------------------
    """