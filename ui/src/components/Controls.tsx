import type { ActionMode } from "../api/types";
import { selectionCountForMode } from "../state/useGame";

interface ControlsProps {
  mode: ActionMode;
  selectedSquares: string[];
  loading: boolean;
  disabled: boolean;
  onModeChange: (mode: ActionMode) => void;
  onClearSelection: () => void;
  onExecute: () => void;
  onReset: () => void;
}

const MODES: { id: ActionMode; icon: string; label: string }[] = [
  { id: "classical", icon: "→", label: "Classical" },
  { id: "split",     icon: "⇌", label: "Split" },
  { id: "merge",     icon: "⊕", label: "Merge" },
];

export function Controls({ mode, selectedSquares, loading, disabled, onModeChange, onClearSelection, onExecute, onReset }: ControlsProps) {
  const required = selectionCountForMode(mode);
  const ready = selectedSquares.length === required;
  const squaresDisplay = selectedSquares.length ? selectedSquares.join(" → ") : "none";

  return (
    <section className="panel">
      <p className="panel-title">Move type</p>
      <div className="mode-grid">
        {MODES.map(({ id, icon, label }) => (
          <button
            key={id}
            type="button"
            className={["mode-btn", mode === id ? "mode-btn-active" : ""].join(" ")}
            onClick={() => onModeChange(id)}
            disabled={disabled}
          >
            <span className="mode-btn-icon">{icon}</span>
            <span className="mode-btn-label">{label}</span>
          </button>
        ))}
      </div>

      <div className="selection-display">
        {selectedSquares.length > 0 ? (
          <>
            <span className="selection-squares">{squaresDisplay}</span>
            {" "}
            <span style={{ color: "var(--text-muted)" }}>({selectedSquares.length}/{required})</span>
          </>
        ) : (
          <span>select {required} square{required > 1 ? "s" : ""}</span>
        )}
      </div>

      <div className="action-row">
        <button
          type="button"
          className="btn-primary"
          onClick={onExecute}
          disabled={disabled || loading || !ready}
        >
          Execute
        </button>
        <button
          type="button"
          className="btn-secondary"
          onClick={onClearSelection}
          disabled={disabled || loading || selectedSquares.length === 0}
        >
          ✕
        </button>
        <button
          type="button"
          className="btn-secondary"
          onClick={onReset}
          disabled={loading}
        >
          Reset
        </button>
      </div>
    </section>
  );
}
