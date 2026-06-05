"""
Live WC 2026 result ingestion from football-data.org.

Fetches finished matches, applies Elo updates, and persists tournament state
to data/tournament_state.json. The API and notification script both read from
this file so predictions automatically reflect results as the tournament progresses.

Setup:
  1. Register for a free API key at https://www.football-data.org/client/register
  2. Set the environment variable: export FD_API_KEY=your_key_here

Usage:
  python src/live_ingestion.py          # fetch + update, print new results
  python src/live_ingestion.py --reset  # wipe state back to pre-tournament Elos
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

STATE_PATH = Path(__file__).parent.parent / "data" / "tournament_state.json"

FD_BASE = "https://api.football-data.org/v4"
WC_CODE = "WC"          # football-data.org competition code for FIFA World Cup
ELO_K = 40              # K-factor — higher than club football; WC matches are high-stakes

# football-data.org team names → our internal names
_FD_NAME_MAP: dict[str, str] = {
    "United States": "USA",
    "Korea Republic": "South Korea",
    "Iran": "Iran",
    "IR Iran": "Iran",
    "Saudi Arabia": "Saudi Arabia",
}


def _canon(name: str) -> str:
    return _FD_NAME_MAP.get(name, name)


# ---------------------------------------------------------------------------
# Elo math
# ---------------------------------------------------------------------------

def _elo_expected(elo_a: float, elo_b: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((elo_b - elo_a) / 400.0))


def _elo_update(elo_a: float, elo_b: float, score_a: float) -> tuple[float, float]:
    """score_a: 1.0 = home win, 0.5 = draw, 0.0 = away win."""
    exp = _elo_expected(elo_a, elo_b)
    delta = ELO_K * (score_a - exp)
    return elo_a + delta, elo_b - delta


# ---------------------------------------------------------------------------
# Tournament state
# ---------------------------------------------------------------------------

@dataclass
class MatchEntry:
    match_id: int
    home: str
    away: str
    score: str          # e.g. "3-3 (pen 4-2)"
    stage: str
    utc_date: str
    home_elo_before: float
    away_elo_before: float
    home_elo_after: float
    away_elo_after: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "match_id": self.match_id,
            "home": self.home,
            "away": self.away,
            "score": self.score,
            "stage": self.stage,
            "utc_date": self.utc_date,
            "home_elo_before": self.home_elo_before,
            "away_elo_before": self.away_elo_before,
            "home_elo_after": self.home_elo_after,
            "away_elo_after": self.away_elo_after,
            "home_delta": round(self.home_elo_after - self.home_elo_before, 1),
            "away_delta": round(self.away_elo_after - self.away_elo_before, 1),
        }


class TournamentState:
    """
    Live tournament state: current Elo per team + log of processed matches.
    Persisted to data/tournament_state.json.
    """

    def __init__(self, base_elos: dict[str, float]) -> None:
        self.elos: dict[str, float] = base_elos.copy()
        self.processed_ids: set[int] = set()
        self.match_log: list[dict] = []
        self.last_updated: str = ""

    # ------------------------------------------------------------------

    @classmethod
    def load(cls, base_elos: dict[str, float]) -> "TournamentState":
        """Load from disk; fall back to base Elos if no state file yet."""
        state = cls(base_elos)
        if STATE_PATH.exists():
            raw = json.loads(STATE_PATH.read_text())
            state.elos.update(raw.get("elos", {}))
            state.processed_ids = set(raw.get("processed_match_ids", []))
            state.match_log = raw.get("match_log", [])
            state.last_updated = raw.get("last_updated", "")
        return state

    def save(self) -> None:
        STATE_PATH.parent.mkdir(exist_ok=True)
        STATE_PATH.write_text(json.dumps({
            "elos": {k: round(v, 2) for k, v in self.elos.items()},
            "processed_match_ids": sorted(self.processed_ids),
            "match_log": self.match_log,
            "last_updated": self.last_updated,
        }, indent=2))

    # ------------------------------------------------------------------

    def apply(
        self,
        match_id: int,
        home: str,
        away: str,
        home_goals: int,
        away_goals: int,
        pen_home: int | None,
        pen_away: int | None,
        stage: str,
        utc_date: str,
    ) -> MatchEntry | None:
        """Apply one result. Returns MatchEntry if new, None if already processed."""
        if match_id in self.processed_ids:
            return None

        home_elo = self.elos.get(home, 1750.0)
        away_elo = self.elos.get(away, 1750.0)

        if home_goals > away_goals:
            score_home = 1.0
        elif away_goals > home_goals:
            score_home = 0.0
        elif pen_home is not None and pen_away is not None:
            score_home = 1.0 if pen_home > pen_away else 0.0
        else:
            score_home = 0.5

        new_home, new_away = _elo_update(home_elo, away_elo, score_home)
        self.elos[home] = new_home
        self.elos[away] = new_away
        self.processed_ids.add(match_id)
        self.last_updated = datetime.now(timezone.utc).isoformat()

        score_str = f"{home_goals}-{away_goals}"
        if pen_home is not None and pen_away is not None:
            score_str += f" (pen {pen_home}-{pen_away})"

        entry = MatchEntry(
            match_id=match_id,
            home=home,
            away=away,
            score=score_str,
            stage=stage,
            utc_date=utc_date,
            home_elo_before=round(home_elo, 1),
            away_elo_before=round(away_elo, 1),
            home_elo_after=round(new_home, 1),
            away_elo_after=round(new_away, 1),
        )
        self.match_log.append(entry.to_dict())
        return entry


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_live_elos(base_elos: dict[str, float]) -> dict[str, float]:
    """
    Return the latest Elo ratings — live if tournament_state.json exists,
    pre-tournament base values otherwise.
    """
    if not STATE_PATH.exists():
        return base_elos.copy()
    raw = json.loads(STATE_PATH.read_text())
    merged = base_elos.copy()
    merged.update(raw.get("elos", {}))
    return merged


def fetch_and_update(
    api_key: str,
    base_elos: dict[str, float],
) -> list[MatchEntry]:
    """
    Pull finished WC matches from football-data.org, apply Elo updates for
    any that haven't been processed yet. Returns newly processed entries.
    """
    state = TournamentState.load(base_elos)

    headers = {"X-Auth-Token": api_key}
    url = f"{FD_BASE}/competitions/{WC_CODE}/matches"
    params = {"status": "FINISHED"}

    resp = httpx.get(url, headers=headers, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    new_entries: list[MatchEntry] = []
    for m in data.get("matches", []):
        match_id = m["id"]
        if match_id in state.processed_ids:
            continue

        home = _canon(m["homeTeam"].get("name") or m["homeTeam"].get("shortName", ""))
        away = _canon(m["awayTeam"].get("name") or m["awayTeam"].get("shortName", ""))
        if not home or not away:
            continue

        score = m.get("score", {})
        ft = score.get("fullTime") or {}
        home_goals = ft.get("home") or 0
        away_goals = ft.get("away") or 0

        pen = score.get("penalties") or {}
        pen_home = pen.get("home")
        pen_away = pen.get("away")

        stage = m.get("stage", "")
        utc_date = m.get("utcDate", "")

        entry = state.apply(match_id, home, away, home_goals, away_goals,
                            pen_home, pen_away, stage, utc_date)
        if entry:
            new_entries.append(entry)

    if new_entries:
        state.save()

    return new_entries


def get_state_summary(base_elos: dict[str, float]) -> dict[str, Any]:
    """Return a dict summary of current tournament state for the API /state endpoint."""
    if not STATE_PATH.exists():
        return {
            "status": "pre_tournament",
            "matches_processed": 0,
            "last_updated": None,
            "elo_changes": {},
        }
    raw = json.loads(STATE_PATH.read_text())
    live_elos = raw.get("elos", {})
    changes = {
        team: round(live_elos[team] - base_elos.get(team, 1750), 1)
        for team in live_elos
        if abs(live_elos[team] - base_elos.get(team, 1750)) > 0.01
    }
    return {
        "status": "in_progress",
        "matches_processed": len(raw.get("processed_match_ids", [])),
        "last_updated": raw.get("last_updated"),
        "recent_matches": raw.get("match_log", [])[-5:],
        "elo_changes": dict(sorted(changes.items(), key=lambda x: -abs(x[1]))),
    }


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    sys.path.insert(0, str(Path(__file__).parent))
    from main import TEAMS

    base_elos = {t.name: t.elo for t in TEAMS}

    parser = argparse.ArgumentParser(description="Fetch live WC results and update Elos")
    parser.add_argument("--reset", action="store_true", help="Delete state and start fresh")
    args = parser.parse_args()

    if args.reset:
        if STATE_PATH.exists():
            STATE_PATH.unlink()
            print("State reset.")
        else:
            print("No state file to reset.")
        sys.exit(0)

    api_key = os.environ.get("FD_API_KEY", "")
    if not api_key:
        print("Error: set FD_API_KEY environment variable.", file=sys.stderr)
        print("Get a free key at https://www.football-data.org/client/register")
        sys.exit(1)

    print("Fetching WC results from football-data.org...")
    try:
        new = fetch_and_update(api_key, base_elos)
    except httpx.HTTPStatusError as e:
        print(f"API error {e.response.status_code}: {e.response.text}", file=sys.stderr)
        sys.exit(1)

    if not new:
        print("No new results.")
    else:
        print(f"{len(new)} new result(s):")
        for e in new:
            print(f"  {e.stage:<20} {e.home} {e.score} {e.away}")
            print(f"    Elo: {e.home} {e.home_elo_before:.0f}→{e.home_elo_after:.0f} "
                  f"({e.home_elo_after - e.home_elo_before:+.1f})  |  "
                  f"{e.away} {e.away_elo_before:.0f}→{e.away_elo_after:.0f} "
                  f"({e.away_elo_after - e.away_elo_before:+.1f})")
