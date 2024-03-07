from abc import ABC, abstractmethod
from typing import Iterator, Sequence, Callable

from acedev.service.model import ChatMessage


class AgentRunner(ABC):
    @abstractmethod
    def stream(
        self, messages: list[ChatMessage], tools: Sequence[Callable[[str], str]]
    ) -> Iterator[ChatMessage]:
        pass

    @abstractmethod
    def run(
        self, messages: list[ChatMessage], tools: Sequence[Callable[[str], str]]
    ) -> Sequence[ChatMessage]:
        pass
