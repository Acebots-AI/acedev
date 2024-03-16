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
            before, after = split_hunk_to_before_after(hunk.splitlines(keepends=True))
            updated_file = find_and_replace(file_content, before, after)

            if updated_file != file_content:
                file_content = updated_file
                continue

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
    original_before, original_after = split_hunk_to_before_after(hunk_lines, as_lines=True)
    reconciled_before = reconcile_subsequence(original_before, file_content_lines)
    # dirty because might remove lines that are not supposed to be removed
    dirty_diff = unified_diff(reconciled_before, original_after, filename)
    reconciled_diff = reconcile_diffs(dirty_diff, hunk_lines)
    reconciled_before, reconciled_after = split_hunk_to_before_after(reconciled_diff, as_lines=True)
    reconciled_hunk = unified_diff(reconciled_before, reconciled_after, filename)
    return "".join(reconciled_hunk)


def normalize_diff(diff_lines: list[str], filename: str) -> list[str]:
    before_lines, after_lines = split_hunk_to_before_after(diff_lines, as_lines=True)
    diff_lines = unified_diff(before_lines, after_lines, filename)
    return diff_lines


def split_hunk_to_before_after(
    hunk_lines: list[str], as_lines: bool = False
) -> tuple[list[str], list[str]] | tuple[str, str]:
    before: list[str] = []
    after: list[str] = []

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


def reconcile_subsequence(subsequence: list[str], superset: list[str], extra_lines: int = 3) -> list[str]:
    """
    Reconciles a subsequence of text with the original superset of lines.
    
    Args:
        subsequence (list[str]): The subsequence to evaluate.
        superset (list[str]): The original superset of lines.
    
    Returns:
        list[str]: The reconciled subsequence.
    """
    reconciled: list[str] = []
    superset_index = 0
    subsequence_index = 0

    while subsequence_index < len(subsequence) and superset_index < len(superset):
        if subsequence[subsequence_index] == superset[superset_index]:
            reconciled.append(subsequence[subsequence_index])
            subsequence_index += 1
            superset_index += 1
        elif subsequence[subsequence_index] in superset[superset_index:]:
            # If the current line in subsequence exists further in the superset,
            # add missing lines from the superset to the reconciled list
            next_correct_index = superset.index(subsequence[subsequence_index], superset_index)
            reconciled.extend(superset[superset_index:next_correct_index])
            superset_index = next_correct_index
        else:
            # Remove non-existing lines from the subsequence
            subsequence_index += 1

    # Add any remaining lines from the superset to the reconciled list
    if superset_index < len(superset):
        reconciled.extend(superset[superset_index : superset_index + extra_lines])

    return reconciled


def reconcile_diffs(current_diff: list[str], original_diff: list[str]) -> list[str]:
    """
    Takes two unified diffs and converts removed lines from the first one into unchanged if they are not removed in the second one as well.

    Args:
        current_diff (list[str]): The current unified diff list.
        original_diff (list[str]): The original unified diff list.

    Returns:
        list[str]: The reconciled unified diff.
    """
    reconciled_diff: list[str] = []
    for line in current_diff:
        if line.startswith("---") or line.startswith("+++") or line.startswith("@@"):
            reconciled_diff.append(line)
        elif line.startswith('-') and not line in original_diff:
            reconciled_diff.append(" " + line[1:])
        else:
            reconciled_diff.append(line)
    return reconciled_diff


def find_and_replace(file_content: str, old_text: str, new_text: str) -> str:
    """
    Finds and replaces all occurrences of old_text with new_text in the given file_content.

    Args:
        file_content (str): The content of the file as a string.
        old_text (str): The text to be replaced.
        new_text (str): The text to replace with.

    Returns:
        str: The updated file content with all occurrences of old_text replaced by new_text.
    """
    return file_content.replace(old_text, new_text)
