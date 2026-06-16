import os
import re
from ollama import Client
from pydantic import BaseModel
from typing import TypeVar
from app.llms.llm import LLM

T = TypeVar("T", bound=BaseModel)


class OllamaLLM(LLM):

    def __init__(self):
        self._client = Client(
            host="https://ollama.com",
            headers={"Authorization": f"Bearer {os.environ['OLLAMA_API_KEY']}"},
        )

    def invoke_structured(self, prompt: str, output_type: type[T]) -> T:
        response = self._client.chat(
            model="gemma3:12b",
            messages=[
                {
                    "role": "user",
                    "content": f"{prompt}\n\nRespondé ÚNICAMENTE con un JSON válido que siga este schema, sin texto adicional:\n{output_type.model_json_schema()}",
                }
            ],
            format=output_type.model_json_schema(),
        )

        content = response.message.content

        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            content = match.group(0)

        return output_type.model_validate_json(content)
