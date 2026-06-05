"""
Raumdeuter REST API

Endpoints:
  GET  /teams                     — list all 32 teams with current Elo
  POST /predict  {home, away}     — XGBoost 3-way probability
  POST /simulate {home, away, n_sims, knockout} — Monte Carlo head-to-head
  GET  /modules?home=X&away=Y     — per-module score breakdown
  GET  /state                     — live tournament Elo changes + recent results
  POST /ingest                    — pull latest results from football-data.org

Run:
  uvicorn api:app --reload --app-dir src
  python src/api.py
"""
from __future__ import annotations

import dataclasses
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).parent))

from main import TEAMS, WC_2026, _COMPOSITOR, TEAM_HISTORIES  # noqa: E402
from match_simulator import MatchSimulator  # noqa: E402
from ml_model import XGBoostMatchPredictor, generate_training_data  # noqa: E402
from team import Team  # noqa: E402
from live_ingestion import load_live_elos, fetch_and_update, get_state_summary  # noqa: E402
from data_ingestion import load_h2h_data  # noqa: E402
from match_analysis import compute_matchup_features, h2h_summary, xg_summary  # noqa: E402

# ---------------------------------------------------------------------------
# Shared state — initialised once at startup
# ---------------------------------------------------------------------------

_BASE_ELOS: dict[str, float] = {t.name: t.elo for t in TEAMS}
_team_map: dict[str, Team] = {t.name.lower(): t for t in TEAMS}
_match_sim = MatchSimulator()
_model: XGBoostMatchPredictor | None = None
_H2H_DATA: dict[str, dict] = load_h2h_data()


def _get_model() -> XGBoostMatchPredictor:
    global _model
    if _model is None:
        samples = generate_training_data(
            TEAMS, WC_2026, _COMPOSITOR, TEAM_HISTORIES, n_samples=2_000,
            h2h_data=_H2H_DATA,
        )
        _model = XGBoostMatchPredictor()
        _model.train(samples)
    return _model


def _resolve(name: str) -> Team:
    """Resolve a team name to a Team object with the current live Elo."""
    base = _team_map.get(name.lower())
    if not base:
        matches = [t for t in TEAMS if name.lower() in t.name.lower()]
        if len(matches) == 1:
            base = matches[0]
        elif len(matches) > 1:
            raise HTTPException(
                status_code=422,
                detail=f"Ambiguous team name {name!r}: {[t.name for t in matches]}",
            )
        else:
            raise HTTPException(status_code=404, detail=f"Team not found: {name!r}")

    live_elos = load_live_elos(_BASE_ELOS)
    live_elo = live_elos.get(base.name, base.elo)
    return dataclasses.replace(base, elo=live_elo)


# ---------------------------------------------------------------------------
# App + lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-train so the first /predict call isn't slow
    _get_model()
    yield


app = FastAPI(
    title="Raumdeuter",
    description="WC 2026 match predictor — Dixon-Coles + XGBoost + SHAP research modules",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class MatchupRequest(BaseModel):
    home: str = Field(..., examples=["Argentina"])
    away: str = Field(..., examples=["France"])


class SimRequest(MatchupRequest):
    n_sims: int = Field(2_000, ge=100, le=50_000)
    knockout: bool = False


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def root() -> dict[str, Any]:
    return {
        "name": "Raumdeuter",
        "version": "1.0.0",
        "teams": len(TEAMS),
        "endpoints": ["/teams", "/predict", "/simulate", "/modules"],
    }


@app.get("/teams")
def list_teams() -> list[dict[str, Any]]:
    live_elos = load_live_elos(_BASE_ELOS)
    return [
        {
            "name": t.name,
            "elo": round(live_elos.get(t.name, t.elo), 1),
            "elo_base": t.elo,
            "elo_delta": round(live_elos.get(t.name, t.elo) - t.elo, 1),
            "fifa_code": t.fifa_code,
            "confederation": t.confederation,
        }
        for t in sorted(TEAMS, key=lambda t: -live_elos.get(t.name, t.elo))
    ]


@app.get("/state")
def tournament_state() -> dict[str, Any]:
    """Live tournament state: Elo changes since kick-off, recent results."""
    return get_state_summary(_BASE_ELOS)


@app.post("/ingest")
def ingest() -> dict[str, Any]:
    """
    Pull latest finished matches from football-data.org and update Elos.
    Requires FD_API_KEY environment variable.
    """
    api_key = os.environ.get("FD_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="FD_API_KEY environment variable not set. "
                   "Get a free key at https://www.football-data.org/client/register",
        )
    try:
        new_entries = fetch_and_update(api_key, _BASE_ELOS)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"football-data.org fetch failed: {exc}")

    return {
        "new_matches": len(new_entries),
        "results": [e.to_dict() for e in new_entries],
    }


@app.post("/predict")
def predict(req: MatchupRequest) -> dict[str, Any]:
    """XGBoost 3-way match outcome probabilities for a single matchup."""
    home = _resolve(req.home)
    away = _resolve(req.away)
    model = _get_model()

    home_scores = _COMPOSITOR.compute_all(home, WC_2026, TEAM_HISTORIES.get(home.name))
    away_scores = _COMPOSITOR.compute_all(away, WC_2026, TEAM_HISTORIES.get(away.name))
    matchup = compute_matchup_features(home.name, away.name, TEAM_HISTORIES, _H2H_DATA)
    probs = model.predict_proba(home.elo, away.elo, home_scores, away_scores, matchup)

    elo_win = _match_sim.elo_win_probability(home, away)
    return {
        "home_team": home.name,
        "away_team": away.name,
        "home_elo": home.elo,
        "away_elo": away.elo,
        "home_win": round(probs["home_win"], 4),
        "draw": round(probs["draw"], 4),
        "away_win": round(probs["away_win"], 4),
        "elo_home_win": round(elo_win, 4),
        "module_delta": round(probs["home_win"] - elo_win, 4),
    }


