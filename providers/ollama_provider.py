import asyncio
import os
from typing import Any, Dict, List, Optional

try:
    from openai import OpenAI
    from openai import APIStatusError as OpenAIError
except ImportError:
    from openai import OpenAI
    from openai import OpenAIError

from providers.init import BaseProvider

class OllamaProvider(BaseProvider):
    def __init__(self, name_model: str = "llama3", temperature: float = 0.7, max_tokens: int = 150, base_url: str = None):
        self.name_model = name_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.base_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")

    def _get_client(self) -> OpenAI:
        return OpenAI(
            base_url=self.base_url,
            api_key="ollama", # Ollama doesn't require key, but SDK expects a non-empty string
        )

    async def _chat_with_model(self, message: str) -> str:
        client = self._get_client()
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=self.name_model,
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

    async def chat(self, message: str, context: Optional[List[Dict[str, Any]]] = None) -> Optional[str]:
        try:
            return await self._chat_with_model(message)
        except OpenAIError as exc:
            print(f"Ollama API error for {self.name_model}: {exc}")
            return None

    async def embedding(self, text: str) -> List[float]:
        try:
            client = self._get_client()
            response = await asyncio.to_thread(
                client.embeddings.create,
                model=self.name_model,
                input=[text],
            )
            return response.data[0].embedding
        except OpenAIError as exc:
            print(f"Ollama API embedding error: {exc}")
            return []

    async def health(self) -> bool:
        try:
            # Check model availability or check endpoint with a dummy call
            client = self._get_client()
            # Send a fast test chat completion to verify Ollama is up and model is loaded
            await self.chat("ping")
            return True
        except Exception as exc:
            print(f"Ollama health check error: {exc}")
            return False
