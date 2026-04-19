import { useEffect, useState } from "react";

import { gameClient } from "../api/client";
import type { ActionMode, GameSnapshot } from "../api/types";

async function runAction(mode: ActionMode, selections: string[]): Promise<GameSnapshot> {
  if (mode === "classical") {
    const [src, target] = selections;
    return gameClient.classicalMove({ src, target });
  }

  if (mode === "split") {
    const [src, target_a, target_b] = selections;
    return gameClient.splitMove({ src, target_a, target_b });
  }

  if (mode === "merge") {
    const [src_a, src_b, target] = selections;
    return gameClient.mergeMove({ src_a, src_b, target });
  }

  const [target] = selections;
  return gameClient.measureSquare({ target });
}

export function selectionCountForMode(mode: ActionMode): number {
  if (mode === "measure") {
    return 1;
  }
  if (mode === "classical") {
    return 2;
  }
  return 3;
}

export function modeLabel(mode: ActionMode): string {
  if (mode === "classical") {
    return "Classical move";
  }
  if (mode === "split") {
    return "Split move";
  }
  if (mode === "merge") {
    return "Merge move";
  }
  return "Measure square";
}

export function useGame() {
  const [snapshot, setSnapshot] = useState<GameSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const nextSnapshot = await gameClient.getGame();
        if (active) {
          setSnapshot(nextSnapshot);
          setError(null);
        }
      } catch (nextError) {
        if (active) {
          setError(nextError instanceof Error ? nextError.message : "Failed to load game");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, []);

  async function reset() {
    setLoading(true);
    try {
      const nextSnapshot = await gameClient.resetGame();
      setSnapshot(nextSnapshot);
      setError(null);
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Failed to reset game");
    } finally {
      setLoading(false);
    }
  }

  async function execute(mode: ActionMode, selections: string[]) {
    setLoading(true);
    try {
      const nextSnapshot = await runAction(mode, selections);
      setSnapshot(nextSnapshot);
      setError(null);
      return true;
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Action failed");
      return false;
    } finally {
      setLoading(false);
    }
  }

  return {
    snapshot,
    loading,
    error,
    reset,
    execute,
  };
}
