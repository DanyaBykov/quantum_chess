from typing import Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel


class GameSnapshot(BaseModel):
    board: Dict[str, Optional[str]]
    probabilities: Dict[str, float]
    side_to_move: Literal["white", "black"]
    fullmove_number: int
    game_status: Literal["ongoing", "white_wins", "black_wins"]
    legal_moves: List[Tuple[str, str]]
    last_move_outcome: Optional[Literal["success", "capture_failed"]] = None


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
