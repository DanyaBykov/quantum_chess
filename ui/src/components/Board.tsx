import type { GameSnapshot } from "../api/types";

import "./Board.css";

const FILES = ["a", "b", "c", "d", "e", "f", "g", "h"];
const RANKS = ["8", "7", "6", "5", "4", "3", "2", "1"];
const PIECE_GLYPHS: Record<string, string> = {
  K: "♔",
  Q: "♕",
  R: "♖",
  B: "♗",
  N: "♘",
  P: "♙",
  k: "♚",
  q: "♛",
  r: "♜",
  b: "♝",
  n: "♞",
  p: "♟",
};

interface BoardProps {
  snapshot: GameSnapshot | null;
  selectedSquares: string[];
  onSelectSquare: (square: string) => void;
}

export function Board({ snapshot, selectedSquares, onSelectSquare }: BoardProps) {
  return (
    <div className="board" aria-label="Quantum chess board">
      {RANKS.flatMap((rank) =>
        FILES.map((file, fileIndex) => {
          const square = `${file}${rank}`;
          const piece = snapshot?.board[square] ?? null;
          const pieceGlyph = piece ? PIECE_GLYPHS[piece] ?? piece : "";
          const probability = snapshot?.probabilities[square] ?? 0;
          const isSelected = selectedSquares.includes(square);
          const isDark = (Number(rank) + fileIndex) % 2 === 0;

          return (
            <button
              key={square}
              type="button"
              className={[
                "square",
                isDark ? "square-dark" : "square-light",
                isSelected ? "square-selected" : "",
              ].join(" ")}
              onClick={() => onSelectSquare(square)}
              aria-label={`Square ${square}`}
            >
              <span className="square-piece">{pieceGlyph}</span>
              {probability > 0 && probability < 1 ? (
                <span className="square-probability">{Math.round(probability * 100)}%</span>
              ) : null}
              <span className="square-name">{square}</span>
            </button>
          );
        }),
      )}
    </div>
  );
}
