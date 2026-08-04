"""
Interfaces abstractas que todo proveedor de LLM o de generación de imágenes
debe implementar. El resto del proyecto (core/) solo conoce estas interfaces,
nunca un proveedor concreto. Esto permite cambiar de Gemini a OpenAI (o
cualquier otro) sin tocar la lógica de negocio.
"""

from abc import ABC, abstractmethod
from typing import Generator


class BaseLLMProvider(ABC):
    """Proveedor de modelo de lenguaje con capacidad de visión y streaming."""

    @abstractmethod
    def analyze_image(self, image_bytes: bytes, mime_type: str = "image/png") -> str:
        """
        Analiza el dibujo subido por el usuario y devuelve una descripción
        textual detallada del personaje (apariencia, colores, rasgos
        distintivos) que se usará como contexto fijo durante toda la historia.
        """
        raise NotImplementedError

    @abstractmethod
    def stream_story(self, messages: list[dict]) -> Generator[str, None, None]:
        """
        Genera la continuación de la historia en streaming.
        `messages` sigue el formato [{"role": "user"|"assistant"|"system", "content": str}, ...]
        Debe hacer yield de fragmentos de texto (chunks) a medida que el
        modelo los genera, no devolver el texto completo de una vez.
        """
        raise NotImplementedError


class BaseImageProvider(ABC):
    """Proveedor de generación de imágenes (ilustraciones del cuento)."""

    @abstractmethod
    def generate_image(self, prompt: str) -> bytes:
        """
        Genera una ilustración a partir de un prompt textual y devuelve
        los bytes de la imagen (PNG/JPEG).
        """
        raise NotImplementedError
