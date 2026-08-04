"""
Controla la lógica de checkpoints: en qué turno tocan opciones de
decisión, cuándo generar una nueva imagen, y cuándo cerrar la historia.
"""


class CheckpointController:
    def __init__(self, max_turns: int = 3, max_images: int = 3):
        self.max_turns = max_turns
        self.max_images = max_images
        self.current_turn = 0  # número de turnos interactivos completados
        self.images_used = 0

    def is_story_finished(self) -> bool:
        return self.current_turn >= self.max_turns

    def register_turn(self):
        self.current_turn += 1

    def should_generate_image(self) -> bool:
        """Compatibilidad con el flujo anterior."""
        return self.images_used < self.max_images

    def should_generate_image_for_stage(self, stage: str) -> bool:
        """
        Reserva 3 momentos de imagen para respetar el límite:
        1) apertura, 2) primera continuación, 3) conclusión.
        """
        if stage == "opening":
            return self.images_used == 0 and self.images_used < self.max_images

        if stage == "continuing":
            return self.images_used == 1 and self.images_used < self.max_images

        if stage == "conclusion":
            return self.images_used < self.max_images

        return False

    def register_image_used(self):
        self.images_used += 1

    def turns_remaining(self) -> int:
        return max(0, self.max_turns - self.current_turn)
