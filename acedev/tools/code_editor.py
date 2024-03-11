import logging
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
        diff_lines = diff.splitlines()

        if diff_lines[0].startswith("---") and diff_lines[1].startswith("+++"):
            diff = "\n".join(diff_lines[2:])
        else:
            logger.warning(f"Diff does not start with file paths: {diff_lines[0:2]}")

        try:
            patch = self.dmp.patch_fromText(diff)
            content, _ = self.dmp.patch_apply(patch, file.content)

            return File(path=file.path, content=content)
        except Exception as e:
            raise CodeEditorException(f"Failed to apply diff to {file.path}: {e}")


class CodeEditorException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def split_hunk_into_before_and_after(hunk: str) -> tuple[str, str]:
    before = []
    after = []
    for line in hunk.splitlines():
        if line.startswith("-"):
            before.append(line)
        elif line.startswith("+"):
            after.append(line)
        else:
            before.append(line)
            after.append(line)
    return "\n".join(before), "\n".join(after)
