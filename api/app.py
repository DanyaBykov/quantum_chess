from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fastapi import FastAPI, HTTPException

from api.schemas import (
    ClassicalMoveRequest,
    GameSnapshot,
    MeasureRequest,
    MergeMoveRequest,
    SplitMoveRequest,
)
from api.state_store import snapshot_game, store

app = FastAPI(title="Quantum Chess API")


def _handle_engine_error(exc: ValueError):
    raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/game", response_model=GameSnapshot)
def get_game() -> GameSnapshot:
    return snapshot_game(store.get_game())


@app.post("/game/reset", response_model=GameSnapshot)
def reset_game() -> GameSnapshot:
    return snapshot_game(store.reset())


@app.post("/game/move/classical", response_model=GameSnapshot)
def apply_classical_move(payload: ClassicalMoveRequest) -> GameSnapshot:
    game = store.get_game()
    try:
        game.apply_classical_move(payload.src, payload.target)
    except ValueError as exc:
        _handle_engine_error(exc)
    return snapshot_game(game)


@app.post("/game/move/split", response_model=GameSnapshot)
def apply_split_move(payload: SplitMoveRequest) -> GameSnapshot:
    game = store.get_game()
    try:
        game.apply_split_move(payload.src, payload.target_a, payload.target_b)
    except ValueError as exc:
        _handle_engine_error(exc)
    return snapshot_game(game)


@app.post("/game/move/merge", response_model=GameSnapshot)
def apply_merge_move(payload: MergeMoveRequest) -> GameSnapshot:
    game = store.get_game()
    try:
        game.apply_merge_move(payload.src_a, payload.src_b, payload.target)
    except ValueError as exc:
        _handle_engine_error(exc)
    return snapshot_game(game)


@app.post("/game/measure", response_model=GameSnapshot)
def measure_square(payload: MeasureRequest) -> GameSnapshot:
    game = store.get_game()
    try:
        game.measure_square(payload.target)
    except ValueError as exc:
        _handle_engine_error(exc)
    return snapshot_game(game)
