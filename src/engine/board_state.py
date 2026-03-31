import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional, Any
import chess

# A BasisState is a hashable representation of a single classical board configuration.
# We use a tuple of 64 strings (or None) corresponding to squares A1 through H8.
BasisState = Tuple[Optional[str], ...]

@dataclass
class BoardState:
    """
    Represents the quantum state of the chess board as a superposition of classical states.
    """
    # Maps a classical board configuration (basis state) to its complex probability amplitude
    # This tracks only reachable basis states instead of a full 2^64 state vector
    amplitudes: Dict[BasisState, complex] = field(default_factory=dict)
    
    # Tracks which pieces are correlated so collapse propagates correctly
    entanglement_map: Dict[str, set] = field(default_factory=dict)

    @classmethod
    def initial(cls) -> 'BoardState':
        """
        Creates the initial classical chess board state with a single basis state 
        having an amplitude of 1.0 + 0j.
        """
        board = chess.Board() # Using python-chess for standard starting position
        
        # Convert chess.Board to our hashable BasisState tuple
        initial_tuple = cls._board_to_tuple(board)
        
        # The game starts entirely classical: 100% probability in the starting position
        state = cls(amplitudes={initial_tuple: 1.0 + 0.0j})
        return state

    @staticmethod
    def _board_to_tuple(board: chess.Board) -> BasisState:
        """Helper to convert a python-chess board into a 64-element tuple."""
        squares = []
        for square in chess.SQUARES: # 0 to 63
            piece = board.piece_at(square)
            squares.append(piece.symbol() if piece else None)
        return tuple(squares)

    def amplitude(self, square_name: str) -> complex:
        """
        Calculates the total amplitude of ANY piece existing on a given square 
        across all superposed basis states.
        
        Note: To get the actual probability, the caller should compute 
        abs(state.amplitude(sq))**2.
        """
        square_index = chess.parse_square(square_name)
        total_amplitude = 0.0 + 0.0j
        
        for basis_state, amp in self.amplitudes.items():
            if basis_state[square_index] is not None:
                total_amplitude += amp
                
        return total_amplitude
        
    def probability(self, square_name: str) -> float:
        """Returns the classical probability (amplitude squared) of a square being occupied."""
        amp = self.amplitude(square_name)
        return abs(amp)**2

    def prune_states(self, threshold: float = 0.001):
        """
        Prunes basis states with probability (amplitude^2) < threshold to prevent 
        state explosion.
        """
        states_to_remove = []
        for basis_state, amp in self.amplitudes.items():
            prob = abs(amp)**2
            if prob < threshold:
                states_to_remove.append(basis_state)
                
        for state in states_to_remove:
            del self.amplitudes[state]
            
        self.normalize()

    def normalize(self):
        """
        Ensures the sum of all probabilities (abs(amplitude)**2) across all 
        basis states equals exactly 1.0.
        """
        total_prob = sum(abs(amp)**2 for amp in self.amplitudes.values())
        if total_prob == 0:
            return
            
        # Scale amplitudes so their squared absolute values sum to 1
        scale_factor = np.sqrt(1.0 / total_prob)
        for basis_state in self.amplitudes:
            self.amplitudes[basis_state] *= scale_factor