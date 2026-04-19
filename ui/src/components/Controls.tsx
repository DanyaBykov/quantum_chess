import type { ActionMode } from "../api/types";

import { modeLabel, selectionCountForMode } from "../state/useGame";

interface ControlsProps {
  mode: ActionMode;
  selectedSquares: string[];
  loading: boolean;
  onModeChange: (mode: ActionMode) => void;
  onClearSelection: () => void;
  onExecute: () => void;
  onReset: () => void;
}

const MODES: ActionMode[] = ["classical", "split", "merge", "measure"];

export function Controls({
  mode,
  selectedSquares,
  loading,
  onModeChange,
  onClearSelection,
  onExecute,
  onReset,
}: ControlsProps) {
  const requiredSelections = selectionCountForMode(mode);

  return (
    <section className="panel">
      <h2>Actions</h2>
      <div className="mode-list">
        {MODES.map((entry) => (
          <label key={entry} className="mode-option">
            <input
              type="radio"
              name="mode"
              value={entry}
              checked={mode === entry}
              onChange={() => onModeChange(entry)}
            />
            <span>{modeLabel(entry)}</span>
          </label>
        ))}
      </div>
      <p className="selection-hint">
        Selected {selectedSquares.length}/{requiredSelections}:{" "}
        {selectedSquares.length ? selectedSquares.join(" -> ") : "none"}
      </p>
      <div className="button-row">
        <button type="button" onClick={onExecute} disabled={loading || selectedSquares.length !== requiredSelections}>
          Execute
        </button>
        <button type="button" onClick={onClearSelection} disabled={loading || selectedSquares.length === 0}>
          Clear
        </button>
        <button type="button" onClick={onReset} disabled={loading}>
          Reset
        </button>
      </div>
    </section>
  );
}
