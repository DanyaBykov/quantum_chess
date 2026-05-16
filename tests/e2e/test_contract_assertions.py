import unittest

from tests.e2e.base import SeleniumE2ECase, selenium_enabled, selenium_skip_reason


@unittest.skipUnless(selenium_enabled(), selenium_skip_reason())
class ContractAssertionsTest(SeleniumE2ECase):
    def setUp(self) -> None:
        self.reset_game()
        self.open_app()

    def test_status_panel_matches_snapshot_contract(self):
        snapshot = self.api_get("/game")
        self.assertIn(f"{snapshot['side_to_move']} to move", self.driver.page_source)

        legal_moves_value = self.driver.find_element(
            "xpath",
            "//span[normalize-space()='Legal moves']/following-sibling::span",
        ).text
        self.assertEqual(int(legal_moves_value), len(snapshot["legal_moves"]))

        status_value = self.driver.find_element(
            "xpath",
            "//span[normalize-space()='Status']/following-sibling::span",
        ).text
        self.assertEqual(status_value, snapshot["game_status"])

    def test_move_history_notation_and_outcome_match_snapshot(self):
        self.execute_classical_move("b1", "c3")
        self.wait_for_side_to_move("black")

        snapshot = self.api_get("/game")
        last = snapshot["move_history"][-1]
        self.assertEqual(last["mode"], "classical")
        self.assertEqual(last["squares"], ["b1", "c3"])
        self.assertEqual(last["outcome"], "success")
        self.assertIn("b1→c3", self.driver.page_source)

    def test_split_probability_cues_match_snapshot(self):
        self.click_button("Split")
        self.click_square("b1")
        self.click_square("a3")
        self.click_square("c3")
        self.click_button("Execute")
        self.wait_for_side_to_move("black")

        snapshot = self.api_get("/game")
        self.assertAlmostEqual(snapshot["probabilities"]["a3"], 0.5, places=2)
        self.assertAlmostEqual(snapshot["probabilities"]["c3"], 0.5, places=2)

        a3_prob = self.square("a3").find_element("css selector", ".square-prob").text
        c3_prob = self.square("c3").find_element("css selector", ".square-prob").text
        self.assertEqual(a3_prob, "50%")
        self.assertEqual(c3_prob, "50%")
