import difflib
import logging
import re
import subprocess
from dataclasses import dataclass

from diff_match_patch import diff_match_patch

from acedev.service.git_repository import GitRepository
from acedev.service.model import File

logger = logging.getLogger(__name__)


@dataclass
class CodeEditor:

    @staticmethod
    def apply_diff(diff: str, file: File) -> File:
        file_content = file.content
        diff = add_suffix_context(diff, file_content)
        hunks = split_diff_into_hunks(diff)
        for hunk in hunks:
            before, after = split_hunk_to_before_after(hunk)
            before = remove_non_existing_lines(before, file_content)
            norm_diff = normalize_diff(before, after, file.path)

            # Create a temporary file to hold the original content
            filename = file.path.split("/")[-1]
            tmp_path = f"/tmp/{filename}"
            with open(tmp_path, "w") as f:
                f.write(file_content)

            diff_path = f"/tmp/{filename}.diff"
            with open(diff_path, "w") as f:
                f.write(norm_diff)

            # Prepare the patch command, reading from stdin with '-'
            command = ["patch", "--verbose", tmp_path, diff_path]

            # Execute the patch command, providing the patch content via stdin
            process = subprocess.run(
                command, text=True, capture_output=True
            )

            # Check the result
            if process.returncode == 0:
                logger.info(f"Patch applied successfully:\n{process.stdout}")
                # Read the patched content
                with open(tmp_path, "r") as f:
                    patched_content = f.read()

                # Clean up the temporary file
                subprocess.run(["rm", f"{tmp_path}*"])

                file_content = patched_content
            else:
                logger.error(f"Failed to apply patch: {process.stdout}")
                # Clean up the temporary file
                subprocess.run(["rm", f"{tmp_path}*"])
                raise CodeEditorException(
                    f"Failed to apply diff to {file.path}: {process.stdout}"
                )

        return File(path=file.path, content=file_content)


class CodeEditorException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def split_diff_into_hunks(diff: str) -> list[str]:
    # Pattern to identify the start of hunks
    hunk_start_pattern = re.compile(r'^@@.*?@@', re.MULTILINE)

    # Find all match positions (start of each hunk)
    hunk_starts = [match.start() for match in hunk_start_pattern.finditer(diff)]

    # Split the diff text into hunks using the identified positions
    hunks = [diff[hunk_starts[i]:hunk_starts[i+1]-1] for i in range(len(hunk_starts)-1)]
    # Add the last hunk
    hunks.append(diff[hunk_starts[-1]:])

    return hunks


def split_hunk_to_before_after(
    hunk: str, as_lines: bool = False
) -> tuple[list[str], list[str]] | tuple[str, str]:
    before = []
    after = []

    for line in hunk.splitlines(keepends=True):
        if line.startswith("---") or line.startswith("+++") or line.startswith("@@"):
            continue

        if len(line) < 1:
            before.append(line)
            after.append(line)
            continue

        op = line[0]
        line_content = line[1:]

        match op:
            case " ":
                before.append(line_content)
                after.append(line_content)
            case "-":
                before.append(line_content)
            case "+":
                after.append(line_content)
            case _:
                logger.warning(
                    f"Can't parse a diff hunk line: {line}. Adding to both before and after."
                )
                before.append(line)
                after.append(line)

    if as_lines:
        return before, after

    return "".join(before), "".join(after)


def remove_non_existing_lines(content: str, existing_content: str) -> str:
    existing_lines = existing_content.splitlines(keepends=True)
    result = []

    for line in content.splitlines(keepends=True):
        if line in existing_lines:
            result.append(line)
        else:
            logger.warning(f"Line not found in existing content: {line}")

    return "".join(result)


def normalize_diff(before: str, after: str, filename: str) -> str:
    before_lines = before.splitlines(keepends=True)
    after_lines = after.splitlines(keepends=True)
    diff = difflib.unified_diff(
        before_lines,
        after_lines,
        fromfile=filename,
        tofile=filename,
        n=max(len(before_lines), len(after_lines)),
    )
    return "".join(diff)


def add_suffix_context(diff: str, file_content: str):
    diff_lines = diff.splitlines(keepends=True)
    file_lines = file_content.splitlines(keepends=True)
    last_existing_line = ""
    for line in diff_lines:
        if line.startswith(" "):
            last_existing_line = line[1:]

    last_existing_line_index = file_lines.index(last_existing_line)

    if last_existing_line_index != len(file_lines) - 1:
        diff_lines.extend(" " + line for line in file_lines[last_existing_line_index + 1:last_existing_line_index + 4])

    return "".join(diff_lines)
