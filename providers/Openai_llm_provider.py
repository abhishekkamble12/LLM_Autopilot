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
    def __init__(self, name_model: str, temperature: float = 0.7, max_tokens: int = 150,default_model: str = "openai/gpt-4o-mini"):
        self.name_model = name_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.default_model = default_model

    def _get_client(self) -> OpenAI:
        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ.get("OPENROUTER_API_KEY"),
        )

    def _get_model_name(self, model_name: Optional[str] = None) -> str:
        requested_model = (model_name or self.name_model or self.default_model).strip()
        return requested_model or self.default_model

    async def _chat_with_model(self, model_name: str, message: str):
        client = self._get_client()
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=model_name,
            messages=[{"role": "user", "content": message}],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        if not getattr(response, "choices", None):
            raise OpenAIError("No response choices returned")

        content = response.choices[0].message.content
        if content is None:
            raise OpenAIError("Empty response content")
        return content

    async def chat(self, message: str, context: Optional[List[Dict[str, Any]]] = None):
        requested_model = self._get_model_name(self.name_model)
        try:
            return await self._chat_with_model(requested_model, message)
        except OpenAIError as exc:
            # Suppress terminal spam for API errors (e.g. 402 insufficient funds, 404 offline)
            # print(f"OpenAI API error for {requested_model}: {exc}")
            if requested_model != self.default_model:
                try:
                    return await self._chat_with_model(self.default_model, message)
                except OpenAIError as fallback_exc:
                    # print(f"Fallback OpenAI API error for {self.default_model}: {fallback_exc}")
                    pass
            return None

    async def embedding(self, text: str) -> List[float]:
        try:
            client = self._get_client()
            response = await asyncio.to_thread(
                client.embeddings.create,
                model="openai/text-embedding-3-small",
                input=[text],
            )
            return response.data[0].embedding
        except OpenAIError as exc:
            print(f"OpenAI API error: {exc}")
            return []

    async def health(self) -> bool:
        requested_model = self._get_model_name(self.name_model)
        try:
            client = self._get_client()
            await asyncio.to_thread(client.models.retrieve, requested_model)
            return True
        except OpenAIError as exc:
            # print(f"OpenAI API health check error for {requested_model}: {exc}")
            if requested_model != self.default_model:
                try:
                    client = self._get_client()
                    await asyncio.to_thread(client.models.retrieve, self.default_model)
                    return True
                except OpenAIError as fallback_exc:
                    # print(f"Fallback OpenAI API health check error for {self.default_model}: {fallback_exc}")
                    pass
            return False

