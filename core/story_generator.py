"""
Construye los prompts de cada fase narrativa (apertura, continuación,
cierre) y delega la generación en streaming al proveedor de LLM activo.
"""

from pathlib import Path
from typing import Generator

from providers.base import BaseLLMProvider
from core.context_manager import ContextManager

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def _read_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def stream_opening(
    llm_provider: BaseLLMProvider, context: ContextManager
) -> Generator[str, None, None]:
    """Genera en streaming las páginas de apertura de la historia."""
    prompt = _read_prompt("story_opening.txt")
    context.add_user_turn(prompt)
    yield from llm_provider.stream_story(context.get_messages())


def stream_continuation(
    llm_provider: BaseLLMProvider, context: ContextManager, user_choice: str
) -> Generator[str, None, None]:
    """Genera en streaming la continuación tras la elección del usuario."""
    template = _read_prompt("story_continuation.txt")
    prompt = template.format(user_choice=user_choice)
    context.add_user_turn(prompt)
    yield from llm_provider.stream_story(context.get_messages())


def stream_conclusion(
    llm_provider: BaseLLMProvider, context: ContextManager
) -> Generator[str, None, None]:
    """Genera en streaming el cierre de la historia."""
    prompt = _read_prompt("story_conclusion.txt")
    context.add_user_turn(prompt)
    yield from llm_provider.stream_story(context.get_messages())
