import math
import pathlib
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from engine.board_state import BoardState, parse_square
from engine.quantum_ops import _move_piece_in_tuple, measure, merge_move, split_move


class QuantumOpsTest(unittest.TestCase):
    def test_move_piece_in_tuple_moves_piece_between_indices(self):
        basis = BoardState._board_to_tuple({"b1": "N"})

        moved = _move_piece_in_tuple(basis, parse_square("b1"), parse_square("c3"))

        self.assertIsNone(moved[parse_square("b1")])
        self.assertEqual(moved[parse_square("c3")], "N")

    def test_split_move_splits_amplitude_between_targets(self):
        state = BoardState(amplitudes={BoardState._board_to_tuple({"b1": "N"}): 1 + 0j})

        new_state = split_move(state, "b1", "a3", "c3")

        self.assertEqual(len(new_state.amplitudes), 2)
        self.assertAlmostEqual(abs(new_state.amplitudes[BoardState._board_to_tuple({"a3": "N"})]) ** 2, 0.5)
        self.assertAlmostEqual(abs(new_state.amplitudes[BoardState._board_to_tuple({"c3": "N"})]) ** 2, 0.5)

    def test_split_move_preserves_basis_without_source_piece(self):
        basis = BoardState._board_to_tuple({"a1": "K"})
        state = BoardState(amplitudes={basis: 1 + 0j})

        new_state = split_move(state, "b1", "a3", "c3")

        self.assertEqual(new_state.amplitudes, {basis: 1 + 0j})

    def test_merge_move_combines_sources_into_target_basis(self):
        amplitude = 1 / math.sqrt(2)
        state = BoardState(
            amplitudes={
                BoardState._board_to_tuple({"a3": "N"}): amplitude + 0j,
                BoardState._board_to_tuple({"c3": "N"}): amplitude + 0j,
            }
        )

        new_state = merge_move(state, "a3", "c3", "b1")

        self.assertEqual(list(new_state.amplitudes.keys()), [BoardState._board_to_tuple({"b1": "N"})])
        self.assertAlmostEqual(abs(next(iter(new_state.amplitudes.values()))) ** 2, 1.0)

    @patch("engine.quantum_ops.random.choices", return_value=[True])
    def test_measure_keeps_occupied_branches_when_observed_occupied(self, _mock_choices):
        amplitude = 1 / math.sqrt(2)
        occupied = BoardState._board_to_tuple({"d4": "Q"})
        empty = BoardState._board_to_tuple({})
        state = BoardState(amplitudes={occupied: amplitude + 0j, empty: amplitude + 0j})

        collapsed = measure(state, "d4")

        self.assertEqual(collapsed.amplitudes, {occupied: 1 + 0j})

    @patch("engine.quantum_ops.random.choices", return_value=[False])
    def test_measure_keeps_empty_branches_when_observed_empty(self, _mock_choices):
        amplitude = 1 / math.sqrt(2)
        occupied = BoardState._board_to_tuple({"d4": "Q"})
        empty = BoardState._board_to_tuple({})
        state = BoardState(amplitudes={occupied: amplitude + 0j, empty: amplitude + 0j})

        collapsed = measure(state, "d4")

        self.assertEqual(collapsed.amplitudes, {empty: 1 + 0j})


if __name__ == "__main__":
    unittest.main()
