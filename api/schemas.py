from typing import Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel


class GameSnapshot(BaseModel):
    board: Dict[str, Optional[str]]
    probabilities: Dict[str, float]
    side_to_move: Literal["white", "black"]
    fullmove_number: int
    in_check: bool
    game_status: Literal["ongoing", "checkmate", "stalemate"]
    promotion_pending: bool
    promotion_square: Optional[str]
    legal_moves: List[Tuple[str, str]]


class ClassicalMoveRequest(BaseModel):
    src: str
    target: str


class SplitMoveRequest(BaseModel):
    src: str
    target_a: str
    target_b: str


class MergeMoveRequest(BaseModel):
    src_a: str
    src_b: str
    target: str


class MeasureRequest(BaseModel):
    target: str


class PromoteRequest(BaseModel):
    piece: str
