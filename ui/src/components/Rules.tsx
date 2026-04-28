export function Rules() {
  return (
    <div className="rules-content">
      <h2 className="rules-heading">How to play Quantum Chess</h2>

      <section className="rules-section">
        <h3 className="rules-subheading">Classical chess</h3>
        <p>Standard chess rules apply: pieces move as normal, the goal is checkmate. White moves first; fullmove number increments after Black moves.</p>
      </section>

      <section className="rules-section">
        <h3 className="rules-subheading">Quantum superposition</h3>
        <p>A piece can exist in a <em>superposition</em> — simultaneously occupying multiple squares with associated probability amplitudes. Each possible configuration of the board is called a <em>basis state</em>. The game tracks all basis states and their complex amplitudes at once.</p>
        <p>Squares with probability between 0 % and 100 % glow <span className="rules-cyan">cyan</span> — the intensity reflects how uncertain the piece's location is.</p>
      </section>

      <section className="rules-section">
        <h3 className="rules-subheading">Move types</h3>

        <div className="rules-move">
          <span className="rules-move-icon">→</span>
          <div>
            <strong>Classical move</strong> — move a piece from one square to another, exactly as in standard chess. Only legal in all basis states where the piece exists.
          </div>
        </div>

        <div className="rules-move">
          <span className="rules-move-icon">⇌</span>
          <div>
            <strong>Split move</strong> — select a source and two target squares. The piece enters superposition: it moves to <em>both</em> targets simultaneously with equal amplitude (√½ each), doubling the number of basis states. Pawns cannot split to the promotion rank.
          </div>
        </div>

        <div className="rules-move">
          <span className="rules-move-icon">⊕</span>
          <div>
            <strong>Merge move</strong> — select two source squares and one target. Branches where the piece is at either source are combined into the target via quantum interference. Both source squares must contain the same piece type.
          </div>
        </div>

        <div className="rules-move">
          <span className="rules-move-icon">◎</span>
          <div>
            <strong>Measure</strong> — collapse a square's quantum state. The square is observed: with probability equal to its current probability the piece is found there (branches where it isn't are discarded and renormalized), and with the complementary probability it is found absent. This is irreversible.
          </div>
        </div>
      </section>

      <section className="rules-section">
        <h3 className="rules-subheading">Check and legal moves</h3>
        <p>A king is in <span className="rules-red">check</span> if it is attacked in <em>any</em> basis state. A move is legal only if it is valid in every basis state where the moving piece exists, and does not leave the king in check in the resulting branches.</p>
        <p>Checkmate and stalemate are determined from the full quantum state: if the side to move has no legal move in any mode, the game ends.</p>
      </section>

      <section className="rules-section">
        <h3 className="rules-subheading">Promotion</h3>
        <p>When a pawn reaches the back rank via a classical move, the game pauses for promotion. Choose Queen, Rook, Bishop, or Knight. Split moves to the promotion rank are not allowed.</p>
      </section>

      <section className="rules-section">
        <h3 className="rules-subheading">Interface guide</h3>
        <ul className="rules-list">
          <li>Click a piece to select it. In <strong>Classical</strong> mode, legal target squares are highlighted with dots (empty) or rings (occupied).</li>
          <li>Click a second square to complete the selection, then press <strong>Execute</strong>.</li>
          <li>For <strong>Split</strong>, select source then two targets (3 clicks). For <strong>Merge</strong>, select two sources then one target (3 clicks). For <strong>Measure</strong>, select one square (1 click).</li>
          <li>Press <strong>✕</strong> to clear the current selection or <strong>Reset</strong> to start a new game.</li>
        </ul>
      </section>
    </div>
  );
}
