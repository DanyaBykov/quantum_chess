from typing import Dict, Literal, Optional

from pydantic import BaseModel


class GameSnapshot(BaseModel):
    board: Dict[str, Optional[str]]
    probabilities: Dict[str, float]
    side_to_move: Literal["white", "black"]
    fullmove_number: int


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
