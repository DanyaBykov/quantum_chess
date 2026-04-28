import pathlib
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from engine.board_state import BoardState
from engine.game_state import QuantumGame, game_status, is_in_check, legal_moves_for, validate_move_on_basis


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


class CheckDetectionTest(unittest.TestCase):
    def test_is_in_check_detects_rook_attack(self):
        basis = BoardState._board_to_tuple({"e8": "R", "e1": "k"})
        state = BoardState(amplitudes={basis: 1 + 0j})
        self.assertTrue(is_in_check(state, "black"))

    def test_is_in_check_no_check_when_blocked(self):
        basis = BoardState._board_to_tuple({"e8": "R", "e4": "p", "e1": "k"})
        state = BoardState(amplitudes={basis: 1 + 0j})
        self.assertFalse(is_in_check(state, "black"))

    def test_is_in_check_false_when_safe(self):
        basis = BoardState._board_to_tuple({"a1": "K", "h8": "k"})
        state = BoardState(amplitudes={basis: 1 + 0j})
        self.assertFalse(is_in_check(state, "white"))
        self.assertFalse(is_in_check(state, "black"))

    def test_apply_classical_move_rejects_move_that_exposes_king(self):
        basis = BoardState._board_to_tuple({"e1": "K", "e4": "R", "e8": "q"})
        game = QuantumGame(board_state=BoardState(amplitudes={basis: 1 + 0j}))
        with self.assertRaisesRegex(ValueError, "leaves white's king in check"):
            game.apply_classical_move("e4", "a4")


class LegalMovesTest(unittest.TestCase):
    def test_initial_position_white_has_20_moves(self):
        state = BoardState.initial()
        moves = legal_moves_for(state, "white")
        self.assertEqual(len(moves), 20)

    def test_initial_position_black_also_has_20_moves(self):
        # legal_moves_for doesn't enforce turn — it returns moves regardless of whose turn it is
        state = BoardState.initial()
        moves = legal_moves_for(state, "black")
        self.assertEqual(len(moves), 20)

    def test_returns_empty_when_color_has_no_pieces(self):
        basis = BoardState._board_to_tuple({"e1": "K"})
        state = BoardState(amplitudes={basis: 1 + 0j})
        moves = legal_moves_for(state, "black")
        self.assertEqual(moves, [])

    def test_superposition_excludes_move_blocked_in_one_branch(self):
        import math
        # Knight in superposition at b1: in branch A target c3 is empty (valid),
        # in branch B a white pawn occupies c3 (same-color capture, invalid).
        # The move b1->c3 must be excluded because it's illegal in branch B.
        basis_a = BoardState._board_to_tuple({"b1": "N", "e1": "K", "e8": "k"})
        basis_b = BoardState._board_to_tuple({"b1": "N", "c3": "P", "e1": "K", "e8": "k"})
        amp = 1 / math.sqrt(2)
        state = BoardState(amplitudes={basis_a: amp + 0j, basis_b: amp + 0j})
        moves = legal_moves_for(state, "white")
        self.assertNotIn(("b1", "c3"), moves)
        # But a3 is free in both branches, so b1->a3 should be legal
        self.assertIn(("b1", "a3"), moves)

    def test_pinned_piece_excluded_from_legal_moves(self):
        # White knight on d4 is pinned — any knight move exposes the king on d1 to black rook on d8.
        # Knights cannot slide along the pin axis, so no knight move is legal.
        basis = BoardState._board_to_tuple({"d1": "K", "d4": "N", "d8": "r"})
        state = BoardState(amplitudes={basis: 1 + 0j})
        moves = legal_moves_for(state, "white")
        src_squares = {src for src, _ in moves}
        self.assertNotIn("d4", src_squares)  # knight is pinned — no legal moves
        self.assertIn("d1", src_squares)     # king can still move


class GameStatusTest(unittest.TestCase):
    def test_ongoing_when_legal_moves_exist(self):
        self.assertEqual(game_status(BoardState.initial(), "white"), "ongoing")

    def test_checkmate_when_in_check_with_no_moves(self):
        # White king a1, black queen b3, black rook a8.
        # Rook on a8 checks along the a-file; queen on b3 covers a2, b2, and b1;
        # the king has no legal escape squares.
        basis = BoardState._board_to_tuple({"a1": "K", "b3": "q", "a8": "r"})
        state = BoardState(amplitudes={basis: 1 + 0j})
        self.assertEqual(game_status(state, "white"), "checkmate")

    def test_stalemate_when_no_moves_not_in_check(self):
        # White king a1, black queen b3 — king not in check but no legal moves
        basis = BoardState._board_to_tuple({"a1": "K", "b3": "q"})
        state = BoardState(amplitudes={basis: 1 + 0j})
        self.assertEqual(game_status(state, "white"), "stalemate")


