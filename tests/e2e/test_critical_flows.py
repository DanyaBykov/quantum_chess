import unittest

from tests.e2e.base import SeleniumE2ECase, selenium_enabled, selenium_skip_reason


@unittest.skipUnless(selenium_enabled(), selenium_skip_reason())
class CriticalFlowsTest(SeleniumE2ECase):
    def setUp(self) -> None:
        self.reset_game()
        self.open_app()

    def test_initial_load_renders_board_and_status(self):
        squares = self.driver.find_elements("css selector", "button.square")
        self.assertEqual(len(squares), 64)
        self.assertIn("white to move", self.driver.page_source)
        self.assertIn("♔", self.square("e1").text)
        self.assertIn("♚", self.square("e8").text)

    def test_classical_move_updates_board_and_history(self):
        self.execute_classical_move("b1", "c3")
        self.wait_for_side_to_move("black")
        self.assertIn("♘", self.square("c3").text)
        self.assertEqual(self.square("b1").text.strip(), "")
        self.wait_for_text("b1→c3")

    def test_split_and_merge_flow(self):
        self.click_button("Split")
        self.click_square("b1")
        self.click_square("a3")
        self.click_square("c3")
        self.click_button("Execute")
        self.wait_for_side_to_move("black")
        self.assertIn("50%", self.square("a3").text)
        self.assertIn("50%", self.square("c3").text)

        self.execute_classical_move("b8", "a6")
        self.wait_for_side_to_move("white")

        self.click_button("Merge")
        self.click_square("a3")
        self.click_square("c3")
        self.click_square("b1")
        self.click_button("Execute")
        self.wait_for_side_to_move("black")

        self.assertIn("♘", self.square("b1").text)
        self.assertNotIn("♘", self.square("a3").text)
        self.assertNotIn("♘", self.square("c3").text)
        self.wait_for_text("a3+c3→b1")

    def test_reset_restores_initial_position_and_clears_history(self):
        self.execute_classical_move("b1", "c3")
        self.wait_for_side_to_move("black")
        self.click_button("Reset")
        self.wait_for_side_to_move("white")

        self.assertIn("♘", self.square("b1").text)
        self.assertEqual(self.square("c3").text.strip(), "")
        self.wait_for_text("no moves yet")

    def test_rules_tab_navigation(self):
        self.click_button("Rules")
        self.wait_for_text("How to play Quantum Chess")
        self.click_button("Game")
        self.wait.until(lambda d: "Quantum chess board" in d.page_source)
