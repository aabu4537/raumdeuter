# Raumdeuter · The Off-Ball Engine

**Live demo: [raumdeuter.vercel.app](https://raumdeuter.vercel.app)** · Built mid-tournament during the 2026 World Cup knockout stage.

*Raumdeuter* is German for "space interpreter", the role Thomas Müller invented for himself: a player
whose value lives in movement the box score never records. This app asks one question about the 2026
World Cup: **if you price that invisible work (pressing, regains, runs that drag defenders out of
shape), who actually wins?**

The α dial is that price. At α = 0 the model sees only on-ball production. At α = 1 it prices
players almost entirely on what they do without the ball. Every swap, every dial move re-solves the
entire remaining tournament instantly.

## How the model works

1. **Player vectors.** Every player carries an on-ball vector (finishing, chance creation,
   progression) and an off-ball vector on a StatsBomb-style schema (pressures P90, pressure
   regains, space interpretation, defensive coverage).
2. **α blend, per player.** `v = (1 − α)·on + α·off` is applied *before* aggregation, so α
   reprices individuals, not just teams. That is why a Kane-for-Watkins swap hurts England at
   α = 0 and helps them at α = 0.8 (there is a property test asserting exactly that sign flip).
3. **Team strengths.** XI vectors aggregate with positional weights into attack and defence,
   mapped to goal expectations `λ = exp(ln 1.35 + (Atk − Def)/12)`.
4. **Match engine.** A Dixon-Coles adjusted double Poisson (ρ = −0.10) produces the full
   scoreline grid; knockout draws resolve by a strength-tilted coin flip (max ±8%).
5. **Bracket.** Champion odds propagate **analytically** through the real remaining bracket via
   the law of total probability. Zero simulations; every number is exact given the model and
   reproducible to the digit.

## Repo layout

```
src/model/engine.js    pure prediction engine (no React, no DOM)
src/model/heatmap.js   procedural archetype-driven pressing maps
src/data/teams.js      squads verified against confirmed team sheets (Jul 6, 2026)
src/components/        pitch, scout cards, charts, simulator
tests/engine.test.js   property tests (probability sums, DC correction, α semantics)
pipeline/              ratings-computation scaffold (StatsBomb → PostgreSQL → ratings.json)
PREDICTIONS.md         frozen pre-quarterfinal predictions + track record
```

## Running it

```bash
npm install
npm run dev      # local dev server
npm test         # 11 property tests on the pure engine
npm run build    # production build (deployed to Vercel)
```

## Honest limitations

- **Ratings are curated analyst estimates**, not computed from event data. The schema mirrors the
  real pipeline this fronts (StatsBombPy → PostgreSQL → features), and `pipeline/` documents the
  intended computation, but the numbers themselves are subjective. Argue with them; that is the point.
- The draw-to-penalties resolution is a tilted coin flip; it ignores extra-time dynamics,
  fatigue, and shootout-specific skill.
- No lineup priors: the model trusts whatever XI you set, with no minutes or fitness modeling.
- Home advantage is not modeled (defensible mid-tournament at neutral-ish venues, still a simplification).

## Prediction track record

See [PREDICTIONS.md](./PREDICTIONS.md): match-by-match probabilities and championship odds frozen
July 7, 2026, before the quarterfinals, scored after the final on July 19.
