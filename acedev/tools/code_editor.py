import difflib
import logging
import subprocess
from dataclasses import dataclass

from diff_match_patch import diff_match_patch

from acedev.service.git_repository import GitRepository
from acedev.service.model import File

logger = logging.getLogger(__name__)


@dataclass
class CodeEditor:
    git_repository: GitRepository
    dmp: diff_match_patch

    def apply_diff(self, diff: str, file: File) -> File:
        before, after = split_hunk_to_before_after(diff)
        norm_diff = normalize_diff(before, after, file.path)

        # Create a temporary file to hold the original content
        filename = file.path.split("/")[-1]
        tmp_path = f"/tmp/{filename}"
        with open(tmp_path, "w") as f:
            f.write(file.content)

        # Prepare the patch command, reading from stdin with '-'
        command = ["patch", "--verbose", tmp_path, "-"]

        # Execute the patch command, providing the patch content via stdin
        process = subprocess.run(
            command, input=norm_diff, text=True, capture_output=True
        )

        # Check the result
        if process.returncode == 0:
            logger.info(f"Patch applied successfully:\n{process.stdout}")
            # Read the patched content
            with open(tmp_path, "r") as f:
                patched_content = f.read()

            # Clean up the temporary file
            subprocess.run(["rm", f"{tmp_path}*"])

            return File(path=file.path, content=patched_content)
        else:
            logger.error("Failed to apply patch:", process.stderr)
            # Clean up the temporary file
            subprocess.run(["rm", f"{tmp_path}*"])
            raise CodeEditorException(
                f"Failed to apply diff to {file.path}: {process.stderr}"
            )


class CodeEditorException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def split_hunk_to_before_after(
    hunk: str, as_lines: bool = False
) -> tuple[list[str], list[str]] | tuple[str, str]:
    before = []
    after = []

    for line in hunk.splitlines():
        if line.startswith("---") or line.startswith("+++") or line.startswith("@@"):
            continue

        if len(line) < 1:
            before.append(line)
            after.append(line)
            continue

        op = line[0]
        line = line[1:]

        match op:
            case " ":
                before.append(line)
                after.append(line)
            case "-":
                before.append(line)
            case "+":
                after.append(line)
            case _:
                logger.warning(f"Can't parse a diff hunk line: {line}")

    if as_lines:
        return before, after

    return "\n".join(before), "\n".join(after)


def normalize_diff(before: str, after: str, filename: str) -> str:
    before_lines = before.splitlines()
    after_lines = after.splitlines()
    diff = difflib.unified_diff(
        before_lines,
        after_lines,
        fromfile=filename,
        tofile=filename,
        n=max(len(before_lines), len(after_lines)),
        lineterm="",
    )
    return "\n".join(diff)
