"""
Construye los prompts de cada fase narrativa (apertura, continuación,
cierre) y delega la generación en streaming al proveedor de LLM activo.
"""

from typing import Generator

from providers.base import BaseLLMProvider
from core.context_manager import ContextManager
from prompts.loader import load_prompt


def stream_opening(
    llm_provider: BaseLLMProvider, context: ContextManager
) -> Generator[str, None, None]:
    """Genera en streaming las páginas de apertura de la historia."""
    prompt = load_prompt("story_opening.txt")
    context.add_user_turn(prompt)
    yield from llm_provider.stream_story(context.get_messages())


def stream_continuation(
    llm_provider: BaseLLMProvider, context: ContextManager, user_choice: str
) -> Generator[str, None, None]:
    """Genera en streaming la continuación tras la elección del usuario."""
    prompt = load_prompt("story_continuation.txt", user_choice=user_choice)
    context.add_user_turn(prompt)
    yield from llm_provider.stream_story(context.get_messages())


def stream_conclusion(
    llm_provider: BaseLLMProvider, context: ContextManager
) -> Generator[str, None, None]:
    """Genera en streaming el cierre de la historia."""
    prompt = load_prompt("story_conclusion.txt")
    context.add_user_turn(prompt)
    yield from llm_provider.stream_story(context.get_messages())