@app.post("/simulate")
def simulate(req: SimRequest) -> dict[str, Any]:
    """Monte Carlo Dixon-Coles simulation for a matchup."""
    home = _resolve(req.home)
    away = _resolve(req.away)

    home_scores = _COMPOSITOR.compute_all(home, WC_2026, TEAM_HISTORIES.get(home.name))
    away_scores = _COMPOSITOR.compute_all(away, WC_2026, TEAM_HISTORIES.get(away.name))

    counts: dict[str, int] = {home.name: 0, away.name: 0, "Draw": 0}
    for _ in range(req.n_sims):
        result = _match_sim.simulate(home, away, home_scores, away_scores, knockout=req.knockout)
        key = result.winner.name if result.winner else "Draw"
        counts[key] += 1

    n = req.n_sims
    return {
        "home_team": home.name,
        "away_team": away.name,
        "n_sims": n,
        "knockout": req.knockout,
        "home_win_pct": round(counts[home.name] / n, 4),
        "draw_pct": round(counts["Draw"] / n, 4),
        "away_win_pct": round(counts[away.name] / n, 4),
        "elo_home_win": round(_match_sim.elo_win_probability(home, away), 4),
    }


@app.get("/modules")
def modules(
    home: str = Query(..., examples=["Argentina"]),
    away: str = Query(..., examples=["France"]),
) -> dict[str, Any]:
    """Per-module research scores for both teams in a matchup."""
    home_team = _resolve(home)
    away_team = _resolve(away)

    home_scores = _COMPOSITOR.compute_all(home_team, WC_2026, TEAM_HISTORIES.get(home_team.name))
    away_scores = _COMPOSITOR.compute_all(away_team, WC_2026, TEAM_HISTORIES.get(away_team.name))

    modules_out = {}
    for mod_name in home_scores:
        modules_out[mod_name] = {
            home_team.name: round(home_scores[mod_name], 2),
            away_team.name: round(away_scores[mod_name], 2),
            "delta": round(home_scores[mod_name] - away_scores[mod_name], 2),
        }

    return {
        "home_team": home_team.name,
        "away_team": away_team.name,
        "home_composite": round(_COMPOSITOR.composite_score(home_team, WC_2026, TEAM_HISTORIES.get(home_team.name)), 2),
        "away_composite": round(_COMPOSITOR.composite_score(away_team, WC_2026, TEAM_HISTORIES.get(away_team.name)), 2),
        "modules": modules_out,
    }


@app.get("/analysis")
def analysis(
    home: str = Query(..., examples=["Argentina"]),
    away: str = Query(..., examples=["France"]),
) -> dict[str, Any]:
    """
    Deep single-match analysis: prediction, head-to-head history,
    xG form, and per-module research scores in one response.
    """
    home_team = _resolve(home)
    away_team = _resolve(away)
    model = _get_model()

    home_scores = _COMPOSITOR.compute_all(home_team, WC_2026, TEAM_HISTORIES.get(home_team.name))
    away_scores = _COMPOSITOR.compute_all(away_team, WC_2026, TEAM_HISTORIES.get(away_team.name))
    matchup = compute_matchup_features(home_team.name, away_team.name, TEAM_HISTORIES, _H2H_DATA)
    probs = model.predict_proba(home_team.elo, away_team.elo, home_scores, away_scores, matchup)

    elo_win = _match_sim.elo_win_probability(home_team, away_team)
    matchup_adj = probs["home_win"] - elo_win

    modules_out = {
        mod: {
            home_team.name: round(home_scores[mod], 1),
            away_team.name: round(away_scores[mod], 1),
            "edge": (
                f"{home_team.name} +{home_scores[mod] - away_scores[mod]:.1f}"
                if home_scores[mod] >= away_scores[mod]
                else f"{away_team.name} +{away_scores[mod] - home_scores[mod]:.1f}"
            ),
        }
        for mod in home_scores
    }

    home_comp = _COMPOSITOR.composite_score(home_team, WC_2026, TEAM_HISTORIES.get(home_team.name))
    away_comp = _COMPOSITOR.composite_score(away_team, WC_2026, TEAM_HISTORIES.get(away_team.name))

    return {
        "home_team": home_team.name,
        "away_team": away_team.name,
        "home_elo": round(home_team.elo, 1),
        "away_elo": round(away_team.elo, 1),
        "prediction": {
            "home_win": round(probs["home_win"], 4),
            "draw": round(probs["draw"], 4),
            "away_win": round(probs["away_win"], 4),
            "elo_baseline_home_win": round(elo_win, 4),
            "matchup_adjustment": f"{matchup_adj:+.3f}",
        },
        "head_to_head": h2h_summary(home_team.name, away_team.name, _H2H_DATA),
        "xg_form": xg_summary(home_team.name, away_team.name, TEAM_HISTORIES),
        "research_modules": modules_out,
        "composite_score": {
            home_team.name: round(home_comp, 1),
            away_team.name: round(away_comp, 1),
            "edge": (
                f"{home_team.name} +{home_comp - away_comp:.1f}"
                if home_comp >= away_comp
                else f"{away_team.name} +{away_comp - home_comp:.1f}"
            ),
        },
    }


# ---------------------------------------------------------------------------
# Dev entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True, app_dir=str(Path(__file__).parent))
