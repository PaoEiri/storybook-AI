"""
Implementación de BaseImageProvider usando Pollinations.ai.
No requiere API key. Si el servidor falla (error 500 frecuente),
reintenta con un prompt simplificado antes de rendirse.
"""

import urllib.parse
import requests
from .base import BaseImageProvider

BASE_URL = "https://image.pollinations.ai/prompt/"
STYLE = ", children's illustrated storybook, soft watercolor style, warm golden light, whimsical"


class PollinationsImageProvider(BaseImageProvider):
    def __init__(self, api_key: str | None = None):
        pass

    def _fetch(self, prompt: str, timeout: int = 60) -> bytes:
        encoded = urllib.parse.quote(prompt)
        url = f"{BASE_URL}{encoded}?width=768&height=768&nologo=true&seed=42"
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.content

    def generate_image(self, prompt: str) -> bytes:
        # Intento 1: prompt completo
        full_prompt = prompt + STYLE
        try:
            return self._fetch(full_prompt)
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 500:
                pass  # reintenta con prompt corto
            else:
                raise

        # Intento 2: prompt recortado a 300 chars + estilo mínimo
        short_prompt = prompt[:300] + ", children's storybook illustration, soft watercolor"
        try:
            return self._fetch(short_prompt)
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 500:
                pass
            else:
                raise

        # Intento 3: solo el estilo genérico (garantiza una imagen aunque no sea específica)
        fallback = "magical children's storybook scene, soft watercolor illustration, warm colors"
        return self._fetch(fallback)
