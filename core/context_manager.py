"""
Mantiene el estado conversacional completo de la historia: el mensaje de
sistema (con la descripción del personaje incrustada), y el historial de
turnos (aperturas, continuaciones, elecciones del usuario y cierre).

Esto es lo que garantiza la COHERENCIA narrativa: cada llamada al LLM
recibe todo el contexto previo, nunca solo el último fragmento.
"""

from prompts.loader import load_prompt


class ContextManager:
    def __init__(self, character_description: str):
        self.character_description = character_description
        system_prompt = load_prompt(
            "story_system.txt", character_description=character_description
        )

        self.messages: list[dict] = [
            {"role": "system", "content": system_prompt}
        ]

    def add_user_turn(self, content: str):
        self.messages.append({"role": "user", "content": content})

    def add_assistant_turn(self, content: str):
        self.messages.append({"role": "assistant", "content": content})

    def get_messages(self) -> list[dict]:
        return self.messages

    def get_full_story_text(self) -> str:
        """Concatena solo los fragmentos de historia (turnos assistant)."""
        return "\n\n".join(
            m["content"] for m in self.messages if m["role"] == "assistant"
        )
