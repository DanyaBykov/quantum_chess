from dataclasses import dataclass, field
from typing import Iterable, Optional

from engine.board_state import BoardState, BasisState, parse_square, square_name
from engine.quantum_ops import measure, merge_move, split_move


def _piece_color(piece: str) -> str:
    return "white" if piece.isupper() else "black"


def _same_square(src_idx: int, tgt_idx: int) -> bool:
    return src_idx == tgt_idx


def _delta(src_idx: int, tgt_idx: int) -> tuple[int, int]:
    src_file = src_idx % 8
    src_rank = src_idx // 8
    tgt_file = tgt_idx % 8
    tgt_rank = tgt_idx // 8
    return tgt_file - src_file, tgt_rank - src_rank


def _path_is_clear(basis: BasisState, src_idx: int, tgt_idx: int) -> bool:
    file_delta, rank_delta = _delta(src_idx, tgt_idx)
    step_file = 0 if file_delta == 0 else file_delta // abs(file_delta)
    step_rank = 0 if rank_delta == 0 else rank_delta // abs(rank_delta)

    src_file = src_idx % 8
    src_rank = src_idx // 8
    tgt_file = tgt_idx % 8
    tgt_rank = tgt_idx // 8

    current_file = src_file + step_file
    current_rank = src_rank + step_rank
    while (current_file, current_rank) != (tgt_file, tgt_rank):
        current_idx = current_file + 8 * current_rank
        if basis[current_idx] is not None:
            return False
        current_file += step_file
        current_rank += step_rank

    return True


def _is_legal_piece_move(
    piece: str,
    src_idx: int,
    tgt_idx: int,
    basis: BasisState,
    *,
    allow_empty_target_for_pawn_diagonal: bool = False,
    en_passant_idx: Optional[int] = None,
) -> bool:
    if _same_square(src_idx, tgt_idx):
        return False

    target_piece = basis[tgt_idx]
    if target_piece is not None and _piece_color(target_piece) == _piece_color(piece):
        return False

    file_delta, rank_delta = _delta(src_idx, tgt_idx)
    abs_file = abs(file_delta)
    abs_rank = abs(rank_delta)
    lower_piece = piece.lower()

    if lower_piece == "n":
        return (abs_file, abs_rank) in {(1, 2), (2, 1)}

    if lower_piece == "k":
        if max(abs_file, abs_rank) == 1:
            return True
        # Castling: king moves 2 squares horizontally from starting position
        if rank_delta == 0 and abs_file == 2:
            src_rank = src_idx // 8
            expected_rank = 0 if piece.isupper() else 7
            if src_rank != expected_rank or src_idx % 8 != 4:
                return False
            rook_piece = "R" if piece.isupper() else "r"
            rook_src = src_rank * 8 + (7 if file_delta > 0 else 0)
            if basis[rook_src] != rook_piece:
                return False
            return _path_is_clear(basis, src_idx, rook_src)
        return False

    if lower_piece == "b":
        return abs_file == abs_rank and _path_is_clear(basis, src_idx, tgt_idx)

    if lower_piece == "r":
        return (file_delta == 0 or rank_delta == 0) and _path_is_clear(basis, src_idx, tgt_idx)

    if lower_piece == "q":
        diagonal = abs_file == abs_rank
        straight = file_delta == 0 or rank_delta == 0
        return (diagonal or straight) and _path_is_clear(basis, src_idx, tgt_idx)

    if lower_piece == "p":
        direction = 1 if piece.isupper() else -1
        src_rank = src_idx // 8
        start_rank = 1 if piece.isupper() else 6
        one_step = file_delta == 0 and rank_delta == direction and target_piece is None
        two_step = (
            file_delta == 0
            and rank_delta == 2 * direction
            and src_rank == start_rank
            and target_piece is None
            and _path_is_clear(basis, src_idx, tgt_idx)
        )
        diagonal_capture = abs_file == 1 and rank_delta == direction and (
            (target_piece is not None and _piece_color(target_piece) != _piece_color(piece))
            or allow_empty_target_for_pawn_diagonal
            or (en_passant_idx is not None and tgt_idx == en_passant_idx)
        )
        return one_step or two_step or diagonal_capture

    return False


