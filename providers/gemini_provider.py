from providers.Openai_llm_provider import Openai_llm_provider

class GeminiProvider(Openai_llm_provider):
    def __init__(self, name_model: str = "google/gemini-flash-1.5", temperature: float = 0.7, max_tokens: int = 150):
        super().__init__(
            name_model=name_model,
            temperature=temperature,
            max_tokens=max_tokens,
            default_model="openai/gpt-4o-mini"
        )
