import unittest

from tests.e2e.base import By, SeleniumE2ECase, selenium_enabled, selenium_skip_reason


@unittest.skipUnless(selenium_enabled(), selenium_skip_reason())
class EdgeCasesTest(SeleniumE2ECase):
    def setUp(self) -> None:
        self.reset_game()
        self.open_app()

    def test_inert_square_click_is_ignored(self):
        self.click_square("e4")
        self.assertIn("select 2 squares", self.selection_text())

    def test_merge_requires_matching_piece_sources(self):
        self.click_button("Merge")
        self.click_square("b1")
        self.click_square("e2")
        self.assertIn("e2", self.selection_text())
        self.assertNotIn("b1", self.selection_text())

    def test_execute_disabled_until_selection_complete(self):
        execute_btn = self.action_button("Execute")
        self.assertEqual(execute_btn.get_attribute("disabled"), "true")
        self.click_square("b1")
        self.assertEqual(execute_btn.get_attribute("disabled"), "true")
        self.click_square("c3")
        self.assertIsNone(execute_btn.get_attribute("disabled"))

    def test_loading_state_disables_action_buttons(self):
        self.driver.execute_script(
            """
            if (!window.__origFetch) {
              window.__origFetch = window.fetch;
            }
            window.fetch = async (input, init) => {
              const url = typeof input === "string" ? input : input.url;
              if (url.includes("/game/move/classical")) {
                await new Promise((resolve) => setTimeout(resolve, 700));
              }
              return window.__origFetch(input, init);
            };
            """
        )
        self.execute_classical_move("b1", "c3")
        self.assertEqual(self.action_button("Execute").get_attribute("disabled"), "true")
        self.wait_for_side_to_move("black")

    def test_stale_client_selection_surfaces_api_error(self):
        self.click_square("b1")
        self.click_square("c3")

        self.api_post("/game/move/classical", {"src": "b1", "target": "a3"})

        self.click_button("Execute")
        alert = self.wait.until(
            lambda d: d.find_element(By.CSS_SELECTOR, '[role="alert"]')
        )
        self.assertTrue(
            "illegal move" in alert.text or "no piece present" in alert.text,
            f"Unexpected error text: {alert.text}",
        )

    def test_capture_failed_outcome_is_rendered(self):
        seen_capture_failed = False
        for _ in range(12):
            self.reset_game()
            self.open_app()

            self.click_button("Split")
            self.click_square("b1")
            self.click_square("a3")
            self.click_square("c3")
            self.click_button("Execute")
            self.wait_for_side_to_move("black")

            self.execute_classical_move("b7", "b5")
            self.wait_for_side_to_move("white")
            self.execute_classical_move("a3", "b5")
            self.wait_for_side_to_move("black")

            if "Negative observation" in self.driver.page_source:
                classes = self.square("b5").get_attribute("class")
                self.assertIn("square-capture-failed", classes)
                seen_capture_failed = True
                break

        self.assertTrue(
            seen_capture_failed,
            "Expected to observe at least one capture_failed outcome across retries",
        )

    def test_game_over_banner_after_king_capture(self):
        self.execute_classical_move("e2", "e4")
        self.wait_for_side_to_move("black")
        self.execute_classical_move("f7", "f6")
        self.wait_for_side_to_move("white")
        self.execute_classical_move("d1", "h5")
        self.wait_for_side_to_move("black")
        self.execute_classical_move("a7", "a6")
        self.wait_for_side_to_move("white")
        self.execute_classical_move("h5", "e8")

        self.wait_for_text("White wins")
        execute_btn = self.action_button("Execute")
        self.assertEqual(execute_btn.get_attribute("disabled"), "true")
