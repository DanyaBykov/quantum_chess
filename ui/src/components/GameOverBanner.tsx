import type { GameStatus } from "../api/types";

interface GameOverBannerProps {
  status: "white_wins" | "black_wins";
  onReset: () => void;
}

export function GameOverBanner({ status, onReset }: GameOverBannerProps) {
  const headline = status === "white_wins" ? "White wins" : "Black wins";
  const sub = "The king has been captured";

  return (
    <div className="overlay" role="dialog" aria-modal="true" aria-label="Game over">
      <div className="overlay-card">
        <div>
          <p className="overlay-headline">{headline}</p>
          <p className="overlay-sub">{sub}</p>
        </div>
        <button type="button" className="btn-primary" style={{ width: "100%", fontSize: "0.9rem" }} onClick={onReset}>
          New game
        </button>
      </div>
    </div>
  );
}
