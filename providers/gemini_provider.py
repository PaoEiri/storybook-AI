"""
Implementación de BaseLLMProvider usando Google Gemini (tier gratuito).
Soporta visión (análisis del dibujo) y streaming de texto.
Lanza GeminiQuotaError cuando se supera la cuota de la API gratuita.
"""

from typing import Generator
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, TooManyRequests

from .base import BaseLLMProvider
from prompts.loader import load_prompt


class GeminiQuotaError(Exception):
    """Se lanza cuando Gemini devuelve un error de cuota agotada (429)."""
    pass


def _wrap_quota(fn):
    """Decorador que convierte errores de cuota de Google en GeminiQuotaError."""
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (ResourceExhausted, TooManyRequests) as e:
            raise GeminiQuotaError(str(e)) from e
        except Exception as e:
            # Algunos errores de cuota llegan como genéricos con código 429
            msg = str(e).lower()
            if "429" in msg or "quota" in msg or "rate limit" in msg or "exhausted" in msg:
                raise GeminiQuotaError(str(e)) from e
            raise
    return wrapper


class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-3.5-flash"):
        if not api_key:
            raise ValueError(
                "Falta GEMINI_API_KEY. Consíguela gratis en "
                "https://aistudio.google.com/app/apikey"
            )
        genai.configure(api_key=api_key)
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)

    @_wrap_quota
    def analyze_image(self, image_bytes: bytes, mime_type: str = "image/png") -> str:
        prompt = load_prompt("character_analysis.txt")
        image_part = {"mime_type": mime_type, "data": image_bytes}
        response = self.model.generate_content([prompt, image_part])
        return response.text.strip()

    def stream_story(self, messages: list[dict]) -> Generator[str, None, None]:
        system_instruction = None
        history = []

        for msg in messages:
            if msg["role"] == "system" and system_instruction is None:
                system_instruction = msg["content"]
                continue
            role = "model" if msg["role"] == "assistant" else "user"
            history.append({"role": role, "parts": [msg["content"]]})

        if not history:
            return

        *previous, last = history
        model = (
            genai.GenerativeModel(self.model_name, system_instruction=system_instruction)
            if system_instruction
            else self.model
        )
        chat = model.start_chat(history=previous)

        try:
            response_stream = chat.send_message(last["parts"][0], stream=True)
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
        except (ResourceExhausted, TooManyRequests) as e:
            raise GeminiQuotaError(str(e)) from e
        except Exception as e:
            msg = str(e).lower()
            if "429" in msg or "quota" in msg or "rate limit" in msg or "exhausted" in msg:
                raise GeminiQuotaError(str(e)) from e
            raise
