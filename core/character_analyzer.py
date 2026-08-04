"""
Analiza el dibujo subido por el usuario y extrae una descripción del
personaje que servirá como ancla narrativa y visual durante toda la
historia.
"""

from providers.base import BaseLLMProvider


def analyze_character(llm_provider: BaseLLMProvider, image_bytes: bytes, mime_type: str) -> str:
    """
    Devuelve una descripción textual del personaje del dibujo.
    El prompt de análisis vive en prompts/character_analysis.txt y lo carga
    directamente cada proveedor (gemini_provider.py, openai_provider.py);
    aquí simplemente delegamos.
    """
    description = llm_provider.analyze_image(image_bytes, mime_type)
    return description.strip()
