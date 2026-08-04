"""
Analiza el dibujo subido por el usuario y extrae una descripción del
personaje que servirá como ancla narrativa y visual durante toda la
historia.
"""

from pathlib import Path

from providers.base import BaseLLMProvider

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "character_analysis.txt"


def analyze_character(llm_provider: BaseLLMProvider, image_bytes: bytes, mime_type: str) -> str:
    """
    Devuelve una descripción textual del personaje del dibujo.
    El prompt específico de análisis vive en prompts/character_analysis.txt
    pero la implementación del proveedor (gemini_provider.py) ya lo
    incorpora; aquí simplemente delegamos y dejamos el archivo como
    referencia/documentación editable sin tocar código.
    """
    description = llm_provider.analyze_image(image_bytes, mime_type)
    return description.strip()
