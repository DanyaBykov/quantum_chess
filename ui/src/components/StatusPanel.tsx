import type { GameSnapshot } from "../api/types";

interface StatusPanelProps {
  snapshot: GameSnapshot | null;
  loading: boolean;
  error: string | null;
}

export function StatusPanel({ snapshot, loading, error }: StatusPanelProps) {
  const status = snapshot?.game_status ?? "ongoing";
  const inCheck = snapshot?.in_check ?? false;
  const legalCount = snapshot?.legal_moves?.length ?? 0;

  return (
    <section className="panel">
      <p className="panel-title">Game state</p>

      <div className="status-row">
        <span className="status-label">Status</span>
        <span className={["status-value", status !== "ongoing" ? "status-value-check" : "status-value-ok"].join(" ")}>
          {loading ? "sync…" : status}
        </span>
      </div>

      <div className="status-row">
        <span className="status-label">Check</span>
        <span className={["status-value", inCheck ? "status-value-check" : ""].join(" ")}>
          {inCheck ? "YES" : "—"}
        </span>
      </div>

      <div className="status-row">
        <span className="status-label">Legal moves</span>
        <span className="status-value">{snapshot ? legalCount : "—"}</span>
      </div>

      {error ? (
        <div className="status-row" style={{ borderTop: "1px solid var(--border)", marginTop: "0.4rem" }}>
          <span style={{ fontSize: "0.72rem", color: "var(--red)", fontFamily: "var(--font-mono)" }}>
            {error}
          </span>
        </div>
      ) : null}
    </section>
  );
}
