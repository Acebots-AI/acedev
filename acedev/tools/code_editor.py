import difflib
import logging
import re
import subprocess
from dataclasses import dataclass
from typing import Optional

from acedev.service.model import File

logger = logging.getLogger(__name__)


@dataclass
class CodeEditor:

    @staticmethod
    def apply_diff(diff: str, file: File) -> File:
        file_content = file.content
        hunks = split_diff_into_hunks(diff)
        for hunk in hunks:
            norm_diff_lines = normalize_diff(hunk.splitlines(keepends=True), file.path)
            norm_diff = "".join(norm_diff_lines)
            updated_file = run_patch_cli(file.path, file_content, norm_diff)

            if updated_file:
                file_content = updated_file
                continue

            fixed_honk = fix_hunk(
                hunk.splitlines(keepends=True),
                file.path,
                file_content.splitlines(keepends=True),
            )

            updated_file = run_patch_cli(file.path, file_content, fixed_honk)

            if updated_file:
                file_content = updated_file
                continue
            else:
                raise CodeEditorException(
                    f"Failed to apply diff to {file.path}: {norm_diff}"
                )

        return File(path=file.path, content=file_content)


def run_patch_cli(file_path: str, file_content: str, norm_diff: str) -> Optional[str]:
    # Create a temporary file to hold the original content
    filename = file_path.split("/")[-1]
    tmp_file_path = f"/tmp/{filename}"
    with open(tmp_file_path, "w") as f:
        f.write(file_content)

    # Create a temporary file to hold the diff
    tmp_diff_path = f"/tmp/{filename}.diff"
    with open(tmp_diff_path, "w") as f:
        f.write(norm_diff)

    # Prepare the patch command
    command = ["patch", "--verbose", tmp_file_path, tmp_diff_path]

    # Execute the patch command
    process = subprocess.run(command, text=True, capture_output=True)

    # Check the result
    if process.returncode == 0:
        logger.info(f"Patch applied successfully:\n{process.stdout}")
        # Read the patched content
        with open(tmp_file_path, "r") as f:
            patched_content = f.read()

        return patched_content
    else:
        logger.error(f"Failed to apply patch: {process.stdout}")
        # raise CodeEditorException(
        #     f"Failed to apply diff to {file_path}: {process.stdout}"
        # )
        return None


class CodeEditorException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def split_diff_into_hunks(diff: str) -> list[str]:
    # Pattern to identify the start of hunks
    hunk_start_pattern = re.compile(r"^@@.*?@@", re.MULTILINE)

    # Find all match positions (start of each hunk)
    hunk_starts = [match.start() for match in hunk_start_pattern.finditer(diff)]

    # Split the diff text into hunks using the identified positions
    hunks = [
        diff[hunk_starts[i] : hunk_starts[i + 1] - 1]
        for i in range(len(hunk_starts) - 1)
    ]
    # Add the last hunk
    hunks.append(diff[hunk_starts[-1] :])

    return hunks


def fix_hunk(
    hunk_lines: list[str], filename: str, file_content_lines: list[str]
) -> str:
    hunk_lines = add_suffix_context(hunk_lines, file_content_lines)
    before_lines, after_lines = split_hunk_to_before_after(hunk_lines, as_lines=True)
    before_lines = remove_non_existing_lines(before_lines, file_content_lines)
    before_lines = add_missing_lines(before_lines, file_content_lines)
    diff_lines = unified_diff(before_lines, after_lines, filename)

    for idx, line in enumerate(diff_lines):
        if line.startswith("---") or line.startswith("+++") or line.startswith("@@"):
            continue
        if line.startswith("-") and line not in hunk_lines:
            logger.warning(
                f"Removed line not found in original hunk: {line}. Leaving it in the diff."
            )
            diff_lines[idx] = " " + line[1:]

    diff_lines = normalize_diff(diff_lines, filename)
    return "".join(diff_lines)


def normalize_diff(diff_lines: list[str], filename: str) -> list[str]:
    before_lines, after_lines = split_hunk_to_before_after(diff_lines, as_lines=True)
    diff_lines = unified_diff(before_lines, after_lines, filename)
    return diff_lines


def split_hunk_to_before_after(
    hunk_lines: list[str], as_lines: bool = False
) -> tuple[list[str], list[str]] | tuple[str, str]:
    before = []
    after = []

    for line in hunk_lines:
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


def remove_non_existing_lines(
    content_lines: list[str], existing_content_lines: list[str]
) -> list[str]:
    result = []
    current_line_number = None
    for line in content_lines:
        if line in existing_content_lines:
            current_line_number = existing_content_lines.index(line)
            break

    if current_line_number is None:
        logger.warning(
            f"None of the lines in Before block found in existing content. \
            Dropping these lines: {content_lines}"
        )
        return result

    for idx, line in enumerate(content_lines):
        if current_line_number >= len(existing_content_lines):
            logger.warning(
                f"Reached end of file while removing non existing lines from Before block. \
                Dropping these lines: {content_lines[idx:]}"
            )
            break

        if line == existing_content_lines[current_line_number]:
            result.append(line)
            current_line_number += 1
        else:
            logger.warning(f"Line not found in existing content: {line}")
            if line in existing_content_lines[current_line_number:]:
                content_lines.append(line)
                current_line_number += 1

    return result


def add_missing_lines(
    content_lines: list[str], existing_content_lines: list[str]
) -> list[str]:
    current_line_number = existing_content_lines.index(content_lines[0])

    for idx, line in enumerate(content_lines):
        if current_line_number >= len(existing_content_lines):
            logger.warning(
                f"Reached end of file while adding missing lines to Before block. \
                Dropping these lines: {content_lines[idx:]}"
            )
            break

        if line != existing_content_lines[current_line_number]:
            logger.warning(
                f"Found missing line: {existing_content_lines[current_line_number]}"
            )
            content_lines.insert(idx, existing_content_lines[current_line_number])

        current_line_number += 1

    return content_lines


def unified_diff(
    before_lines: list[str], after_lines: list[str], filename: str
) -> list[str]:
    return list(
        difflib.unified_diff(
            before_lines,
            after_lines,
            fromfile=filename,
            tofile=filename,
            n=max(len(before_lines), len(after_lines)),
        )
    )


def add_suffix_context(diff_lines: list[str], file_lines: list[str]) -> list[str]:
    if diff_lines[-1].startswith(" "):
        return diff_lines

    last_existing_line = ""
    for line in diff_lines:
        if (line.startswith(" ") or line.startswith("-")) and line.strip():
            last_existing_line = line[1:]

    last_existing_line_index = file_lines.index(last_existing_line)

    if last_existing_line_index != len(file_lines) - 1:
        diff_lines.extend(
            " " + line
            for line in file_lines[
                last_existing_line_index + 1 : last_existing_line_index + 4
            ]
        )

    return diff_lines
