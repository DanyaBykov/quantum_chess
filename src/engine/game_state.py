from dataclasses import dataclass
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
        return max(abs_file, abs_rank) == 1

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
        diagonal_capture = (
            abs_file == 1
            and rank_delta == direction
            and (
                (target_piece is not None and _piece_color(target_piece) != _piece_color(piece))
                or allow_empty_target_for_pawn_diagonal
            )
        )
        return one_step or two_step or diagonal_capture

    return False


def validate_move_on_basis(
    basis: BasisState,
    src: str,
    target: str,
    *,
    allow_empty_target_for_pawn_diagonal: bool = False,
) -> str:
    src_idx = parse_square(src)
    tgt_idx = parse_square(target)
    piece = basis[src_idx]
    if piece is None:
        raise ValueError(f"no piece at source square {src}")

    if not _is_legal_piece_move(
        piece,
        src_idx,
        tgt_idx,
        basis,
        allow_empty_target_for_pawn_diagonal=allow_empty_target_for_pawn_diagonal,
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


@dataclass
class QuantumGame:
    board_state: BoardState
    side_to_move: str = "white"
    fullmove_number: int = 1

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

    def apply_classical_move(self, src: str, target: str):
        occupied_bases = list(_occupied_basis_states(self.board_state, src))
        if not occupied_bases:
            raise ValueError(f"no piece present at {src}")

        piece = self.board_state.occupied_piece(src)
        if piece is None:
            raise ValueError(f"no piece present at {src}")

        self._assert_side_to_move(piece)
        for basis in occupied_bases:
            validate_move_on_basis(basis, src, target)

        new_amplitudes = {}
        src_idx = parse_square(src)
        tgt_idx = parse_square(target)
        for basis, amplitude in self.board_state.amplitudes.items():
            if basis[src_idx] is None:
                new_amplitudes[basis] = amplitude
                continue

            moved_basis = list(basis)
            moved_basis[tgt_idx] = moved_basis[src_idx]
            moved_basis[src_idx] = None
            moved_basis = tuple(moved_basis)
            new_amplitudes[moved_basis] = new_amplitudes.get(moved_basis, 0j) + amplitude

        self.board_state = BoardState(
            amplitudes=new_amplitudes,
            entanglement_map=self.board_state.entanglement_map,
        )
        self.board_state.normalize()
        self._advance_turn()

    def apply_split_move(self, src: str, target_a: str, target_b: str):
        if target_a == target_b:
            raise ValueError("split move targets must differ")

        piece = _piece_for_quantum_source(self.board_state, src)
        self._assert_side_to_move(piece)

        occupied_bases = list(_occupied_basis_states(self.board_state, src))
        for basis in occupied_bases:
            validate_move_on_basis(
                basis,
                src,
                target_a,
                allow_empty_target_for_pawn_diagonal=False,
            )
            validate_move_on_basis(
                basis,
                src,
                target_b,
                allow_empty_target_for_pawn_diagonal=False,
            )

        self.board_state = split_move(self.board_state, src, target_a, target_b)
        self.board_state.normalize()
        self._advance_turn()

    def apply_merge_move(self, src_a: str, src_b: str, target: str):
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
                basis,
                src_a,
                target,
                allow_empty_target_for_pawn_diagonal=piece_a.lower() == "p",
            )
        for basis in occupied_b:
            validate_move_on_basis(
                basis,
                src_b,
                target,
                allow_empty_target_for_pawn_diagonal=piece_b.lower() == "p",
            )

        self.board_state = merge_move(self.board_state, src_a, src_b, target)
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
