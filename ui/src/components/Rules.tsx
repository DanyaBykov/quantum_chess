export function Rules() {
  return (
    <div className="rules-content">
      <h2 className="rules-heading">How to play Quantum Chess</h2>

      <section className="rules-section">
        <h3 className="rules-subheading">Core idea</h3>
        <p>Pieces can be in superposition, so one piece may occupy multiple squares with different probabilities. The board is represented as many classical positions (basis states) with amplitudes.</p>
      </section>

      <section className="rules-section">
        <h3 className="rules-subheading">Move types</h3>
        <p><strong>Classical move</strong>: normal chess move rules, including captures.</p>
        <p><strong>Split move</strong>: one piece moves to two legal, non-capturing targets at once. Targets must be empty.</p>
        <p><strong>Merge move</strong>: two copies of the same piece move to one common legal target. Merge is non-capturing and target must be empty.</p>
      </section>

      <section className="rules-section">
        <h3 className="rules-subheading">Captures and observation</h3>
        <p>Captures by pieces in superposition may trigger observation (collapse) to determine whether the piece is present on its starting square.</p>
        <p>For pawn captures (including en passant), both sides involved may be observed; failed observations can make the capture fail and still pass the turn.</p>
        <p>Squares with probability between 0 % and 100 % glow <span className="rules-cyan">cyan</span> — the intensity reflects how uncertain the piece's location is.</p>
      </section>

      <section className="rules-section">
        <h3 className="rules-subheading">Win condition and special rules</h3>
        <p>There is no check/checkmate constraint. The game ends when one side has no king copies left on the board.</p>
        <p>Castling and en passant are supported. Castling does not require check-related validation in this variant.</p>
      </section>

      <section className="rules-section">
        <h3 className="rules-subheading">Promotion</h3>
        <p>Pawns promote automatically to queens on the back rank. Split moves to promotion rank are not allowed.</p>
        <p>A promoted queen keeps all entanglements the pawn had. However, she cannot merge with copies of the original pawn that are still pawns — once promoted she is a queen, not a pawn sibling. If both copies of a split pawn promote to queens, those queens can merge with each other, since they are still copies of the same original piece.</p>
      </section>

      <section className="rules-section">
        <h3 className="rules-subheading">Interface guide</h3>
        <ul className="rules-list">
          <li>Click a piece to select it. In <strong>Classical</strong> mode, legal target squares are highlighted with dots (empty) or rings (occupied).</li>
          <li>Click a second square to complete the selection, then press <strong>Execute</strong>.</li>
          <li>For <strong>Split</strong>, select source then two targets (3 clicks). For <strong>Merge</strong>, select two sources then one target (3 clicks).</li>
          <li>Press <strong>✕</strong> to clear the current selection or <strong>Reset</strong> to start a new game.</li>
        </ul>
      </section>
    </div>
  );
}
