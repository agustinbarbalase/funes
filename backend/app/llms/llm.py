from abc import ABC, abstractmethod
from typing import TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLM(ABC):

    @abstractmethod
    def invoke_structured(self, prompt: str, output_type: type[T]) -> T:
        pass
