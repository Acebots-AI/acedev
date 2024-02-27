from abc import ABC, abstractmethod
from typing import Iterator, Sequence, Callable

from acedev.service.model import AgentCompletionRequest, ChatMessage


class Agent(ABC):
    @abstractmethod
    def stream(self, request: AgentCompletionRequest, tools: Sequence[Callable[[str], str]]) -> Iterator[ChatMessage]:
        pass

    @abstractmethod
    def run(self, request: AgentCompletionRequest, tools: Sequence[Callable[[str], str]]) -> Sequence[ChatMessage]:
        pass
