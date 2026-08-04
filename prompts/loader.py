"""
Helper único para cargar prompts desde archivos .txt en este directorio.
Centraliza lo que antes estaba duplicado en varios módulos de core/.
"""

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str, **kwargs) -> str:
    """Lee prompts/<name> y, si se pasan kwargs, los interpola con .format()."""
    text = (PROMPTS_DIR / name).read_text(encoding="utf-8")
    return text.format(**kwargs) if kwargs else text