class PromotionTest(unittest.TestCase):
    def test_pawn_reaching_back_rank_sets_promotion_pending(self):
        basis = BoardState._board_to_tuple({"e7": "P", "a1": "K", "a8": "k"})
        game = QuantumGame(board_state=BoardState(amplitudes={basis: 1 + 0j}))
        game.apply_classical_move("e7", "e8")
        self.assertTrue(game.promotion_pending)
        self.assertEqual(game.promotion_square, "e8")
        self.assertEqual(game.side_to_move, "white")  # turn NOT advanced

    def test_apply_promotion_replaces_pawn_and_advances_turn(self):
        basis = BoardState._board_to_tuple({"e7": "P", "a1": "K", "a8": "k"})
        game = QuantumGame(board_state=BoardState(amplitudes={basis: 1 + 0j}))
        game.apply_classical_move("e7", "e8")
        game.apply_promotion("Q")
        self.assertFalse(game.promotion_pending)
        self.assertEqual(game.piece_at("e8"), "Q")
        self.assertEqual(game.side_to_move, "black")

    def test_apply_promotion_rejects_invalid_piece(self):
        basis = BoardState._board_to_tuple({"e7": "P", "a1": "K", "a8": "k"})
        game = QuantumGame(board_state=BoardState(amplitudes={basis: 1 + 0j}))
        game.apply_classical_move("e7", "e8")
        with self.assertRaisesRegex(ValueError, "invalid promotion piece"):
            game.apply_promotion("K")

    def test_apply_classical_move_blocked_when_promotion_pending(self):
        basis = BoardState._board_to_tuple({"e7": "P", "d2": "P", "a1": "K", "a8": "k"})
        game = QuantumGame(board_state=BoardState(amplitudes={basis: 1 + 0j}))
        game.apply_classical_move("e7", "e8")
        with self.assertRaisesRegex(ValueError, "promotion pending"):
            game.apply_classical_move("d2", "d3")

    def test_black_pawn_promotion_pending(self):
        basis = BoardState._board_to_tuple({"e2": "p", "h1": "K", "h8": "k"})
        game = QuantumGame(board_state=BoardState(amplitudes={basis: 1 + 0j}), side_to_move="black")
        game.apply_classical_move("e2", "e1")
        self.assertTrue(game.promotion_pending)
        self.assertEqual(game.promotion_square, "e1")
        self.assertEqual(game.side_to_move, "black")  # turn not advanced

    def test_apply_promotion_works_for_black(self):
        basis = BoardState._board_to_tuple({"e2": "p", "h1": "K", "h8": "k"})
        game = QuantumGame(board_state=BoardState(amplitudes={basis: 1 + 0j}), side_to_move="black")
        game.apply_classical_move("e2", "e1")
        game.apply_promotion("q")
        self.assertEqual(game.piece_at("e1"), "q")
        self.assertEqual(game.side_to_move, "white")
        self.assertIsNone(game.promotion_square)

    def test_apply_promotion_raises_when_not_pending(self):
        basis = BoardState._board_to_tuple({"a1": "K", "a8": "k"})
        game = QuantumGame(board_state=BoardState(amplitudes={basis: 1 + 0j}))
        with self.assertRaisesRegex(ValueError, "no promotion is pending"):
            game.apply_promotion("Q")

    def test_split_move_to_promotion_rank_raises(self):
        # White pawn on e7 cannot split to d8/f8 (diagonal captures to back rank)
        basis = BoardState._board_to_tuple({"e7": "P", "d8": "r", "f8": "r", "a1": "K", "e8": "k"})
        game = QuantumGame(board_state=BoardState(amplitudes={basis: 1 + 0j}))
        with self.assertRaisesRegex(ValueError, "pawn cannot split to promotion rank"):
            game.apply_split_move("e7", "d8", "f8")

    def test_apply_promotion_raises_if_no_pawn_at_square(self):
        # Manually set promotion_pending without a real pawn at the square
        basis = BoardState._board_to_tuple({"a1": "K", "a8": "k"})
        game = QuantumGame(board_state=BoardState(amplitudes={basis: 1 + 0j}))
        game.promotion_pending = True
        game.promotion_square = "e8"  # no pawn here
        with self.assertRaisesRegex(ValueError, "no pawn found"):
            game.apply_promotion("Q")

    def test_split_and_merge_blocked_when_promotion_pending(self):
        basis = BoardState._board_to_tuple({"e7": "P", "b1": "N", "a1": "K", "a8": "k"})
        game = QuantumGame(board_state=BoardState(amplitudes={basis: 1 + 0j}))
        game.apply_classical_move("e7", "e8")
        with self.assertRaisesRegex(ValueError, "promotion pending"):
            game.apply_split_move("b1", "a3", "c3")
        with self.assertRaisesRegex(ValueError, "promotion pending"):
            game.apply_merge_move("b1", "c3", "d2")


