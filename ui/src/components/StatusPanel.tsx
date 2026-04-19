import type { GameSnapshot } from "../api/types";

interface StatusPanelProps {
  snapshot: GameSnapshot | null;
  loading: boolean;
  error: string | null;
}

export function StatusPanel({ snapshot, loading, error }: StatusPanelProps) {
  return (
    <section className="panel">
      <h2>Status</h2>
      <p>Side to move: {snapshot?.side_to_move ?? "loading"}</p>
      <p>Fullmove: {snapshot?.fullmove_number ?? "-"}</p>
      <p>{loading ? "Synchronizing game state..." : "Ready"}</p>
      {error ? (
        <p role="alert" className="error-text">
          {error}
        </p>
      ) : null}
    </section>
  );
}
