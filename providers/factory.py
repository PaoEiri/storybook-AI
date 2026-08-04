"""
Factory: lee las variables de entorno LLM_PROVIDER e IMAGE_PROVIDER
y devuelve la implementación concreta correspondiente.

Este es el ÚNICO lugar del proyecto donde se decide qué proveedor usar.
Para hacer el swap a OpenAI cuando recuperes la API key, basta con
cambiar las variables de entorno; no hay que tocar ni una línea de
código en core/.
"""

import os

from .base import BaseLLMProvider, BaseImageProvider


def get_llm_provider() -> BaseLLMProvider:
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()

    if provider == "gemini":
        from .gemini_provider import GeminiProvider
        return GeminiProvider(
            api_key=os.getenv("GEMINI_API_KEY"),
            model_name=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        )

    if provider == "openai":
        from .openai_provider import OpenAILLMProvider
        return OpenAILLMProvider(api_key=os.getenv("OPENAI_API_KEY"))

    raise ValueError(
        f"LLM_PROVIDER='{provider}' no reconocido. Usa 'gemini' u 'openai'."
    )


def get_image_provider() -> BaseImageProvider:
    provider = os.getenv("IMAGE_PROVIDER", "huggingface").lower()

    if provider == "huggingface":
        from .huggingface_provider import HuggingFaceImageProvider
        return HuggingFaceImageProvider(api_key=os.getenv("HF_API_KEY"))

    if provider == "pollinations":
        from .pollinations_provider import PollinationsImageProvider
        return PollinationsImageProvider()

    if provider == "openai":
        from .openai_provider import OpenAIImageProvider
        return OpenAIImageProvider(api_key=os.getenv("OPENAI_API_KEY"))

    raise ValueError(
        f"IMAGE_PROVIDER='{provider}' no reconocido. "
        "Usa 'huggingface', 'pollinations' u 'openai'."
    )
