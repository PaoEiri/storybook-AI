"""
Implementación de BaseLLMProvider y BaseImageProvider usando OpenAI.
Lista para usarse en cuanto recuperes acceso a la API de OpenAI:
solo cambia LLM_PROVIDER=openai e IMAGE_PROVIDER=openai en tu .env.
"""

import base64
from typing import Generator

from openai import OpenAI

from .base import BaseLLMProvider, BaseImageProvider


class OpenAILLMProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model_name: str = "gpt-4.1-nano"):
        if not api_key:
            raise ValueError("Falta OPENAI_API_KEY en el entorno.")
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name

    def analyze_image(self, image_bytes: bytes, mime_type: str = "image/png") -> str:
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        prompt = (
            "Eres un asistente que ayuda a crear cuentos infantiles. "
            "Observa este dibujo hecho por un niño o niña y describe el "
            "personaje que ves con detalle: tipo de criatura o persona, "
            "colores, forma, rasgos distintivos, expresión, accesorios. "
            "Escribe la descripción en 3-4 frases, en un tono cálido y "
            "evocador, como si describieras al protagonista de un cuento."
        )

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{b64_image}"
                            },
                        },
                    ],
                }
            ],
        )
        return response.choices[0].message.content.strip()

    def stream_story(self, messages: list[dict]) -> Generator[str, None, None]:
        stream = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


class OpenAIImageProvider(BaseImageProvider):
    def __init__(self, api_key: str, quality: str = "low"):
        if not api_key:
            raise ValueError("Falta OPENAI_API_KEY en el entorno.")
        self.client = OpenAI(api_key=api_key)
        self.quality = quality  # respetar restricción de coste de la tarea

    def generate_image(self, prompt: str) -> bytes:
        full_prompt = (
            f"{prompt}, children's storybook illustration style, "
            "soft colors, whimsical, warm lighting"
        )
        response = self.client.images.generate(
            model="gpt-image-1",
            prompt=full_prompt,
            quality=self.quality,
            size="1024x1024",
        )
        b64_data = response.data[0].b64_json
        return base64.b64decode(b64_data)
