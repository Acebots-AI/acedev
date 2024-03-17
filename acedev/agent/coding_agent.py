import logging
import re
from dataclasses import dataclass

from acedev.agent.prompts import coding_agent_system_prompt
from acedev.service.model import (
    UserMessage,
    SystemMessage,
    File,
)
from acedev.service.openai_service import OpenAIService
from acedev.tools.code_editor import CodeEditor, CodeEditorException

logger = logging.getLogger(__name__)


@dataclass
class CodingAgent:
    code_editor: CodeEditor
    openai_service: OpenAIService
    model: str
    temperature: float
    max_retries: int

    def edit_file(self, instructions: str, file: File) -> File:
        """
        Edit the file in the given task using the LLM agent.
        """
        messages = [
            SystemMessage(content=coding_agent_system_prompt()),
            UserMessage(
                content=f"Instructions: {instructions}.\n```{file.path}\n{file.content}```"
            ),
        ]

        for attempt in range(self.max_retries):
            try:
                response = self.openai_service.invoke(
                    messages, model=self.model, temperature=self.temperature
                )
                pattern = r"```diff(.*?)```"
                matches = re.findall(pattern, response.content, re.DOTALL)
                if not matches:
                    logger.warning(f"No diff found in response on attempt {attempt + 1}: {response.content}")
                    messages.append(SystemMessage(content=f"No diff found in response. Make sure to wrap diff \
                                                  inside triple ticks with the diff identifier, e.g. ```diff ...```."))
                    continue

                if len(matches) > 1:
                    logger.warning(
                        f"Multiple diffs found in response on attempt {attempt + 1}: {response.content}"
                    )
                    messages.append(SystemMessage(content=f"Multiple diffs found in response. Please respond with just one diff."))
                    continue

                diff = matches[0]
                logger.info(f"Applying diff to {file.path}:\n{diff}")
                return self.code_editor.apply_diff(diff, file)
            except CodeEditorException as e:
                logger.warning(f"Attempt {attempt + 1} failed, retrying. Error: {e}")
                messages.append(SystemMessage(content=f"Retry attempt {attempt + 1} due to error: {e}"))
        else:
            raise CodingAgentException(
                f"All {self.max_retries} attempts to edit the file have failed."
            )

class CodingAgentException(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
