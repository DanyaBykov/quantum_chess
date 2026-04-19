import math
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from engine.board_state import BoardState, _initial_basis_state, parse_square


class ParseSquareTest(unittest.TestCase):
    def test_parse_square_maps_board_coordinates(self):
        self.assertEqual(parse_square("a1"), 0)
        self.assertEqual(parse_square("h1"), 7)
        self.assertEqual(parse_square("a8"), 56)
        self.assertEqual(parse_square("h8"), 63)

    def test_parse_square_rejects_invalid_coordinates(self):
        with self.assertRaises(ValueError):
            parse_square("z9")


class BoardStateTest(unittest.TestCase):
    def test_initial_creates_standard_starting_position(self):
        state = BoardState.initial()

        self.assertEqual(len(state.amplitudes), 1)
        basis, amplitude = next(iter(state.amplitudes.items()))

        self.assertEqual(amplitude, 1.0 + 0.0j)
        self.assertEqual(basis[parse_square("a1")], "R")
        self.assertEqual(basis[parse_square("e1")], "K")
        self.assertEqual(basis[parse_square("a2")], "P")
        self.assertEqual(basis[parse_square("a7")], "p")
        self.assertEqual(basis[parse_square("e8")], "k")
        self.assertIsNone(basis[parse_square("d4")])

    def test_board_to_tuple_builds_expected_layout(self):
        basis = BoardState._board_to_tuple({"a1": "K", "h8": "k", "d4": "Q"})

        self.assertEqual(basis[parse_square("a1")], "K")
        self.assertEqual(basis[parse_square("h8")], "k")
        self.assertEqual(basis[parse_square("d4")], "Q")
        self.assertIsNone(basis[parse_square("b2")])

    def test_amplitude_sums_occupied_basis_amplitudes(self):
        occupied = BoardState._board_to_tuple({"d4": "Q"})
        empty = BoardState._board_to_tuple({})
        state = BoardState(amplitudes={occupied: 0.5 + 0.5j, empty: 0.5 + 0.0j})

        self.assertEqual(state.amplitude("d4"), 0.5 + 0.5j)
        self.assertEqual(state.amplitude("a1"), 0j)

    def test_probability_sums_basis_probabilities(self):
        occupied_a = BoardState._board_to_tuple({"d4": "Q"})
        occupied_b = BoardState._board_to_tuple({"d4": "R"})
        amplitude = 1 / math.sqrt(2)
        state = BoardState(
            amplitudes={
                occupied_a: amplitude + 0j,
                occupied_b: -amplitude + 0j,
            }
        )

        self.assertEqual(state.amplitude("d4"), 0j)
        self.assertAlmostEqual(state.probability("d4"), 1.0)

    def test_normalize_scales_amplitudes_to_total_probability_one(self):
        basis_a = BoardState._board_to_tuple({"a1": "K"})
        basis_b = BoardState._board_to_tuple({"b1": "Q"})
        state = BoardState(amplitudes={basis_a: 1 + 0j, basis_b: 1 + 0j})

        state.normalize()

        total_probability = sum(abs(amp) ** 2 for amp in state.amplitudes.values())
        self.assertAlmostEqual(total_probability, 1.0)
        self.assertAlmostEqual(abs(state.amplitudes[basis_a]) ** 2, 0.5)
        self.assertAlmostEqual(abs(state.amplitudes[basis_b]) ** 2, 0.5)

    def test_prune_states_drops_low_probability_entries_and_renormalizes(self):
        basis_a = BoardState._board_to_tuple({"a1": "K"})
        basis_b = BoardState._board_to_tuple({"b1": "Q"})
        state = BoardState(amplitudes={basis_a: 1 + 0j, basis_b: 0.01 + 0j})

        state.prune_states(threshold=0.001)

        self.assertEqual(state.amplitudes, {basis_a: 1 + 0j})

    def test_initial_basis_state_matches_initial_state(self):
        state = BoardState.initial()
        basis, _ = next(iter(state.amplitudes.items()))

        self.assertEqual(basis, _initial_basis_state())


if __name__ == "__main__":
    unittest.main()
