from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
UI_DIST = ROOT / "ui" / "dist"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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


if UI_DIST.exists():
    assets_dir = UI_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


@app.get("/")
def serve_index():
    if not UI_DIST.exists():
        raise HTTPException(status_code=404, detail="UI bundle not found")
    return FileResponse(UI_DIST / "index.html")


@app.get("/{path:path}")
def serve_spa(path: str):
    if path.startswith("game"):
        raise HTTPException(status_code=404, detail="Not found")
    if not UI_DIST.exists():
        raise HTTPException(status_code=404, detail="UI bundle not found")

    target = UI_DIST / path
    if path and target.exists() and target.is_file():
        return FileResponse(target)

    return FileResponse(UI_DIST / "index.html")
