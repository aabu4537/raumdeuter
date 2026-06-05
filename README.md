# Raumdeuter

> *Raumdeuter* (German): "space interpreter" — a footballer who reads and exploits space before others see it. Named after the analytical style of players like Thomas Müller; this platform tries to find the spaces in football data that conventional analysis misses.

A production-grade football analytics platform for predicting FIFA World Cup outcomes, with a focus on testing unconventional hypotheses about what truly drives tournament success.

---

## What it does

Most World Cup prediction models lean on FIFA rankings or Elo ratings and call it done. Raumdeuter goes further: it models the intangibles — climate adaptation, tournament resilience, pressure performance, squad cohesion under chaos — and runs Monte Carlo simulations to quantify how much (if at all) those factors lift predictive accuracy over a pure Elo baseline.

The core research question: **do the intangibles actually matter, or are they noise?**

---

## Project structure

```
Raumdeuter/
├── src/
│   ├── team.py                  # Team + Tournament dataclasses (Elo, climate, geo)
│   ├── research_modules.py      # Abstract ResearchModule base + 10 concrete modules + ModuleCompositor
│   ├── match_simulator.py       # MatchResult dataclass + MatchSimulator (Dixon-Coles model)
│   ├── tournament_simulator.py  # TournamentSimulator: group stage + knockout Monte Carlo
│   └── main.py                  # Demo runners + 32-team WC 2026 field
├── data/                        # Historical match data, team stats (populated separately)
├── notebooks/                   # EDA and research notebooks
├── tests/
├── requirements.txt
└── README.md
```

---

## Quickstart

**Prerequisites:** Python 3.9+

```bash
# Clone and set up environment
git clone https://github.com/aabu4537/raumdeuter.git
cd Raumdeuter
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run the demo
python src/main.py
```

Example output:
```
=== Head-to-Head: Argentina vs France (10,000 match simulations) ===

  Argentina win : 50.7%
  Draw          : 16.6%
  France win    : 32.8%

=== Module Score Breakdown: Top 4 Teams ===

  Module                           Argentina        France       England        Brazil
  ------------------------------------------------------------------------------------
  climate_adaptation                    34.0          27.3          23.6          49.4
  tournament_resilience                 65.0          65.7          44.7          49.9
  tournament_dna                        64.0          60.0          54.0          48.0
  leadership_stability                 100.0          77.5          67.9          50.4
  squad_fatigue                         49.3          48.7          50.0          36.0
  injury_impact                        100.0          92.0         100.0         100.0

  Composite scores:
    Argentina        58.9
    France           53.0
    England          48.6
    Brazil           47.7

=== Elo-only vs Module-adjusted Win Probability (Argentina vs Brazil) ===

  Elo-only P(Argentina wins): 65.3%
  Module-adjusted P(Argentina wins): 55.4%
  Delta: -9.9%
```

The -9.9% delta on the last line is the core research output: climate adaptation and squad fatigue drag Argentina's Elo-implied edge down significantly against a Brazil side more accustomed to South American conditions.

---

## How the simulation works

### Match model — Dixon-Coles bivariate Poisson

Each team's Elo is converted to a Poisson goal-rate parameter λ:

```
λ = exp((Elo - 1800) / 500) × 1.25
```

If research module scores are enabled, λ is adjusted by a weighted composite:

```
λ_adjusted = λ × (1 + (module_avg - 0.5) × module_weight)
```

Goals are sampled from the joint distribution with the Dixon-Coles correction applied to low-scoring results (0-0, 1-0, 0-1, 1-1), which standard Poisson underestimates in football. Knockout draws go to extra time (30% rate) and then penalties (50/50).

Implemented in [src/match_simulator.py](src/match_simulator.py) as the `MatchSimulator` class.

### Monte Carlo tournament simulation

Runs the full 32-team, 64-match World Cup bracket `n` times. Each simulation:

1. Randomly draws 32 teams into 8 groups of 4
2. Simulates all 6 round-robin matches per group (points, goal difference, goals scored for tiebreaking)
3. Top 2 from each group advance — 16 qualifiers into the knockout bracket
4. Simulates R16 → QF → SF → Final with extra time and penalties

Aggregates champion/finalist/semifinalist counts across all runs to produce calibrated probabilities. The simulation is embarrassingly parallel — each run is independent, so `TournamentSimulator` distributes work across CPU cores via `ProcessPoolExecutor`.

Research module scores are pre-computed once before the simulation loop (O(n_teams)), not recalculated per match (which would be O(n_simulations × n_matches)).

Implemented in [src/tournament_simulator.py](src/tournament_simulator.py).

---

## Research modules

Each module is a hypothesis: does this factor, when added to Elo, improve prediction accuracy? Modules are composable — you can run the simulation with any combination and compare Brier Scores.

