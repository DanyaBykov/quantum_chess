import { useState } from "react";

import type { ActionMode } from "./api/types";
import { Board } from "./components/Board";
import { Controls } from "./components/Controls";
import { StatusPanel } from "./components/StatusPanel";
import { selectionCountForMode, useGame } from "./state/useGame";

function trimSelections(mode: ActionMode, current: string[], nextSquare: string): string[] {
  const requiredSelections = selectionCountForMode(mode);
  const withoutExisting = current.filter((square) => square !== nextSquare);
  const nextSelections = [...withoutExisting, nextSquare];
  return nextSelections.slice(-requiredSelections);
}

export default function App() {
  const [mode, setMode] = useState<ActionMode>("classical");
  const [selectedSquares, setSelectedSquares] = useState<string[]>([]);
  const { snapshot, loading, error, reset, execute } = useGame();

  function handleModeChange(nextMode: ActionMode) {
    setMode(nextMode);
    setSelectedSquares([]);
  }

  function handleSelectSquare(square: string) {
    setSelectedSquares((current) => trimSelections(mode, current, square));
  }

  async function handleExecute() {
    const ok = await execute(mode, selectedSquares);
    if (ok) {
      setSelectedSquares([]);
    }
  }

  async function handleReset() {
    await reset();
    setSelectedSquares([]);
  }

  return (
    <main className="app-shell">
      <section className="hero">
        <p className="eyebrow">Quantum Chess</p>
        <h1>Board Shell</h1>
        <p className="lede">
          A thin UI over the engine API for classical, split, merge, and measurement actions.
        </p>
      </section>

      <section className="workspace">
        <Board snapshot={snapshot} selectedSquares={selectedSquares} onSelectSquare={handleSelectSquare} />
        <div className="sidebar">
          <StatusPanel snapshot={snapshot} loading={loading} error={error} />
          <Controls
            mode={mode}
            selectedSquares={selectedSquares}
            loading={loading}
            onModeChange={handleModeChange}
            onClearSelection={() => setSelectedSquares([])}
            onExecute={handleExecute}
            onReset={handleReset}
          />
        </div>
      </section>
    </main>
  );
}
