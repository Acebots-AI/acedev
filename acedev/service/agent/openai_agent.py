import logging
from dataclasses import dataclass
from typing import Iterator, Sequence, Callable

from acedev.service.agent import Agent
from acedev.service.model import AgentCompletionRequest, ChatMessage, ToolMessage, AssistantMessage
from acedev.service.openai_service import OpenAIService

logger = logging.getLogger(__name__)


@dataclass
class OpenAIAgent(Agent):
    model: str
    temperature: float
    openai_service: OpenAIService
    max_steps: int = 16

    def run(self, request: AgentCompletionRequest, tools: dict[str, Callable[..., str]]) -> Sequence[ChatMessage]:
        messages = request.messages.copy()
        output = []

        for _ in range(self.max_steps):
            response = self.openai_service.invoke_with_tools(
                messages=messages,
                tools=tools,
                model=self.model,
                temperature=self.temperature)

            logger.info(f"Function Calling response: {response}")

            if not response.tool_calls:
                # If there are no tool calls, add the final response and exit the loop
                output.append(response)
                break

            messages.append(response)
            output.append(response)

            for tool_call in response.tool_calls:
                function_name = tool_call.tool
                function_to_call = tools[function_name]
                function_response = function_to_call(**tool_call.arguments)
                logger.debug(f"Function response: {function_response}")
                tool_message = ToolMessage(content=function_response, tool_call_id=tool_call.id)
                messages.append(tool_message)
                output.append(tool_message)

        else:  # This clause executes if the loop was not broken out of, i.e., max_steps was reached
            logger.warning(f"Max steps reached: {self.max_steps}. Last 4 messages: {messages[-4:]}")
            output.append(AssistantMessage(content="Help me. I'm stuck 🤖"))  # TODO: Ask AI to analyse the problem

        return output

    def stream(self, request: AgentCompletionRequest, tools: dict[str, Callable[[str], str]]) -> Iterator[ChatMessage]:
        raise NotImplementedError