| Module | Hypothesis |
|--------|-----------|
| **Climate Adaptation Index (CAI)** | Teams playing far from their home climate (temperature, humidity, altitude) underperform relative to Elo |
| **Tournament Resilience Rating (TRR)** | Historical comeback wins, penalty shootout record, and underdog victories predict future clutch performance |
| **Pressure Performance Index (PPI)** | Teams with high-pressure club environments (Champions League knockouts) handle tournament pressure better |
| **Tournament DNA Score** | Some teams systematically outperform their pre-tournament Elo — a persistent "big tournament" effect |
| **Chaos Tolerance Rating** | Teams that maintain cohesion after red cards, injuries, and conceding first |
| **Leadership Stability Score** | Experienced captains and stable coaching tenures correlate with tournament overperformance |
| **Tactical Flexibility Index** | Teams that can shift formations mid-tournament adapt to bracket variance better |
| **Invisible Impact Score** | Off-ball contributions (pressing, recoveries, space creation) not captured in goals/assists |
| **Squad Fatigue Model** | Players with high club-season minutes entering a tournament show elevated injury risk |
| **Injury Impact Estimator** | Counterfactual win probability with and without key players |

### Validation methodology

With only ~22 World Cups in the data, overfitting is the primary risk. The platform uses:

- **Leave-one-tournament-out cross-validation** — train on WC 1990–2018, test on 2022, rotate
- **Brier Score** as the primary metric (lower = better calibrated probabilities)
- **Permutation testing** — shuffle module scores, re-run 1,000 times, confirm real scores beat shuffled baseline at p < 0.05
- **Bootstrapped confidence intervals** on all reported probabilities

---

## Architecture (planned)

The full platform is designed as a microservices system with event-driven communication:

```
Data Sources (StatsBomb, Transfermarkt, OpenWeather)
        ↓
  Kafka (ingestion.raw)
        ↓
  Normalization Service → PostgreSQL
        ↓
  Research Module Engine → Redis cache
        ↓
  Monte Carlo Workers (parallel, auto-scaling)
        ↓
  FastAPI → Dashboard / REST clients
```

**Key design decisions:**
- All inter-service communication through Kafka — no direct service-to-service HTTP in the critical path, enabling replay and fault isolation
- Research scores pre-computed and cached; simulation workers read from cache, not DB
- Simulation results cached in Redis for 24h — identical configs served instantly
- Spot instances for simulation workers (jobs are checkpointable to S3)

---

## API (planned)

```
GET  /teams/{id}/scores              Research module scores for a team
POST /simulations                    Trigger a new simulation run
GET  /simulations/{run_id}           Poll status and results
GET  /analytics/topk/champions       Top-K championship favorites
GET  /research/climate/{team_id}     Climate Adaptation Index breakdown
GET  /injuries/{team_id}             Current squad fatigue snapshot
```

Full spec covers versioned REST endpoints, cursor-based pagination, JWT auth (RS256), Redis rate limiting (sliding window), and CloudFront CDN caching for simulation results.

---

## Database

PostgreSQL schema with tables for `teams`, `tournaments`, `matches`, `research_scores`, `simulation_runs`, `simulation_results`, `player_fatigue`, and `notification_subscriptions`.

`research_scores` is a wide table keyed by `(team_id, tournament_id)` — all module scores in one row. This beats EAV for analytic query performance at the cost of schema migrations when modules are added.

---

## ML roadmap

| Phase | Status | Approach |
|-------|--------|----------|
| 1 | **Done** | Dixon-Coles bivariate Poisson + 10 research modules + parallel Monte Carlo bracket |
| 2 | Planned | Module scores as features in XGBoost; SHAP values to identify which modules add real lift |
| 3 | Planned | Neural network replacing Dixon-Coles, trained on StatsBomb event data |
| 4 | Planned | LSTM/Transformer on match sequences to capture momentum and fatigue accumulation |
| 5 | Planned | Causal inference layer for counterfactual simulation ("what if Neymar was fit in 2014?") |

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `numpy`, `scipy` | Statistical simulation, Poisson distributions |
| `pandas` | Data manipulation and historical dataset handling |
| `matplotlib` | Visualization and result plotting |
| `fastapi`, `uvicorn` | REST API server |
| `pydantic` | Request/response validation |

---

## Name

*Raumdeuter* was Jürgen Klinsmann's term for Thomas Müller — a player who couldn't be marked because he occupied space rather than positions. The name captures what this project is trying to do: find the analytical spaces that position-based (rankings-based) models miss.

---

## Status

**Phase 1 complete.** The full OOP simulation stack is working end-to-end:

- `Team` / `Tournament` dataclasses with climate and geo attributes
- 10 composable research modules with a shared abstract base class
- `MatchSimulator` with Dixon-Coles bivariate Poisson, extra time, and penalties
- `TournamentSimulator` with full group stage + knockout bracket, parallel Monte Carlo

**Up next:** FastAPI layer, PostgreSQL schema + real historical data ingestion, and statistical validation (Brier Score comparison of module configs against historical WC outcomes).
