# Raumdeuter

> *Raumdeuter* (German): "space interpreter" — a footballer who reads and exploits space before others see it. Named after the analytical style of players like Thomas Müller; this platform tries to find the spaces in football data that conventional analysis misses.

A production-grade football analytics platform for predicting FIFA World Cup outcomes, with a focus on testing unconventional hypotheses about what truly drives tournament success.

---

## What it does

Most World Cup prediction models lean on FIFA rankings or Elo ratings and call it done. Raumdeuter goes further: it models the intangibles — climate adaptation, tournament resilience, pressure performance, squad cohesion under chaos — and runs Monte Carlo simulations to quantify how much (if at all) those factors lift predictive accuracy over a pure Elo baseline.

The core research question: **do the intangibles actually matter, or are they noise?**

As the 2026 tournament runs, Raumdeuter ingests live match results, updates team Elo ratings after every game, and re-runs simulations so every prediction reflects the tournament in its current state.

---

## Project structure

```
Raumdeuter/
├── src/
│   ├── team.py                  # Team + Tournament dataclasses (Elo, climate, geo)
│   ├── research_modules.py      # 10 research modules + ModuleCompositor
│   ├── match_simulator.py       # Dixon-Coles bivariate Poisson match model
│   ├── tournament_simulator.py  # Full group stage + knockout Monte Carlo
│   ├── ml_model.py              # XGBoostMatchPredictor + FeatureBuilder
│   ├── shap_analyzer.py         # SHAP module lift analysis
│   ├── validation.py            # k-fold Brier Score validation
│   ├── data_ingestion.py        # StatsBomb historical WC data pipeline + H2H records
│   ├── live_ingestion.py        # football-data.org live result ingestion + Elo updates
│   ├── match_analysis.py        # Matchup features: H2H history, xG form, tactical context
│   ├── notify.py                # GitHub Actions notifier — fetches results + pushes to ntfy
│   ├── api.py                   # FastAPI REST server
│   └── main.py                  # CLI runner + 32-team WC 2026 field
├── .github/
│   └── workflows/
│       └── notify.yml           # Cron job: fetch results every 3h, push phone notification
├── data/
│   ├── team_histories.json      # Cached StatsBomb per-team metrics (auto-generated)
│   ├── h2h_data.json            # Cached WC head-to-head records (auto-generated)
│   └── tournament_state.json    # Live Elo state — updated after each result
├── notebooks/
├── tests/
├── requirements.txt
├── .env                         # FD_API_KEY (not committed)
└── README.md
```

---

## Quickstart

**Prerequisites:** Python 3.9+

```bash
git clone https://github.com/aabu4537/raumdeuter.git
cd Raumdeuter
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

# macOS only — XGBoost requires OpenMP
brew install libomp
```

### Run the CLI predictor

```bash
python src/main.py
```

Prompts you to pick two teams, then prints head-to-head win probabilities, module score breakdowns, and XGBoost predictions with SHAP attribution.

### Run the API server

```bash
uvicorn api:app --app-dir src --reload
```

Then open **http://localhost:8000/docs** for the interactive UI.

---

## REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/teams` | All 32 teams with current Elo (live-adjusted during tournament) |
| `POST` | `/predict` | XGBoost 3-way match probabilities + module delta vs Elo baseline |
| `POST` | `/simulate` | Monte Carlo head-to-head (configurable n\_sims, knockout flag) |
| `GET` | `/modules` | Per-module score breakdown for a matchup |
| `GET` | `/analysis` | Full deep analysis: H2H history, xG form, modules, and prediction in one response |
| `GET` | `/state` | Live tournament state: Elo changes + recent results |
| `POST` | `/ingest` | Pull latest results from football-data.org and update Elos |

### Example — predict a matchup

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"home": "Argentina", "away": "France"}'
```

```json
{
  "home_team": "Argentina",
  "away_team": "France",
  "home_elo": 2150,
  "away_elo": 2100,
  "home_win": 0.5358,
  "draw": 0.2836,
  "away_win": 0.1805,
  "elo_home_win": 0.5715,
  "module_delta": -0.0356
}
```

`module_delta` is the XGBoost win probability minus the raw Elo win probability — positive means the research modules favour this team beyond what Elo predicts.

### Example — deep match analysis

```bash
curl "http://localhost:8000/analysis?home=Argentina&away=France"
```

```json
{
  "home_team": "Argentina",
  "away_team": "France",
  "home_elo": 2150.0,
  "away_elo": 2100.0,
  "prediction": {
    "home_win": 0.5021,
    "draw": 0.2614,
    "away_win": 0.2365,
    "elo_baseline_home_win": 0.5715,
    "matchup_adjustment": "-0.069"
  },
  "head_to_head": {
    "wc_meetings": 1,
    "home_wins": 1,
    "away_wins": 0,
    "draws": 0,
    "record": "Argentina 1W – 0D – 0W France",
    "source": "StatsBomb WC 2018 + 2022 open data"
  },
  "xg_form": {
    "Argentina": { "xg_per_game": 1.84, "xg_against_per_game": 0.93, "wc_games_in_dataset": 14 },
    "France":    { "xg_per_game": 1.56, "xg_against_per_game": 1.12, "wc_games_in_dataset": 13 },
    "attack_edge": "Argentina +0.28",
    "defense_edge": "Argentina +0.19 xG conceded"
  },
  "research_modules": {
    "tournament_dna": { "Argentina": 72.3, "France": 68.1, "edge": "Argentina +4.2" },
    "...": "..."
  },
  "composite_score": { "Argentina": 65.2, "France": 63.8, "edge": "Argentina +1.4" }
}
```

### Example — Monte Carlo simulation

```bash
curl -X POST http://localhost:8000/simulate \
  -H "Content-Type: application/json" \
  -d '{"home": "Morocco", "away": "Brazil", "n_sims": 5000, "knockout": true}'
