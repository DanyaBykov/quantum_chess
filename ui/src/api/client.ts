import type {
  ClassicalMovePayload,
  GameSnapshot,
  MeasurePayload,
  MergeMovePayload,
  SplitMovePayload,
} from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `Request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

export const gameClient = {
  getGame(): Promise<GameSnapshot> {
    return request<GameSnapshot>("/game");
  },

  resetGame(): Promise<GameSnapshot> {
    return request<GameSnapshot>("/game/reset", { method: "POST" });
  },

  classicalMove(payload: ClassicalMovePayload): Promise<GameSnapshot> {
    return request<GameSnapshot>("/game/move/classical", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  splitMove(payload: SplitMovePayload): Promise<GameSnapshot> {
    return request<GameSnapshot>("/game/move/split", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  mergeMove(payload: MergeMovePayload): Promise<GameSnapshot> {
    return request<GameSnapshot>("/game/move/merge", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  measureSquare(payload: MeasurePayload): Promise<GameSnapshot> {
    return request<GameSnapshot>("/game/measure", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};
