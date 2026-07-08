import React from "react";

function Methodology({ onClose }){
  return (
    <div className="method" role="dialog" aria-label="Methodology">
      <div className="overlay" onClick={onClose}/>
      <div className="method-card" style={{zIndex:61}}>
        <button className="scout-x" onClick={onClose} aria-label="Close">✕</button>
        <h3 className="disp">Methodology</h3>
        <p style={{marginTop:6}}>Raumdeuter tests one question: <b style={{color:"var(--chalk)"}}>does valuing
        off-ball work change who you think wins the World Cup?</b></p>
        <h4 className="disp">Player vectors</h4>
        <p>Every player carries an on-ball vector (finishing, chance creation, progression) and an off-ball
        vector on a StatsBomb-style schema: <code>pressures P90</code>, <code>pressure regains</code>,
        <code>space interpretation</code>, <code>defensive coverage</code>. Ratings are curated analyst estimates,
        not live feeds; the schema mirrors the real pipeline (StatsBombPy → PostgreSQL → model) this prototype fronts.</p>
        <h4 className="disp">The α dial</h4>
        <p>α blends each player's two vectors before aggregation: <code>v = (1−α)·on + α·off</code>. At α=0 the
        model sees only on-ball production, the box-score view. At α=1 it prices players almost entirely on what
        they do without the ball. The default 0.35 approximates how possession-adjusted models weight defensive work.</p>
        <h4 className="disp">Match engine</h4>
        <p>XI vectors aggregate into team attack/defence with positional weights, then map to goal expectations
        <code> λ = exp(ln 1.35 + (Atk−Def)/12)</code>. Scorelines follow a Dixon-Coles adjusted double Poisson
        (ρ=−0.10 low-score correction). Knockout draws resolve by a strength-tilted coin flip (max ±8%).</p>
        <h4 className="disp">Bracket</h4>
        <p>Champion odds propagate analytically through the real remaining 2026 bracket, with no Monte Carlo noise.
        Every swap and every α move re-solves the entire tournament tree instantly.</p>
        <h4 className="disp">Honesty note</h4>
        <p>Fixtures and results verified July 6, 2026. Player ratings are subjective estimates built for
        methodological transparency. Argue with them; that's the point.</p>
      </div>
    </div>
  );
}

export default Methodology;