def _apply_move_to_basis(
    basis: list,
    src_idx: int,
    tgt_idx: int,
    en_passant_idx: Optional[int],
) -> None:
    """Apply a move with its implicit side-effects to a mutable basis list in-place."""
    piece = basis[src_idx]
    basis[tgt_idx] = piece
    basis[src_idx] = None

    if piece is None:
        return

    # En passant: remove captured pawn from its actual square (adjacent to landing square)
    if piece.lower() == "p" and en_passant_idx is not None and tgt_idx == en_passant_idx:
        direction = 1 if piece.isupper() else -1
        captured_rank = (en_passant_idx // 8) - direction
        basis[captured_rank * 8 + (en_passant_idx % 8)] = None

    # Castling: move rook alongside the king
    if piece.lower() == "k":
        file_delta = (tgt_idx % 8) - (src_idx % 8)
        if abs(file_delta) == 2:
            rank = src_idx // 8
            if file_delta > 0:  # kingside: rook h→f
                basis[rank * 8 + 5] = basis[rank * 8 + 7]
                basis[rank * 8 + 7] = None
            else:              # queenside: rook a→d
                basis[rank * 8 + 3] = basis[rank * 8 + 0]
                basis[rank * 8 + 0] = None


def validate_move_on_basis(
    basis: BasisState,
    src: str,
    target: str,
    *,
    allow_empty_target_for_pawn_diagonal: bool = False,
    en_passant_idx: Optional[int] = None,
    castling_rights: Optional[dict] = None,
) -> str:
    src_idx = parse_square(src)
    tgt_idx = parse_square(target)
    piece = basis[src_idx]
    if piece is None:
        raise ValueError(f"no piece at source square {src}")

    # Check castling rights before the board-geometry test
    if piece.lower() == "k" and castling_rights is not None:
        file_delta = (tgt_idx % 8) - (src_idx % 8)
        if abs(file_delta) == 2:
            side = "white" if piece.isupper() else "black"
            flank = "kingside" if file_delta > 0 else "queenside"
            if not castling_rights.get(f"{side}_{flank}", False):
                raise ValueError(f"castling rights lost: {side} {flank}")

    if not _is_legal_piece_move(
        piece,
        src_idx,
        tgt_idx,
        basis,
        allow_empty_target_for_pawn_diagonal=allow_empty_target_for_pawn_diagonal,
        en_passant_idx=en_passant_idx,
    ):
        raise ValueError(f"illegal move for {piece} from {src} to {target}")

    return piece


def _occupied_basis_states(state: BoardState, src: str) -> Iterable[BasisState]:
    src_idx = parse_square(src)
    for basis in state.amplitudes:
        if basis[src_idx] is not None:
            yield basis


def _piece_for_quantum_source(state: BoardState, src: str) -> str:
    piece = state.occupied_piece(src)
    if piece is None:
        raise ValueError(f"no piece present at {src}")
    return piece


def _king_square(basis: BasisState, color: str) -> Optional[int]:
    king_piece = "K" if color == "white" else "k"
    for idx, piece in enumerate(basis):
        if piece == king_piece:
            return idx
    return None


def is_in_check(state: BoardState, color: str) -> bool:
    """Return True if color's king is attacked in ANY basis state of the superposition."""
    opponent_color = "black" if color == "white" else "white"
    for basis in state.amplitudes:
        king_idx = _king_square(basis, color)
        if king_idx is None:
            continue
        for src_idx, piece in enumerate(basis):
            if piece is None:
                continue
            if _piece_color(piece) != opponent_color:
                continue
            if _is_legal_piece_move(piece, src_idx, king_idx, basis):
                return True
    return False


_ALL_SQUARES: list[str] = [square_name(idx) for idx in range(64)]


def legal_moves_for(
    state: BoardState,
    color: str,
    *,
    castling_rights: Optional[dict] = None,
    en_passant_target: Optional[str] = None,
) -> list[tuple[str, str]]:
    """Return all legal (src, target) move pairs for the given color.

    A move is legal if:
    - The color has a piece at src in at least one basis state.
    - validate_move_on_basis succeeds on every occupied basis state for src.
    - The modified branches after the move do not leave color's king in check.
    - For castling: king is not currently in check, and does not pass through check.
    """
    ep_idx = parse_square(en_passant_target) if en_passant_target else None

    src_squares: set[str] = set()
    for basis in state.amplitudes:
        for idx, piece in enumerate(basis):
            if piece is not None and _piece_color(piece) == color:
                src_squares.add(square_name(idx))

    if not src_squares:
        return []

    result: list[tuple[str, str]] = []

    for src in src_squares:
        src_idx = parse_square(src)
        occupied_bases = [
            (basis, amp)
            for basis, amp in state.amplitudes.items()
            if basis[src_idx] is not None
        ]

        for target in _ALL_SQUARES:
            if target == src:
                continue

            tgt_idx = parse_square(target)

            valid = True
            for basis, _ in occupied_bases:
                try:
                    validate_move_on_basis(
                        basis, src, target,
                        en_passant_idx=ep_idx,
                        castling_rights=castling_rights,
                    )
                except ValueError:
                    valid = False
                    break

            if not valid:
                continue

            # Build modified branches including castling rook and en passant pawn removal
            modified: dict = {}
            for basis, amp in occupied_bases:
                moved = list(basis)
                _apply_move_to_basis(moved, src_idx, tgt_idx, ep_idx)
                moved_t = tuple(moved)
                modified[moved_t] = modified.get(moved_t, 0j) + amp

            if not modified:
                continue

            trial = BoardState(amplitudes=dict(modified), entanglement_map=state.entanglement_map)
            trial.normalize()
            if is_in_check(trial, color):
                continue

            # Castling extra guards: not while in check, not through check
            piece_at_src = occupied_bases[0][0][src_idx]
            if piece_at_src is not None and piece_at_src.lower() == "k":
                file_delta = (tgt_idx % 8) - (src_idx % 8)
                if abs(file_delta) == 2:
                    if is_in_check(state, color):
                        continue
                    pass_idx = src_idx + (1 if file_delta > 0 else -1)
                    pass_modified: dict = {}
                    for basis, amp in occupied_bases:
                        moved2 = list(basis)
                        moved2[pass_idx] = moved2[src_idx]
                        moved2[src_idx] = None
                        moved2_t = tuple(moved2)
                        pass_modified[moved2_t] = pass_modified.get(moved2_t, 0j) + amp
                    if pass_modified:
                        pass_trial = BoardState(
                            amplitudes=dict(pass_modified),
                            entanglement_map=state.entanglement_map,
                        )
                        pass_trial.normalize()
                        if is_in_check(pass_trial, color):
                            continue

            result.append((src, target))

    return result


def game_status(
    state: BoardState,
    side_to_move: str,
    *,
    castling_rights: Optional[dict] = None,
    en_passant_target: Optional[str] = None,
) -> str:
    """Return 'ongoing', 'checkmate', or 'stalemate' for the side to move."""
    if legal_moves_for(
        state, side_to_move,
        castling_rights=castling_rights,
        en_passant_target=en_passant_target,
    ):
        return "ongoing"
    if is_in_check(state, side_to_move):
        return "checkmate"
    return "stalemate"


_CASTLING_INITIAL = {
    "white_kingside": True,
    "white_queenside": True,
    "black_kingside": True,
    "black_queenside": True,
}

# Squares whose occupant moving revokes the associated castling right(s)
_CASTLING_REVOKE_MAP: dict[int, list[str]] = {
    parse_square("e1"): ["white_kingside", "white_queenside"],
    parse_square("h1"): ["white_kingside"],
    parse_square("a1"): ["white_queenside"],
    parse_square("e8"): ["black_kingside", "black_queenside"],
    parse_square("h8"): ["black_kingside"],
    parse_square("a8"): ["black_queenside"],
}


@dataclass
class QuantumGame:
    board_state: BoardState
    side_to_move: str = "white"
    fullmove_number: int = 1
    promotion_pending: bool = False
    promotion_square: Optional[str] = None
    castling_rights: dict = field(default_factory=lambda: dict(_CASTLING_INITIAL))
    en_passant_target: Optional[str] = None

    @classmethod
    def initial(cls) -> "QuantumGame":
        return cls(board_state=BoardState.initial())

    def piece_at(self, square: str) -> Optional[str]:
        return self.board_state.occupied_piece(square)

    def _assert_side_to_move(self, piece: str):
        if _piece_color(piece) != self.side_to_move:
            raise ValueError(f"it is {self.side_to_move}'s turn, not {_piece_color(piece)}'s")

    def _advance_turn(self):
        if self.side_to_move == "white":
            self.side_to_move = "black"
            return
        self.side_to_move = "white"
        self.fullmove_number += 1

    def _revoke_castling_rights(self, square_idx: int) -> None:
        for right in _CASTLING_REVOKE_MAP.get(square_idx, []):
            self.castling_rights[right] = False

    def apply_classical_move(self, src: str, target: str):
        if self.promotion_pending:
            raise ValueError("promotion pending: call apply_promotion first")
        occupied_bases = list(_occupied_basis_states(self.board_state, src))
        if not occupied_bases:
            raise ValueError(f"no piece present at {src}")

        piece = self.board_state.occupied_piece(src)
        if piece is None:
            raise ValueError(f"no piece present at {src}")

        self._assert_side_to_move(piece)

        ep_idx = parse_square(self.en_passant_target) if self.en_passant_target else None
        for basis in occupied_bases:
            validate_move_on_basis(
                basis, src, target,
                en_passant_idx=ep_idx,
                castling_rights=self.castling_rights,
            )

        src_idx = parse_square(src)
        tgt_idx = parse_square(target)

        modified: dict = {}
        unmodified: dict = {}
        for basis, amplitude in self.board_state.amplitudes.items():
            if basis[src_idx] is None:
                unmodified[basis] = amplitude
                continue
            moved = list(basis)
            _apply_move_to_basis(moved, src_idx, tgt_idx, ep_idx)
            moved_t = tuple(moved)
            modified[moved_t] = modified.get(moved_t, 0j) + amplitude

        if modified:
            trial = BoardState(
                amplitudes=dict(modified),
                entanglement_map=self.board_state.entanglement_map,
            )
            trial.normalize()
            color = _piece_color(piece)
            if is_in_check(trial, color):
                raise ValueError(f"move leaves {color}'s king in check")

        self.board_state = BoardState(
            amplitudes={**modified, **unmodified},
            entanglement_map=self.board_state.entanglement_map,
        )
        self.board_state.normalize()

        # Revoke rights for the moved piece and for any rook captured on its home square
        self._revoke_castling_rights(src_idx)
        self._revoke_castling_rights(tgt_idx)

        # Track en passant target for opponent's next move
        if piece.lower() == "p" and abs(tgt_idx - src_idx) == 16:
            self.en_passant_target = square_name((src_idx + tgt_idx) // 2)
        else:
            self.en_passant_target = None

        if (piece == "P" and tgt_idx // 8 == 7) or (piece == "p" and tgt_idx // 8 == 0):
            self.promotion_pending = True
            self.promotion_square = target
            return

        self._advance_turn()

    def apply_split_move(self, src: str, target_a: str, target_b: str):
        if self.promotion_pending:
            raise ValueError("promotion pending: call apply_promotion first")
        if target_a == target_b:
            raise ValueError("split move targets must differ")

        piece = _piece_for_quantum_source(self.board_state, src)
        self._assert_side_to_move(piece)

        occupied_bases = list(_occupied_basis_states(self.board_state, src))
        # castling_rights={} prevents a king from treating a 2-square move as castling;
        # split/merge never move the rook, so castling is disallowed in these modes.
        for basis in occupied_bases:
            validate_move_on_basis(basis, src, target_a, castling_rights={})
            validate_move_on_basis(basis, src, target_b, castling_rights={})

        if piece.lower() == "p":
            back_rank = 7 if piece.isupper() else 0
            if parse_square(target_a) // 8 == back_rank or parse_square(target_b) // 8 == back_rank:
                raise ValueError("pawn cannot split to promotion rank")

        self._revoke_castling_rights(parse_square(src))
        self.en_passant_target = None

        self.board_state = split_move(self.board_state, src, target_a, target_b)
        self.board_state.normalize()
        self._advance_turn()

    def apply_merge_move(self, src_a: str, src_b: str, target: str):
        if self.promotion_pending:
            raise ValueError("promotion pending: call apply_promotion first")
        piece_a = _piece_for_quantum_source(self.board_state, src_a)
        piece_b = _piece_for_quantum_source(self.board_state, src_b)
        if piece_a != piece_b:
            raise ValueError("merge move requires matching piece identities")

        self._assert_side_to_move(piece_a)

        occupied_a = list(_occupied_basis_states(self.board_state, src_a))
        occupied_b = list(_occupied_basis_states(self.board_state, src_b))
        if not occupied_a or not occupied_b:
            raise ValueError("merge move requires occupied branches at both source squares")

        for basis in occupied_a:
            validate_move_on_basis(
                basis, src_a, target,
                allow_empty_target_for_pawn_diagonal=piece_a.lower() == "p",
                castling_rights={},
            )
        for basis in occupied_b:
            validate_move_on_basis(
                basis, src_b, target,
                allow_empty_target_for_pawn_diagonal=piece_b.lower() == "p",
                castling_rights={},
            )

        self._revoke_castling_rights(parse_square(src_a))
        self._revoke_castling_rights(parse_square(src_b))
        self.en_passant_target = None

        self.board_state = merge_move(self.board_state, src_a, src_b, target)
        self._advance_turn()

    def apply_promotion(self, chosen_piece: str):
        if not self.promotion_pending:
            raise ValueError("no promotion is pending")
        color_pieces = {"Q", "R", "B", "N"} if self.side_to_move == "white" else {"q", "r", "b", "n"}
        if chosen_piece not in color_pieces:
            raise ValueError(f"invalid promotion piece: {chosen_piece!r}")
        sq_idx = parse_square(self.promotion_square)
        new_amplitudes = {}
        for basis, amp in self.board_state.amplitudes.items():
            lst = list(basis)
            if lst[sq_idx] is not None:
                lst[sq_idx] = chosen_piece
            new_amplitudes[tuple(lst)] = amp
        if not any(b[sq_idx] is not None for b in self.board_state.amplitudes):
            raise ValueError("no pawn found at promotion square — board state is inconsistent")
        self.board_state = BoardState(
            amplitudes=new_amplitudes,
            entanglement_map=self.board_state.entanglement_map,
        )
        self.promotion_pending = False
        self.promotion_square = None
        self._advance_turn()

    def measure_square(self, target: str):
        self.board_state = measure(self.board_state, target)

    def board_summary(self) -> dict[str, Optional[str]]:
        summary = {}
        for idx in range(64):
            square = square_name(idx)
            try:
                summary[square] = self.piece_at(square)
            except ValueError:
                summary[square] = None
        return summary
