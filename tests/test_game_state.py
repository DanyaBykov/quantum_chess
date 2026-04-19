import pathlib
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from engine.board_state import BoardState
from engine.game_state import QuantumGame, validate_move_on_basis


class MoveValidationTest(unittest.TestCase):
    def test_validate_move_on_basis_allows_clear_knight_move(self):
        basis = BoardState._board_to_tuple({"b1": "N"})

        piece = validate_move_on_basis(basis, "b1", "c3")

        self.assertEqual(piece, "N")

    def test_validate_move_on_basis_rejects_blocked_bishop(self):
        basis = BoardState._board_to_tuple({"c1": "B", "d2": "P"})

        with self.assertRaisesRegex(ValueError, "illegal move"):
            validate_move_on_basis(basis, "c1", "g5")

    def test_validate_move_on_basis_rejects_same_color_capture(self):
        basis = BoardState._board_to_tuple({"a1": "R", "a3": "P"})

        with self.assertRaisesRegex(ValueError, "illegal move"):
            validate_move_on_basis(basis, "a1", "a3")

    def test_validate_move_on_basis_allows_pawn_two_step_from_start(self):
        basis = BoardState._board_to_tuple({"e2": "P"})

        piece = validate_move_on_basis(basis, "e2", "e4")

        self.assertEqual(piece, "P")


class QuantumGameTest(unittest.TestCase):
    def test_initial_game_starts_with_white_to_move(self):
        game = QuantumGame.initial()

        self.assertEqual(game.side_to_move, "white")
        self.assertEqual(game.fullmove_number, 1)
        self.assertEqual(game.piece_at("e1"), "K")
        self.assertEqual(game.piece_at("e8"), "k")

    def test_apply_classical_move_updates_board_and_turn(self):
        game = QuantumGame(
            board_state=BoardState(amplitudes={BoardState._board_to_tuple({"b1": "N"}): 1 + 0j})
        )

        game.apply_classical_move("b1", "c3")

        self.assertIsNone(game.piece_at("b1"))
        self.assertEqual(game.piece_at("c3"), "N")
        self.assertEqual(game.side_to_move, "black")
        self.assertEqual(game.fullmove_number, 1)

    def test_apply_classical_move_rejects_wrong_side_to_move(self):
        game = QuantumGame(
            board_state=BoardState(amplitudes={BoardState._board_to_tuple({"b8": "n"}): 1 + 0j})
        )

        with self.assertRaisesRegex(ValueError, "white's turn"):
            game.apply_classical_move("b8", "c6")

    def test_apply_classical_move_advances_fullmove_after_black_turn(self):
        white_basis = BoardState._board_to_tuple({"b1": "N", "b8": "n"})
        game = QuantumGame(board_state=BoardState(amplitudes={white_basis: 1 + 0j}))

        game.apply_classical_move("b1", "c3")
        game.apply_classical_move("b8", "c6")

        self.assertEqual(game.side_to_move, "white")
        self.assertEqual(game.fullmove_number, 2)

    def test_apply_split_move_requires_legal_targets(self):
        game = QuantumGame(
            board_state=BoardState(amplitudes={BoardState._board_to_tuple({"c1": "B", "d2": "P"}): 1 + 0j})
        )

        with self.assertRaisesRegex(ValueError, "illegal move"):
            game.apply_split_move("c1", "g5", "h6")

    def test_apply_split_move_updates_board_state(self):
        game = QuantumGame(
            board_state=BoardState(amplitudes={BoardState._board_to_tuple({"b1": "N"}): 1 + 0j})
        )

        game.apply_split_move("b1", "a3", "c3")

        self.assertAlmostEqual(game.board_state.probability("a3"), 0.5)
        self.assertAlmostEqual(game.board_state.probability("c3"), 0.5)
        self.assertEqual(game.side_to_move, "black")

    def test_apply_merge_move_rejects_different_piece_identities(self):
        basis_a = BoardState._board_to_tuple({"a3": "N"})
        basis_b = BoardState._board_to_tuple({"c3": "B"})
        game = QuantumGame(board_state=BoardState(amplitudes={basis_a: 0.5 + 0j, basis_b: 0.5 + 0j}))

        with self.assertRaisesRegex(ValueError, "matching piece identities"):
            game.apply_merge_move("a3", "c3", "b1")

    def test_apply_merge_move_round_trips_split_knight(self):
        game = QuantumGame(
            board_state=BoardState(amplitudes={BoardState._board_to_tuple({"b1": "N"}): 1 + 0j})
        )

        game.apply_split_move("b1", "a3", "c3")
        game.side_to_move = "white"
        game.apply_merge_move("a3", "c3", "b1")

        self.assertEqual(list(game.board_state.amplitudes.keys()), [BoardState._board_to_tuple({"b1": "N"})])
        self.assertAlmostEqual(abs(next(iter(game.board_state.amplitudes.values()))) ** 2, 1.0)

    @patch("engine.game_state.measure")
    def test_measure_square_delegates_to_quantum_measurement(self, measure_mock):
        initial_state = BoardState(amplitudes={BoardState._board_to_tuple({"d4": "Q"}): 1 + 0j})
        collapsed_state = BoardState(amplitudes={BoardState._board_to_tuple({}): 1 + 0j})
        measure_mock.return_value = collapsed_state
        game = QuantumGame(board_state=initial_state)

        game.measure_square("d4")

        measure_mock.assert_called_once_with(initial_state, "d4")
        self.assertIs(game.board_state, collapsed_state)


if __name__ == "__main__":
    unittest.main()
