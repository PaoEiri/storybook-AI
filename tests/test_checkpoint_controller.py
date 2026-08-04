import unittest

from core.checkpoint_controller import CheckpointController


class CheckpointControllerTests(unittest.TestCase):
    def test_continuation_skips_last_turn_to_save_final_image(self):
        checkpoint = CheckpointController(max_turns=3, max_images=3)
        checkpoint.register_turn()  # 1
        checkpoint.register_turn()  # 2
        checkpoint.register_turn()  # 3 -> last turn reached

        self.assertFalse(checkpoint.should_generate_image_for_stage("continuing"))

    def test_conclusion_can_still_use_an_image_when_available(self):
        checkpoint = CheckpointController(max_turns=3, max_images=3)
        checkpoint.register_image_used()
        checkpoint.register_image_used()

        self.assertTrue(checkpoint.should_generate_image_for_stage("conclusion"))


if __name__ == "__main__":
    unittest.main()
