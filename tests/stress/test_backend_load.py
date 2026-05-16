from __future__ import annotations

import os
import random
import statistics
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import httpx

from tests.e2e.base import BASE_URL, LocalAppServer


RUN_STRESS_TESTS = os.getenv("RUN_STRESS_TESTS") == "1"


class BackendLoadProfileTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        if not RUN_STRESS_TESTS:
            raise unittest.SkipTest("Set RUN_STRESS_TESTS=1 to run backend load profile tests")
        cls.base_url = BASE_URL.rstrip("/")
        cls.server = LocalAppServer(cls.base_url)
        cls.server.ensure_running()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.stop()
        super().tearDownClass()

    def _validate_snapshot_shape(self, payload: dict[str, Any]) -> None:
        required = {
            "board",
            "probabilities",
            "side_to_move",
            "fullmove_number",
            "game_status",
            "legal_moves",
            "last_move_outcome",
            "move_history",
        }
        self.assertTrue(required.issubset(payload.keys()))

    def _one_iteration(self, rng: random.Random) -> tuple[float, int, bool]:
        op = rng.choices(["read", "reset", "move"], weights=[0.55, 0.25, 0.20], k=1)[0]
        started = time.perf_counter()
        with httpx.Client(timeout=10) as client:
            if op == "read":
                response = client.get(f"{self.base_url}/game")
            elif op == "reset":
                response = client.post(f"{self.base_url}/game/reset")
            else:
                client.post(f"{self.base_url}/game/reset")
                response = client.post(
                    f"{self.base_url}/game/move/classical",
                    json={"src": "b1", "target": "c3"},
                )

        latency = time.perf_counter() - started
        schema_ok = False
        if response.status_code == 200:
            self._validate_snapshot_shape(response.json())
            schema_ok = True
        return latency, response.status_code, schema_ok

    def test_mixed_concurrency_profile(self):
        concurrency = int(os.getenv("BACKEND_STRESS_CONCURRENCY", "8"))
        operations = int(os.getenv("BACKEND_STRESS_OPERATIONS", "250"))
        p95_threshold_seconds = float(os.getenv("BACKEND_STRESS_P95_SECONDS", "1.5"))
        max_client_error_rate = float(os.getenv("BACKEND_STRESS_MAX_4XX_RATE", "0.25"))

        latencies: list[float] = []
        server_errors = 0
        client_errors = 0
        schema_failures = 0

        seeds = [random.randint(0, 1_000_000) for _ in range(operations)]

        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            results = list(executor.map(lambda s: self._one_iteration(random.Random(s)), seeds))

        for latency, status, schema_ok in results:
            latencies.append(latency)
            if 500 <= status < 600:
                server_errors += 1
            if 400 <= status < 500:
                client_errors += 1
            if status == 200 and not schema_ok:
                schema_failures += 1

        p95_index = max(int(len(latencies) * 0.95) - 1, 0)
        p95_latency = sorted(latencies)[p95_index]
        client_error_rate = client_errors / len(results)

        self.assertEqual(server_errors, 0, f"Observed {server_errors} server errors")
        self.assertEqual(schema_failures, 0, f"Observed {schema_failures} schema failures")
        self.assertLessEqual(
            client_error_rate,
            max_client_error_rate,
            f"Client error rate {client_error_rate:.2%} exceeded {max_client_error_rate:.2%}",
        )
        self.assertLessEqual(
            p95_latency,
            p95_threshold_seconds,
            f"P95 latency {p95_latency:.3f}s exceeded {p95_threshold_seconds:.3f}s",
        )
        self.assertGreater(statistics.mean(latencies), 0.0)
