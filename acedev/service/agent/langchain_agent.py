from typing import Sequence, Callable, Iterator

from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain_community.chat_models import ChatOpenAI
from langchain_core import messages
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.utils.function_calling import convert_to_openai_tool

from acedev.service.agent import Agent
from acedev.service.model import AgentCompletionRequest, ChatMessage, ToolCall

DEFAULT_SYSTEM_PROMPT = "You are a software engineer who writes high-quality code. You are efficient and concise."


class LangchainAgent(Agent):
    def __init__(self, tools: Sequence[Callable], model: str = "gpt-4", temperature: float = 0,
                 system_message: str = DEFAULT_SYSTEM_PROMPT) -> None:
        llm = ChatOpenAI(model=model, temperature=temperature)
        llm_with_tools = llm.bind(tools=[convert_to_openai_tool(t) for t in tools])

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_message,),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        agent = (
                RunnablePassthrough.assign(
                    agent_scratchpad=lambda x: format_to_openai_tool_messages(
                        x["intermediate_steps"]
                    )
                )
                | prompt
                | llm_with_tools
                | OpenAIToolsAgentOutputParser()
        )

        self.agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    def stream(self, request: AgentCompletionRequest) -> Iterator[ChatMessage]:
        # TODO: handle message history
        for chunk in self.agent_executor.stream({"input": request.messages[0].content}):
            tool_calls = None

            if "actions" in chunk:
                tool_calls = []
                for action in chunk["actions"]:
                    tool_calls.append(ToolCall(tool=action.tool, tool_input=action.tool_input))

            for message in chunk.get("messages", []):
                role = self._role_from_langchain_type(message)
                yield ChatMessage(role=role, content=message.content, tool_calls=tool_calls)

    @staticmethod
    def _role_from_langchain_type(message: BaseMessage) -> str:
        match message:
            case messages.AIMessageChunk() | messages.AIMessage():
                return "assistant"
            case messages.ToolMessage() | messages.ToolMessageChunk() | messages.FunctionMessage() | messages.FunctionMessageChunk():
                return "tool"
            case messages.HumanMessage() | messages.HumanMessageChunk():
                return "user"
            case _:
                raise AgentException(f"Unknown message type: {type(message).__name__}")


class AgentException(Exception):
    def __init(self, message: str) -> None:
        super().__init__(message)
