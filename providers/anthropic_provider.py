from providers.Openai_llm_provider import Openai_llm_provider

class AnthropicProvider(Openai_llm_provider):
    def __init__(self, name_model: str = "anthropic/claude-3.5-sonnet", temperature: float = 0.7, max_tokens: int = 150):
        super().__init__(
            name_model=name_model,
            temperature=temperature,
            max_tokens=max_tokens,
            default_model="openai/gpt-4o-mini"
        )
