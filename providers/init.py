# Base class for all providers.
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseProvider(ABC):
    @abstractmethod
    async def chat(self, message: str, context: Optional[List[Dict[str, Any]]] = None):
        pass

    @abstractmethod
    async def embedding(self, text: str) -> List[float]:
        pass

    @abstractmethod
    async def health(self) -> bool:
        """
        Performs a quick check (for example, sending a minimal prompt or checking an
        API endpoint) to verify that the provider is healthy and responsive.
        """
        pass


Provider = BaseProvider

__all__ = ["BaseProvider", "Provider"]