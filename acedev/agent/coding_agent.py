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
from acedev.tools.code_editor import CodeEditor

logger = logging.getLogger(__name__)


@dataclass
class CodingAgent:
    code_editor: CodeEditor
    openai_service: OpenAIService
    model: str
    temperature: float

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

        response = self.openai_service.invoke(
            messages, model=self.model, temperature=self.temperature
        )
        pattern = r"```diff(.*?)```"
        matches = re.findall(pattern, response.content, re.DOTALL)
        if not matches:
            raise ValueError(f"No diff found in response: {response.content}")

        if len(matches) > 1:
            raise ValueError(f"Multiple diffs found in response: {response.content}")

        diff = matches[0]
        logger.info(f"Applying diff to {file.path}:\n{diff}")

        return self.code_editor.apply_diff(diff, file)
