import { useState } from "react";

import type { ActionMode, GameSnapshot } from "./api/types";
import { Board } from "./components/Board";
import { Controls } from "./components/Controls";
import { GameOverBanner } from "./components/GameOverBanner";
import { PromotionDialog } from "./components/PromotionDialog";
import { Rules } from "./components/Rules";
import { StatusPanel } from "./components/StatusPanel";
import { selectionCountForMode, useGame } from "./state/useGame";

type Tab = "game" | "rules";

function trimSelections(mode: ActionMode, current: string[], next: string): string[] {
  const required = selectionCountForMode(mode);
  return [...current.filter((sq) => sq !== next), next].slice(-required);
}

function findKingSquare(board: Record<string, string | null>, side: string): string | null {
  const king = side === "white" ? "K" : "k";
  return Object.keys(board).find((sq) => board[sq] === king) ?? null;
}

function isFriendlyPiece(piece: string | null | undefined, sideToMove: string): boolean {
  if (!piece) return false;
  return sideToMove === "white" ? piece === piece.toUpperCase() : piece === piece.toLowerCase();
}

function computeLegalTargets(mode: ActionMode, selected: string[], snapshot: GameSnapshot | null): string[] {
  if (!snapshot?.legal_moves || !snapshot.board) return [];

  const board = snapshot.board;
  const legalMoves = snapshot.legal_moves;

  if (mode === "classical") {
    if (selected.length === 0) return [];
    return legalMoves.filter(([src]) => src === selected[0]).map(([, tgt]) => tgt);
  }

  if (mode === "split") {
    if (selected.length === 0) return [];
    // Valid destinations for the split source (same move rules as classical)
    const targets = legalMoves.filter(([src]) => src === selected[0]).map(([, tgt]) => tgt);
    // Once first target is picked, exclude it from second-target highlights
    return selected.length >= 2 ? targets.filter((sq) => sq !== selected[1]) : targets;
  }

  if (mode === "merge") {
    if (selected.length === 0) return [];

    if (selected.length === 1) {
      // Show squares that hold the same piece type (potential merge partners)
      const srcPiece = board[selected[0]];
      if (!srcPiece) return [];
      return Object.entries(board)
        .filter(([sq, piece]) => piece === srcPiece && sq !== selected[0])
        .map(([sq]) => sq);
    }

    // Two sources selected — show legal destinations (union of each source's moves)
    const [srcA, srcB] = selected;
    const setA = new Set(legalMoves.filter(([src]) => src === srcA).map(([, tgt]) => tgt));
    const setB = new Set(legalMoves.filter(([src]) => src === srcB).map(([, tgt]) => tgt));
    return [...new Set([...setA, ...setB])];
  }

  return [];
}

export default function App() {
  const [tab, setTab] = useState<Tab>("game");
  const [mode, setMode] = useState<ActionMode>("classical");
  const [selected, setSelected] = useState<string[]>([]);
  const { snapshot, loading, error, reset, execute, promote } = useGame();

  const promotionPending = snapshot?.promotion_pending ?? false;
  const gameStatus = snapshot?.game_status ?? "ongoing";
  const gameOver = gameStatus !== "ongoing";

  const inCheckSquare =
    snapshot?.in_check && snapshot.board && snapshot.side_to_move
      ? findKingSquare(snapshot.board, snapshot.side_to_move)
      : null;

  const legalTargets = computeLegalTargets(mode, selected, snapshot);

  function handleModeChange(next: ActionMode) {
    setMode(next);
    setSelected([]);
  }

  function handleSelectSquare(sq: string) {
    if (promotionPending || gameOver) return;

    const board = snapshot?.board;
    const side = snapshot?.side_to_move ?? "white";
    const piece = board?.[sq] ?? null;
    const friendly = isFriendlyPiece(piece, side);

    if (mode === "classical" || mode === "split") {
      if (friendly) {
        // Clicking the already-selected source deselects it
        if (selected[0] === sq) {
          setSelected([]);
          return;
        }
        setSelected([sq]);
        return;
      }
      setSelected((cur) => trimSelections(mode, cur, sq));
      return;
    }

    if (mode === "merge") {
      if (selected.length === 0) {
        if (friendly) setSelected([sq]);
        return;
      }
      if (selected.length === 1) {
        // Clicking the already-selected source deselects it
        if (sq === selected[0]) {
          setSelected([]);
          return;
        }
        const srcPiece = board?.[selected[0]];
        if (friendly && piece === srcPiece) {
          setSelected([selected[0], sq]);
          return;
        }
        if (friendly) {
          setSelected([sq]);
          return;
        }
        return;
      }
      if (selected.length === 2) {
        // Clicking either source removes it from the pair
        if (sq === selected[0]) { setSelected([selected[1]]); return; }
        if (sq === selected[1]) { setSelected([selected[0]]); return; }
        if (friendly) { setSelected([sq]); return; }
        setSelected([selected[0], selected[1], sq]);
        return;
      }
    }

    if (mode === "measure") {
      setSelected([sq]);
      return;
    }

    setSelected((cur) => trimSelections(mode, cur, sq));
  }

  async function handleExecute() {
    const ok = await execute(mode, selected);
    if (ok) setSelected([]);
  }

  async function handleReset() {
    await reset();
    setSelected([]);
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <h1 className="topbar-title">Quantum Chess</h1>

        <nav className="tab-nav" aria-label="Main tabs">
          <button
            type="button"
            className={`tab-btn ${tab === "game" ? "tab-btn-active" : ""}`}
            onClick={() => setTab("game")}
          >
            Game
          </button>
          <button
            type="button"
            className={`tab-btn ${tab === "rules" ? "tab-btn-active" : ""}`}
            onClick={() => setTab("rules")}
          >
            Rules
          </button>
        </nav>

        {tab === "game" && snapshot ? (
          <div className="topbar-status">
            <span className={`side-pip side-pip-${snapshot.side_to_move}`} />
            <span>{snapshot.side_to_move} to move</span>
            {snapshot.in_check ? <span className="topbar-check">· check</span> : null}
          </div>
        ) : null}

        {error ? <span role="alert" className="topbar-error">{error}</span> : null}

        {tab === "game" ? (
          <span className="topbar-move">move {snapshot?.fullmove_number ?? 1}</span>
        ) : null}
      </header>

      {tab === "game" ? (
        <div className="workspace">
          <div className="board-section">
            <Board
              snapshot={snapshot}
              selectedSquares={selected}
              legalTargets={legalTargets}
              inCheckSquare={inCheckSquare}
              onSelectSquare={handleSelectSquare}
            />
          </div>
          <div className="sidebar">
            <StatusPanel snapshot={snapshot} loading={loading} error={null} />
            <Controls
              mode={mode}
              selectedSquares={selected}
              loading={loading}
              disabled={promotionPending || gameOver}
              onModeChange={handleModeChange}
              onClearSelection={() => setSelected([])}
              onExecute={handleExecute}
              onReset={handleReset}
            />
          </div>
        </div>
      ) : (
        <div className="rules-view">
          <Rules />
        </div>
      )}

      {promotionPending && snapshot ? (
        <PromotionDialog sideToMove={snapshot.side_to_move} onPromote={promote} />
      ) : null}

      {gameOver && snapshot ? (
        <GameOverBanner status={gameStatus} sideToMove={snapshot.side_to_move} onReset={handleReset} />
      ) : null}
    </div>
  );
}
