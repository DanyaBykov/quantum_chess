import os
import statistics
import time
import unittest

from tests.e2e.base import SeleniumE2ECase, selenium_enabled


RUN_STRESS_TESTS = os.getenv("RUN_STRESS_TESTS") == "1"


@unittest.skipUnless(
    RUN_STRESS_TESTS and selenium_enabled(),
    "Set RUN_STRESS_TESTS=1 and RUN_SELENIUM_E2E=1 to run UI stress tests",
)
class UIStressTest(SeleniumE2ECase):
    def test_repeated_interaction_loops(self):
        iterations = int(os.getenv("UI_STRESS_ITERATIONS", "20"))
        max_median_seconds = float(os.getenv("UI_STRESS_MAX_MEDIAN_SECONDS", "2.5"))
        latencies: list[float] = []

        for _ in range(iterations):
            self.reset_game()
            self.open_app()

            start = time.perf_counter()
            self.execute_classical_move("b1", "c3")
            self.wait_for_side_to_move("black")
            self.execute_classical_move("b8", "a6")
            self.wait_for_side_to_move("white")
            self.click_button("Reset")
            self.wait_for_side_to_move("white")
            latencies.append(time.perf_counter() - start)

            self.assertNotIn("Traceback", self.driver.page_source)

        median_latency = statistics.median(latencies)
        self.assertLessEqual(
            median_latency,
            max_median_seconds,
            f"Median UI loop latency {median_latency:.3f}s exceeded {max_median_seconds:.3f}s",
        )