class CastlingTest(unittest.TestCase):
    def _kingside_setup(self, color: str) -> QuantumGame:
        """King and kingside rook only — path already clear."""
        if color == "white":
            basis = BoardState._board_to_tuple({"e1": "K", "h1": "R", "e8": "k"})
        else:
            basis = BoardState._board_to_tuple({"e8": "k", "h8": "r", "e1": "K"})
        game = QuantumGame(
            board_state=BoardState(amplitudes={basis: 1 + 0j}),
            side_to_move=color,
        )
        return game

    def _queenside_setup(self, color: str) -> QuantumGame:
        if color == "white":
            basis = BoardState._board_to_tuple({"e1": "K", "a1": "R", "e8": "k"})
        else:
            basis = BoardState._board_to_tuple({"e8": "k", "a8": "r", "e1": "K"})
        game = QuantumGame(
            board_state=BoardState(amplitudes={basis: 1 + 0j}),
            side_to_move=color,
        )
        return game

    def test_white_kingside_castle_moves_king_and_rook(self):
        game = self._kingside_setup("white")
        game.apply_classical_move("e1", "g1")
        self.assertEqual(game.piece_at("g1"), "K")
        self.assertEqual(game.piece_at("f1"), "R")
        self.assertIsNone(game.piece_at("e1"))
        self.assertIsNone(game.piece_at("h1"))

    def test_white_queenside_castle_moves_king_and_rook(self):
        game = self._queenside_setup("white")
        game.apply_classical_move("e1", "c1")
        self.assertEqual(game.piece_at("c1"), "K")
        self.assertEqual(game.piece_at("d1"), "R")
        self.assertIsNone(game.piece_at("e1"))
        self.assertIsNone(game.piece_at("a1"))

    def test_black_kingside_castle_moves_king_and_rook(self):
        game = self._kingside_setup("black")
        game.apply_classical_move("e8", "g8")
        self.assertEqual(game.piece_at("g8"), "k")
        self.assertEqual(game.piece_at("f8"), "r")
        self.assertIsNone(game.piece_at("e8"))
        self.assertIsNone(game.piece_at("h8"))

    def test_black_queenside_castle_moves_king_and_rook(self):
        game = self._queenside_setup("black")
        game.apply_classical_move("e8", "c8")
        self.assertEqual(game.piece_at("c8"), "k")
        self.assertEqual(game.piece_at("d8"), "r")
        self.assertIsNone(game.piece_at("e8"))
        self.assertIsNone(game.piece_at("a8"))

    def test_castle_blocked_by_piece_in_path(self):
        basis = BoardState._board_to_tuple({"e1": "K", "h1": "R", "f1": "B", "e8": "k"})
        game = QuantumGame(board_state=BoardState(amplitudes={basis: 1 + 0j}))
        with self.assertRaisesRegex(ValueError, "illegal move"):
            game.apply_classical_move("e1", "g1")

    def test_castle_not_in_legal_moves_when_king_in_check(self):
        # King is under attack — castling must not appear in legal moves
        basis = BoardState._board_to_tuple({"e1": "K", "h1": "R", "e8": "k", "e5": "r"})
        state = BoardState(amplitudes={basis: 1 + 0j})
        rights = {"white_kingside": True, "white_queenside": True,
                  "black_kingside": True, "black_queenside": True}
        moves = legal_moves_for(state, "white", castling_rights=rights)
        self.assertNotIn(("e1", "g1"), moves)

    def test_castle_not_in_legal_moves_when_passing_through_attacked_square(self):
        # Black rook attacks f1 — white cannot castle kingside (king passes through f1)
        basis = BoardState._board_to_tuple({"e1": "K", "h1": "R", "e8": "k", "f5": "r"})
        state = BoardState(amplitudes={basis: 1 + 0j})
        rights = {"white_kingside": True, "white_queenside": True,
                  "black_kingside": True, "black_queenside": True}
        moves = legal_moves_for(state, "white", castling_rights=rights)
        self.assertNotIn(("e1", "g1"), moves)

    def test_castling_rights_revoked_after_king_moves(self):
        game = self._kingside_setup("white")
        game.apply_classical_move("e1", "f1")  # normal king move
        # Now try to move back and castle — rights should be gone
        game.side_to_move = "white"
        game.apply_classical_move("f1", "e1")
        game.side_to_move = "white"
        self.assertFalse(game.castling_rights["white_kingside"])
        with self.assertRaisesRegex(ValueError, "castling rights lost"):
            game.apply_classical_move("e1", "g1")

    def test_castling_rights_revoked_after_rook_moves(self):
        game = self._kingside_setup("white")
        game.apply_classical_move("h1", "g1")  # rook moves
        game.side_to_move = "white"
        game.apply_classical_move("g1", "h1")  # rook returns
        game.side_to_move = "white"
        self.assertFalse(game.castling_rights["white_kingside"])
        with self.assertRaisesRegex(ValueError, "castling rights lost"):
            game.apply_classical_move("e1", "g1")

    def test_castling_rights_revoked_for_king_after_split(self):
        basis = BoardState._board_to_tuple({"e1": "K", "h1": "R", "e8": "k", "f1": None, "d1": None})
        # Give king squares to split to
        basis2 = BoardState._board_to_tuple({"e1": "K", "h1": "R", "e8": "k"})
        game = QuantumGame(board_state=BoardState(amplitudes={basis2: 1 + 0j}))
        # Split king to d1 and f1 — both must be reachable
        game.apply_split_move("e1", "d1", "f1")
        self.assertFalse(game.castling_rights["white_kingside"])
        self.assertFalse(game.castling_rights["white_queenside"])


