import type { SideToMove } from "../api/types";

const WHITE_PIECES = ["Q", "R", "B", "N"] as const;
const BLACK_PIECES = ["q", "r", "b", "n"] as const;
const GLYPHS: Record<string, string> = {
  Q: "♕", R: "♖", B: "♗", N: "♘",
  q: "♛", r: "♜", b: "♝", n: "♞",
};

interface PromotionDialogProps {
  sideToMove: SideToMove;
  onPromote: (piece: string) => void;
}

export function PromotionDialog({ sideToMove, onPromote }: PromotionDialogProps) {
  const pieces = sideToMove === "white" ? WHITE_PIECES : BLACK_PIECES;

  return (
    <div className="overlay" role="dialog" aria-modal="true" aria-label="Promote pawn">
      <div className="overlay-card">
        <div>
          <p className="overlay-headline">Promote pawn</p>
          <p className="overlay-sub">Choose a piece</p>
        </div>
        <div className="promotion-choices">
          {pieces.map((piece) => (
            <button
              key={piece}
              type="button"
              className="promotion-piece-btn"
              aria-label={piece}
              onClick={() => onPromote(piece)}
            >
              {GLYPHS[piece]}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
