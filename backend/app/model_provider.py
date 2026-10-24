import os
from dataclasses import dataclass
from typing import Literal

ProviderName = Literal["openai", "anthropic", "gemini"]


@dataclass
class ModelRequest:
    prompt: str
    system_prompt: str | None = None
    temperature: float = 0.2
    max_tokens: int = 512


class BaseModelProvider:
    name: ProviderName = "openai"

    def generate(self, request: ModelRequest) -> dict:
        raise NotImplementedError


class OpenAIProvider(BaseModelProvider):
    name = "openai"

    def generate(self, request: ModelRequest) -> dict:
        return {
            "provider": self.name,
            "prompt": request.prompt,
            "system_prompt": request.system_prompt,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "status": "stubbed",
        }


class AnthropicProvider(BaseModelProvider):
    name = "anthropic"

    def generate(self, request: ModelRequest) -> dict:
        return {
            "provider": self.name,
            "prompt": request.prompt,
            "system_prompt": request.system_prompt,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "status": "stubbed",
        }


class GeminiProvider(BaseModelProvider):
    name = "gemini"

    def generate(self, request: ModelRequest) -> dict:
        return {
            "provider": self.name,
            "prompt": request.prompt,
            "system_prompt": request.system_prompt,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "status": "stubbed",
        }


PROVIDERS = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
}


def get_model_provider() -> BaseModelProvider:
    provider_name = os.getenv("MODEL_PROVIDER", "openai").lower()
    provider_cls = PROVIDERS.get(provider_name, OpenAIProvider)
    return provider_cls()