```

---

## Live data ingestion

Raumdeuter uses two data layers:

### Historical (pre-tournament) — StatsBomb

On first run, `data_ingestion.py` fetches all men's World Cup data from the [StatsBomb open dataset](https://github.com/statsbomb/open-data) and computes per-team metrics for the research modules:

- Comeback win rates, penalty shootout records (TournamentResilienceRating)
- Late goals, wins from behind (PressurePerformanceIndex)
- Pressing intensity, ball recoveries, progressive carries per 90 (InvisibleImpactScore)
- Tournament round progression vs expected (TournamentDNAScore)
- xG for/against per game (match analysis + XGBoost features)
- Head-to-head WC records for every meeting in the dataset (match analysis)

Results cache to `data/team_histories.json` and `data/h2h_data.json` — subsequent starts are instant.

### Live (during tournament) — football-data.org

`live_ingestion.py` pulls finished WC 2026 matches from [football-data.org](https://www.football-data.org) and applies Elo updates (K=40) after every result. The API reads live Elos from `data/tournament_state.json` automatically — no server restart needed.

**Setup:**

1. Get a free API key at https://www.football-data.org/client/register
2. Add it to `.env`:
   ```
   FD_API_KEY=your_key_here
   ```
3. Trigger an update:
   ```bash
   # via CLI
   python src/live_ingestion.py

   # via API
   curl -X POST http://localhost:8000/ingest
   ```

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

Goals are sampled from the joint distribution with the Dixon-Coles correction applied to low-scoring results (0-0, 1-0, 0-1, 1-1), which standard Poisson underestimates in football. Knockout draws go to extra time (30% rate) then penalties (50/50).

### XGBoost match predictor + SHAP analysis

`XGBoostMatchPredictor` is trained on feature vectors built from Elo and module scores:

```
[elo_diff, home_climate, away_climate, climate_delta,
 home_resilience, away_resilience, resilience_delta, ...,
 home_composite, away_composite, composite_delta,
 h2h_win_rate, h2h_meetings, home_xg_per_game, away_xg_per_game,
 xg_form_diff, xg_against_diff]
```

`SHAPAnalyzer` computes SHAP values (TreeExplainer) and surfaces a module lift table showing which research modules add genuine predictive value versus noise on top of Elo:

```
Source                   SHAP    % Total  Verdict
climate_adaptation       0.063    63.3%   significant lift
elo_baseline             0.026    26.5%   baseline
tournament_resilience    0.000     0.0%   noise
```

---

## Research modules

| Module | Hypothesis |
|--------|-----------|
| **Climate Adaptation Index** | Teams playing far from their home climate underperform relative to Elo |
| **Tournament Resilience Rating** | Comeback wins, shootout record, and underdog victories predict clutch performance |
| **Pressure Performance Index** | High-pressure club environments translate to tournament composure |
| **Tournament DNA Score** | Some teams systematically outperform their pre-tournament Elo |
| **Chaos Tolerance Rating** | Teams that maintain cohesion after red cards and conceding first |
| **Leadership Stability Score** | Experienced captains and stable coaching tenures correlate with overperformance |
| **Tactical Flexibility Index** | Formation shifts mid-tournament signal adaptability |
| **Invisible Impact Score** | Pressing, ball recoveries, and progressive carries not captured in goals |
| **Squad Fatigue Model** | High pre-tournament club workload elevates injury and underperformance risk |
| **Injury Impact Estimator** | Win probability drop from key player absences |

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `numpy`, `scipy` | Statistical simulation, Poisson distributions |
| `pandas` | Data manipulation |
| `xgboost` | Match outcome predictor |
| `shap` | Feature importance and module lift analysis |
| `scikit-learn` | k-fold cross-validation, Brier Score |
| `statsbombpy` | Historical WC event data |
| `httpx` | HTTP client for football-data.org API |
| `fastapi`, `uvicorn` | REST API server |
| `pydantic` | Request/response validation |

---

## ML roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| 1 | ✅ Done | Dixon-Coles + 10 research modules + parallel Monte Carlo bracket |
| 2 | ✅ Done | XGBoost on module-enriched features + SHAP lift analysis + Brier Score validation |
| 3 | ✅ Done | FastAPI REST layer + StatsBomb historical data ingestion |
| 4 | ✅ Done | Live result ingestion + real-time Elo updates (football-data.org) |
| 5 | ✅ Done | GitHub Actions cron every 3h — fetches results + pushes phone notification via ntfy |
| 6 | ✅ Done | Deep match analysis: H2H history, xG form + tactical context as XGBoost features; `/analysis` endpoint |

---

## Name

*Raumdeuter* was Jürgen Klinsmann's term for Thomas Müller — a player who couldn't be marked because he occupied space rather than positions. The name captures what this project is trying to do: find the analytical spaces that position-based (rankings-based) models miss.
