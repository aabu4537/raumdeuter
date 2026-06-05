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
│   ├── team.py                  # Team data model (Elo, attributes)
│   ├── match_simulator.py       # Elo-based head-to-head probability + result
│   ├── tournament_simulator.py  # Full bracket simulation (WIP)
│   └── main.py                  # Entry point / demo runner
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
git clone <repo-url>
cd Raumdeuter
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run a basic head-to-head Monte Carlo simulation
cd src
python main.py
```

Example output:
```
{'France': 423, 'Argentina': 577}
```

This runs 1,000 simulated matches between France (Elo 2100) and Argentina (Elo 2150) using the standard Elo win-probability formula. Argentina wins ~57.7% — consistent with their rating advantage.

---

## How the simulation works

### Match probability (current)

Uses the standard Elo expected-score formula:

```
P(A beats B) = 1 / (1 + 10^((Elo_B - Elo_A) / 400))
```

Implemented in [src/match_simulator.py](src/match_simulator.py).

### Monte Carlo tournament simulation (roadmap)

Run the full 48-team, 64-match World Cup bracket `n` times (default 100,000). Aggregate win/finalist/semifinal counts to produce calibrated probabilities. The simulation is embarrassingly parallel — each run is independent, so it scales linearly with worker count.

Planned match model upgrade: **Dixon-Coles bivariate Poisson**, which corrects standard Poisson's underestimation of low-scoring results (0-0, 1-0, 0-1) common in knockout football.

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

| Phase | Approach |
|-------|----------|
| 1 (current) | Monte Carlo + hand-engineered Elo module |
| 2 | Module scores as features in XGBoost; SHAP values to identify which modules add real lift |
| 3 | Neural network replacing Dixon-Coles, trained on StatsBomb event data |
| 4 | LSTM/Transformer on match sequences to capture momentum and fatigue accumulation |
| 5 | Causal inference layer for counterfactual simulation ("what if Neymar was fit in 2014?") |

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

Early development. The Elo simulator and Monte Carlo loop are working. Research modules, tournament bracket simulation, FastAPI layer, and database integration are in progress.
