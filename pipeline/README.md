# Ratings Pipeline (scaffold)

The app currently ships curated ratings in `src/data/teams.js`. This directory documents how those
numbers are intended to be computed from real event data, reusing the existing platform stack
(StatsBombPy → PostgreSQL → FastAPI).

```
StatsBomb events ──► per-player aggregates ──► league-position percentiles ──► ratings.json ──► frontend
      (statsbombpy)        (compute_ratings.py)         (possession-adjusted)
```

## Stat mapping

| App stat | Source computation |
|---|---|
| `fin` | np-xG per shot + shot volume P90, percentile vs position |
| `cre` | xA + key passes P90 |
| `prg` | progressive carries + progressive passes P90 |
| `prs` | pressures P90, possession-adjusted |
| `rgn` | pressure regains + counterpressure regains P90 |
| `mov` | off-ball receptions in zone 14 / box + run-derived xG chain share |
| `cov` | defensive actions P90 × positioning discipline proxy |

`compute_ratings.py` is a documented stub showing the aggregation shape;
`ratings.schema.json` defines the contract the frontend consumes.
