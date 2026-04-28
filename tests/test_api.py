import pathlib
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient

from api.app import app
from api.state_store import store


class ApiTest(unittest.TestCase):
    def setUp(self):
        store.reset()
        self.client = TestClient(app)

    def test_get_game_returns_initial_snapshot(self):
        response = self.client.get("/game")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["side_to_move"], "white")
        self.assertEqual(payload["fullmove_number"], 1)
        self.assertEqual(payload["board"]["e1"], "K")
        self.assertEqual(payload["board"]["e8"], "k")
        self.assertEqual(payload["probabilities"]["e1"], 1.0)

    def test_reset_game_restores_initial_state(self):
        self.client.post("/game/move/classical", json={"src": "b1", "target": "c3"})

        response = self.client.post("/game/reset")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["board"]["b1"], "N")
        self.assertIsNone(payload["board"]["c3"])
        self.assertEqual(payload["side_to_move"], "white")

    def test_classical_move_endpoint_updates_state(self):
        response = self.client.post("/game/move/classical", json={"src": "b1", "target": "c3"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIsNone(payload["board"]["b1"])
        self.assertEqual(payload["board"]["c3"], "N")
        self.assertEqual(payload["side_to_move"], "black")

    def test_classical_move_returns_400_on_illegal_move(self):
        response = self.client.post("/game/move/classical", json={"src": "b1", "target": "b4"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("illegal move", response.json()["detail"])

    def test_split_move_endpoint_returns_probabilities(self):
        response = self.client.post(
            "/game/move/split",
            json={"src": "b1", "target_a": "a3", "target_b": "c3"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertAlmostEqual(payload["probabilities"]["a3"], 0.5)
        self.assertAlmostEqual(payload["probabilities"]["c3"], 0.5)
        self.assertEqual(payload["side_to_move"], "black")

    def test_merge_move_endpoint_combines_split_branches(self):
        self.client.post("/game/move/split", json={"src": "b1", "target_a": "a3", "target_b": "c3"})
        store.get_game().side_to_move = "white"

        response = self.client.post(
            "/game/move/merge",
            json={"src_a": "a3", "src_b": "c3", "target": "b1"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["board"]["b1"], "N")
        self.assertAlmostEqual(payload["probabilities"]["b1"], 1.0)

    @patch("engine.quantum_ops.random.choices", return_value=[False])
    def test_measure_endpoint_collapses_square(self, _mock_choice):
        response = self.client.post("/game/measure", json={"target": "d4"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIsNone(payload["board"]["d4"])
        self.assertEqual(payload["probabilities"]["d4"], 0.0)

    def test_snapshot_includes_new_fields(self):
        response = self.client.get("/game")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("in_check", payload)
        self.assertFalse(payload["in_check"])
        self.assertIn("game_status", payload)
        self.assertEqual(payload["game_status"], "ongoing")
        self.assertIn("promotion_pending", payload)
        self.assertFalse(payload["promotion_pending"])
        self.assertIsNone(payload["promotion_square"])
        self.assertIn("legal_moves", payload)
        self.assertEqual(len(payload["legal_moves"]), 20)

    def test_snapshot_legal_moves_update_after_move(self):
        self.client.post("/game/move/classical", json={"src": "b1", "target": "c3"})
        response = self.client.get("/game")
        payload = response.json()
        self.assertEqual(payload["side_to_move"], "black")
        self.assertEqual(len(payload["legal_moves"]), 20)

    def test_snapshot_promotion_pending_after_pawn_reaches_back_rank(self):
        from api.state_store import store
        from engine.board_state import BoardState
        from engine.game_state import QuantumGame
        basis = BoardState._board_to_tuple({"e7": "P", "a1": "K", "a8": "k"})
        store._game = QuantumGame(board_state=BoardState(amplitudes={basis: 1 + 0j}))
        self.client.post("/game/move/classical", json={"src": "e7", "target": "e8"})
        response = self.client.get("/game")
        payload = response.json()
        self.assertTrue(payload["promotion_pending"])
        self.assertEqual(payload["promotion_square"], "e8")
        self.assertEqual(payload["legal_moves"], [])

    def test_promote_endpoint_replaces_pawn_and_advances_turn(self):
        from engine.board_state import BoardState
        from engine.game_state import QuantumGame
        basis = BoardState._board_to_tuple({"e7": "P", "a1": "K", "a8": "k"})
        store._game = QuantumGame(board_state=BoardState(amplitudes={basis: 1 + 0j}))
        self.client.post("/game/move/classical", json={"src": "e7", "target": "e8"})

        response = self.client.post("/game/move/promote", json={"piece": "Q"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["board"]["e8"], "Q")
        self.assertFalse(payload["promotion_pending"])
        self.assertIsNone(payload["promotion_square"])
        self.assertEqual(payload["side_to_move"], "black")

    def test_promote_endpoint_returns_400_for_invalid_piece(self):
        from engine.board_state import BoardState
        from engine.game_state import QuantumGame
        basis = BoardState._board_to_tuple({"e7": "P", "a1": "K", "a8": "k"})
        store._game = QuantumGame(board_state=BoardState(amplitudes={basis: 1 + 0j}))
        self.client.post("/game/move/classical", json={"src": "e7", "target": "e8"})

        response = self.client.post("/game/move/promote", json={"piece": "K"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("invalid promotion piece", response.json()["detail"])

    def test_promote_endpoint_returns_400_when_no_promotion_pending(self):
        response = self.client.post("/game/move/promote", json={"piece": "Q"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("no promotion is pending", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
