from threading import Lock

from engine.board_state import square_name
from engine.game_state import QuantumGame

from api.schemas import GameSnapshot


class GameStateStore:
    def __init__(self):
        self._lock = Lock()
        self._game = QuantumGame.initial()

    def get_game(self) -> QuantumGame:
        with self._lock:
            return self._game

    def reset(self) -> QuantumGame:
        with self._lock:
            self._game = QuantumGame.initial()
            return self._game


store = GameStateStore()


def snapshot_game(game: QuantumGame) -> GameSnapshot:
    board = game.board_summary()
    probabilities = {
        square_name(index): game.board_state.probability(square_name(index))
        for index in range(64)
    }
    return GameSnapshot(
        board=board,
        probabilities=probabilities,
        side_to_move=game.side_to_move,
        fullmove_number=game.fullmove_number,
    )