class EnPassantTest(unittest.TestCase):
    def test_en_passant_target_set_after_two_step_pawn_move(self):
        basis = BoardState._board_to_tuple({"e2": "P", "e1": "K", "e8": "k"})
        game = QuantumGame(board_state=BoardState(amplitudes={basis: 1 + 0j}))
        game.apply_classical_move("e2", "e4")
        self.assertEqual(game.en_passant_target, "e3")

    def test_en_passant_target_cleared_after_non_two_step_move(self):
        basis = BoardState._board_to_tuple({"e4": "P", "e1": "K", "e8": "k"})
        game = QuantumGame(
            board_state=BoardState(amplitudes={basis: 1 + 0j}),
            en_passant_target="e3",
        )
        game.apply_classical_move("e4", "e5")
        self.assertIsNone(game.en_passant_target)

    def test_white_captures_en_passant(self):
        # Black pawn just moved d7→d5; white pawn at e5 can capture en passant to d6
        basis = BoardState._board_to_tuple({"e5": "P", "d5": "p", "e1": "K", "e8": "k"})
        game = QuantumGame(
            board_state=BoardState(amplitudes={basis: 1 + 0j}),
            en_passant_target="d6",
        )
        game.apply_classical_move("e5", "d6")
        self.assertEqual(game.piece_at("d6"), "P")
        self.assertIsNone(game.piece_at("e5"))
        self.assertIsNone(game.piece_at("d5"))  # captured pawn removed

    def test_black_captures_en_passant(self):
        # White pawn just moved e2→e4; black pawn at d4 can capture en passant to e3
        basis = BoardState._board_to_tuple({"d4": "p", "e4": "P", "e1": "K", "e8": "k"})
        game = QuantumGame(
            board_state=BoardState(amplitudes={basis: 1 + 0j}),
            side_to_move="black",
            en_passant_target="e3",
        )
        game.apply_classical_move("d4", "e3")
        self.assertEqual(game.piece_at("e3"), "p")
        self.assertIsNone(game.piece_at("d4"))
        self.assertIsNone(game.piece_at("e4"))  # captured white pawn removed

    def test_en_passant_appears_in_legal_moves(self):
        basis = BoardState._board_to_tuple({"e5": "P", "d5": "p", "e1": "K", "e8": "k"})
        state = BoardState(amplitudes={basis: 1 + 0j})
        moves = legal_moves_for(state, "white", en_passant_target="d6")
        self.assertIn(("e5", "d6"), moves)

    def test_en_passant_not_in_legal_moves_without_target(self):
        basis = BoardState._board_to_tuple({"e5": "P", "d5": "p", "e1": "K", "e8": "k"})
        state = BoardState(amplitudes={basis: 1 + 0j})
        moves = legal_moves_for(state, "white")  # no en_passant_target
        self.assertNotIn(("e5", "d6"), moves)

    def test_en_passant_target_cleared_after_split_move(self):
        basis = BoardState._board_to_tuple({"b1": "N", "e1": "K", "e8": "k"})
        game = QuantumGame(
            board_state=BoardState(amplitudes={basis: 1 + 0j}),
            en_passant_target="e3",
        )
        game.apply_split_move("b1", "a3", "c3")
        self.assertIsNone(game.en_passant_target)


if __name__ == "__main__":
    unittest.main()
