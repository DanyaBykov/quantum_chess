import type { GameSnapshot } from "../api/types";

import "./Board.css";

const FILES = ["a", "b", "c", "d", "e", "f", "g", "h"];
const RANKS = ["8", "7", "6", "5", "4", "3", "2", "1"];

const PIECE_GLYPHS: Record<string, string> = {
  K: "♔", Q: "♕", R: "♖", B: "♗", N: "♘", P: "♙",
  k: "♚", q: "♛", r: "♜", b: "♝", n: "♞", p: "♟",
};

interface BoardProps {
  snapshot: GameSnapshot | null;
  sourceSquares: string[];
  legalTargets: string[];
  onSelectSquare: (square: string) => void;
}

export function Board({ snapshot, sourceSquares, legalTargets, onSelectSquare }: BoardProps) {
  const sideToMove = snapshot?.side_to_move ?? "white";

  return (
    <div className="board-wrap">
      <div className="board-ranks" aria-hidden="true">
        {RANKS.map((rank) => (
          <span key={rank} className="board-rank-label">{rank}</span>
        ))}
      </div>

      <div className="board" aria-label="Quantum chess board">
        {RANKS.flatMap((rank) =>
          FILES.map((file, fileIdx) => {
            const square = `${file}${rank}`;
            const piece = snapshot?.board[square] ?? null;
            const probability = snapshot?.probabilities[square] ?? 0;
            const isSelected = sourceSquares.includes(square);
            const isLegalTarget = legalTargets.includes(square);
            const isDark = (Number(rank) + fileIdx) % 2 === 0;
            const heatOpacity =
              probability > 0 && probability < 1
                ? (Math.min(probability, 1 - probability) * 0.8).toFixed(3)
                : "0";

            const isFriendly = piece !== null && (
              sideToMove === "white" ? piece === piece.toUpperCase() : piece === piece.toLowerCase()
            );
            // A square is interactive if it's a friendly piece (potential source)
            // or a highlighted legal destination. Everything else is inert.
            const isInteractive = isFriendly || isLegalTarget;

            return (
              <button
                key={square}
                type="button"
                className={[
                  "square",
                  isDark ? "square-dark" : "square-light",
                  isSelected ? "square-selected" : "",
                  !piece && probability > 0 ? "square-ghost" : "",
                  !isInteractive ? "square-inert" : "",
                ].join(" ")}
                style={{ "--heat-opacity": heatOpacity } as React.CSSProperties}
                onClick={() => onSelectSquare(square)}
                aria-label={`Square ${square}`}
                title={!piece && probability > 0 ? `Superposition: ${Math.round(probability * 100)}% chance of a piece here — use ◎ Measure to resolve` : undefined}
              >
                <div className="square-heat" />
                {isLegalTarget && (piece ? <div className="sq-legal-ring" /> : <div className="sq-legal-dot" />)}
                <span className="square-piece">
                  {piece ? (PIECE_GLYPHS[piece] ?? piece) : (probability > 0 ? "⚛" : "")}
                </span>
                {probability > 0 && probability < 1 ? (
                  <span className="square-prob">{Math.round(probability * 100)}%</span>
                ) : null}
              </button>
            );
          }),
        )}
      </div>

      <div className="board-files" aria-hidden="true">
        {FILES.map((file) => (
          <span key={file} className="board-file-label">{file}</span>
        ))}
      </div>
    </div>
  );
}
