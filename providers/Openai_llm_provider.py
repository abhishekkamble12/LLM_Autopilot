# OpenAI-backed provider implementation.
import asyncio
import os
from typing import Any, Dict, List, Optional

try:
    from openai import OpenAI
    from openai import APIStatusError as OpenAIError
except ImportError:  # pragma: no cover - fallback for older SDK layouts
    from openai import OpenAI
    from openai import OpenAIError

from providers.init import BaseProvider


class Openai_llm_provider(BaseProvider):
    def __init__(self, name_model: str, temperature: float = 0.7, max_tokens: int = 150):
        self.name_model = name_model
        self.temperature = temperature
        self.max_tokens = max_tokens

    async def chat(self, message: str, context: Optional[List[Dict[str, Any]]] = None):
        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=self.name_model,
                messages=[{"role": "user", "content": message}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return response.choices[0].message.content
        except OpenAIError as exc:
            print(f"OpenAI API error: {exc}")
            return None

    async def embedding(self, text: str) -> List[float]:
        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = await asyncio.to_thread(
                client.embeddings.create,
                model=self.name_model,
                input=text,
            )
            return response.data[0].embedding
        except OpenAIError as exc:
            print(f"OpenAI API error: {exc}")
            return []

    async def health(self) -> bool:
        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            await asyncio.to_thread(client.models.retrieve, self.name_model)
            return True
        except OpenAIError as exc:
            print(f"OpenAI API health check error: {exc}")
            return False

