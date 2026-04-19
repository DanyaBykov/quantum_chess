export type SideToMove = "white" | "black";
export type ActionMode = "classical" | "split" | "merge" | "measure";

export interface GameSnapshot {
  board: Record<string, string | null>;
  probabilities: Record<string, number>;
  side_to_move: SideToMove;
  fullmove_number: number;
}

export interface ClassicalMovePayload {
  src: string;
  target: string;
}

export interface SplitMovePayload {
  src: string;
  target_a: string;
  target_b: string;
}

export interface MergeMovePayload {
  src_a: string;
  src_b: string;
  target: string;
}

export interface MeasurePayload {
  target: string;
}
