from abc import ABC, abstractmethod


class AIProvider(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_output_tokens: int,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def embed(
        self,
        text: str,
        model: str,
    ) -> list[float]:
        raise NotImplementedError