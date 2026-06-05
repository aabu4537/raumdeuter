"""
StatsBomb open-data ingestion for per-team World Cup history metrics.

First run downloads all available men's WC event data from StatsBomb's free
dataset (covers WC 2018 and WC 2022 as of 2025) and computes the per-team
history dict consumed by the research modules. Results cache to
data/team_histories.json so subsequent imports are instant.

Fields derivable from StatsBomb:
  comeback_wins / conceded_first_matches   (TournamentResilienceRating)
  shootout_wins / shootouts                (TournamentResilienceRating)
  goals_after_80min / total_goals          (PressurePerformanceIndex)
  wins_when_behind / matches_when_behind   (PressurePerformanceIndex)
  ten_man_points_pct / red_card_recovery   (ChaosTolerance)
  pressures_per_90                         (InvisibleImpactScore)
  ball_recoveries_per_90                   (InvisibleImpactScore)
  progressive_actions_per_90              (InvisibleImpactScore)
  finish_round_deltas                      (TournamentDNAScore)

Fields left at safe defaults (need external sources):
  coach_tenure_years, captain_caps         (LeadershipStabilityScore)
  distinct_formations_per_tournament       (TacticalFlexibilityIndex)
  avg_key_player_minutes_last_30_days      (SquadFatigueModel)
  key_players_injured                      (InjuryImpactEstimator)
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

CACHE_PATH = Path(__file__).parent.parent / "data" / "team_histories.json"

# Furthest round a team reaches in a WC → integer rank
ROUND_RANK: dict[str, int] = {
    "Group Stage": 1,
    "Round of 16": 2,
    "Quarter-finals": 3,
    "Semi-finals": 4,
    "3rd Place Final": 4,
    "Final": 5,
}
# Neutral baseline: R16 is the expected exit for any qualified team
_EXPECTED_ROUND = 2.0

# StatsBomb team names that differ from our internal names
_SB_NAME_MAP: dict[str, str] = {
    "United States": "USA",
    "Korea Republic": "South Korea",
    "IR Iran": "Iran",
    "Republic of Ireland": "Ireland",
}


# ---------------------------------------------------------------------------
# Name normalisation helpers
# ---------------------------------------------------------------------------

def _canon(val) -> str:
    """Extract and normalise a team name from a raw StatsBomb value."""
    if isinstance(val, dict):
        name = (
            val.get("home_team_name")
            or val.get("away_team_name")
            or val.get("name")
            or ""
        )
    else:
        name = str(val).strip()
    return _SB_NAME_MAP.get(name, name)


def _match_team(match, side: str) -> str:
    """Return our canonical team name for 'home' or 'away' side of a match row."""
    return _canon(match.get(f"{side}_team", ""))


def _stage_name(match) -> str:
    raw = match.get("competition_stage", {})
    return raw.get("name", "Group Stage") if isinstance(raw, dict) else str(raw)


def _event_type(val) -> str:
    return val.get("name", "") if isinstance(val, dict) else str(val)



# ---------------------------------------------------------------------------
# Per-team accumulator
# ---------------------------------------------------------------------------

@dataclass
class _Acc:
    comeback_wins: int = 0
    conceded_first: int = 0
    shootout_wins: int = 0
    shootouts: int = 0
    goals_after_80: int = 0
    total_goals: int = 0
    wins_when_behind: int = 0
    matches_when_behind: int = 0
    ten_man_points: float = 0.0
    ten_man_matches: int = 0
    pressures: float = 0.0
    recoveries: float = 0.0
    prog_actions: float = 0.0
    total_minutes: float = 0.0
    best_round_per_wc: list[int] = field(default_factory=list)

    def finalize(self) -> dict:
        mins = max(self.total_minutes, 1.0)
        ten_man_rate = (
            self.ten_man_points / (self.ten_man_matches * 3.0)
            if self.ten_man_matches else 0.5
        )
        return {
            # TournamentResilienceRating
            "comeback_wins": self.comeback_wins,
            "conceded_first_matches": max(self.conceded_first, 1),
            "shootout_wins": self.shootout_wins,
            "shootouts": self.shootouts,
            "underdog_wins": 0,
            "underdog_matches": 1,
            # PressurePerformanceIndex
            "ucl_knockout_wins": 0,
            "ucl_knockout_matches": 1,
            "goals_after_80min": self.goals_after_80,
            "total_goals": max(self.total_goals, 1),
            "wins_when_behind": self.wins_when_behind,
            "matches_when_behind": max(self.matches_when_behind, 1),
            # TournamentDNAScore
            "finish_round_deltas": [r - _EXPECTED_ROUND for r in self.best_round_per_wc],
            # ChaosTolerance
            "ten_man_points_pct": round(ten_man_rate, 3),
            "red_card_recovery_rate": round(ten_man_rate, 3),
            "avg_sub_xg_improvement": 0.0,
            # InvisibleImpactScore
            "pressures_per_90": round(self.pressures / mins * 90, 1),
            "ball_recoveries_per_90": round(self.recoveries / mins * 90, 1),
            "progressive_actions_per_90": round(self.prog_actions / mins * 90, 1),
            # LeadershipStabilityScore — external source needed
            "coach_tenure_years": 2.0,
            "captain_caps": 80,
            # TacticalFlexibilityIndex — external source needed
            "distinct_formations_per_tournament": 2,
            "win_rate_after_formation_change": 0.5,
            # SquadFatigueModel — pre-tournament club data needed
            "avg_key_player_minutes_last_30_days": 270,
            "travel_km_last_30_days": 5000,
            # InjuryImpactEstimator — pre-tournament roster data needed
            "key_players_injured": 0,
            "avg_injured_player_importance": 0.0,
        }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_team_histories(force_refresh: bool = False) -> dict[str, dict]:
    """
    Return per-team history metrics derived from StatsBomb WC open data.
    Caches to data/team_histories.json on first call; subsequent calls are instant.
    Pass force_refresh=True to re-download and recompute.
    """
    if not force_refresh and CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text())

    print("Building team histories from StatsBomb open data...")
    print("(First run only — subsequent starts use data/team_histories.json)")
    histories = _build()
    if histories:
        CACHE_PATH.parent.mkdir(exist_ok=True)
        CACHE_PATH.write_text(json.dumps(histories, indent=2))
        print(f"Cached {len(histories)} teams to {CACHE_PATH}")
    return histories


# ---------------------------------------------------------------------------
# Build pipeline
# ---------------------------------------------------------------------------

def _build() -> dict[str, dict]:
    try:
        from statsbombpy import sb
    except ImportError:
        print(
            "statsbombpy not installed. Run: pip install statsbombpy\n"
            "Falling back to empty team histories.",
            file=sys.stderr,
        )
        return {}

    comps = sb.competitions()
    wc = comps[
        (comps["competition_name"] == "FIFA World Cup")
        & (comps["competition_gender"] == "male")
    ]
    if wc.empty:
        print("No men's WC competitions found in StatsBomb free data.", file=sys.stderr)
        return {}

    acc: dict[str, _Acc] = defaultdict(_Acc)

    for _, row in wc.iterrows():
        comp_id = int(row["competition_id"])
        season_id = int(row["season_id"])
        label = row["season_name"]

        print(f"\n  {label} — loading match list...", flush=True)
        try:
            matches = sb.matches(competition_id=comp_id, season_id=season_id)
        except Exception as exc:
            print(f"  Skipping {label}: {exc}", file=sys.stderr)
            continue

        _ingest_matches(matches, acc)

        n = len(matches)
        print(f"  {label} — processing events for {n} matches...", flush=True)
        for i, (_, match) in enumerate(matches.iterrows(), 1):
            try:
                events = sb.events(match_id=int(match["match_id"]))
                _ingest_events(events, match, acc)
            except Exception:
                pass
            if i % 16 == 0 or i == n:
                print(f"    {i}/{n}", flush=True)

    return {name: a.finalize() for name, a in acc.items() if name}


# ---------------------------------------------------------------------------
# Match-level pass (tournament progression)
# ---------------------------------------------------------------------------

def _ingest_matches(matches, acc: dict[str, _Acc]) -> None:
    """Record each team's furthest WC round from match-level data only."""
    best: dict[str, int] = defaultdict(int)
    for _, m in matches.iterrows():
        home = _match_team(m, "home")
        away = _match_team(m, "away")
        rank = ROUND_RANK.get(_stage_name(m), 1)
        best[home] = max(best[home], rank)
        best[away] = max(best[away], rank)
    for team, rank in best.items():
        if team:
            acc[team].best_round_per_wc.append(rank)


# ---------------------------------------------------------------------------
# Event-level pass (per-match stats)
# ---------------------------------------------------------------------------

def _ingest_events(events, match, acc: dict[str, _Acc]) -> None:
    if events is None or events.empty:
        return

    home = _match_team(match, "home")
    away = _match_team(match, "away")
    home_score = int(match.get("home_score") or 0)
    away_score = int(match.get("away_score") or 0)

    # Vectorised type and team Series — same index as events
    type_col = events["type"].apply(_event_type)
    team_col = events["team"].apply(lambda x: _canon(x) if isinstance(x, dict) else _canon(str(x)))

    # 90 minutes of data per match per team
    for team in (home, away):
        acc[team].total_minutes += 90.0

    # --- Goals (periods 1–4, excluding penalty shootout period 5) ---
    goal_mask = (type_col == "Shot") & (events["period"] <= 4)
    if "shot_outcome" in events.columns:
        goal_mask = goal_mask & (events["shot_outcome"] == "Goal")
    goal_events = events[goal_mask].sort_values("minute")

    _update_comeback_stats(goal_events, team_col, home, away, home_score, away_score, acc)
    _update_goal_stats(goal_events, team_col, home, away, acc)
    _update_behind_stats(goal_events, team_col, home, away, home_score, away_score, acc)

    # --- Penalty shootout (period 5) ---
    if 5 in events["period"].values:
        _update_shootout_stats(events, type_col, team_col, home, away, acc)

    # --- Red cards / 10-man performance ---
    _update_red_card_stats(events, type_col, team_col, home, away, home_score, away_score, acc)

    # --- Pressing, recoveries, progressive carries ---
    _update_invisible_stats(events, type_col, team_col, home, away, acc)


def _update_comeback_stats(
    goal_events, team_col, home, away, home_score, away_score, acc
) -> None:
    if goal_events.empty:
        return
    first_scorer = team_col.get(goal_events.index[0], "")
    conceded_first = away if first_scorer == home else home
    acc[conceded_first].conceded_first += 1
    if conceded_first == home and home_score > away_score:
        acc[home].comeback_wins += 1
    elif conceded_first == away and away_score > home_score:
        acc[away].comeback_wins += 1


def _update_goal_stats(goal_events, team_col, home, away, acc) -> None:
    for team in (home, away):
        t_goals = goal_events[team_col.reindex(goal_events.index) == team]
        acc[team].total_goals += len(t_goals)
        acc[team].goals_after_80 += int((t_goals["minute"] >= 80).sum())


def _update_behind_stats(
    goal_events, team_col, home, away, home_score, away_score, acc
) -> None:
    score = {home: 0, away: 0}
    was_behind = {home: False, away: False}

    for idx in goal_events.index:
        scorer = team_col.get(idx, "")
        if scorer not in score:
            continue
        opp = away if scorer == home else home
        if score[opp] > score[scorer]:
            was_behind[scorer] = True
        score[scorer] += 1

    for team, won in ((home, home_score > away_score), (away, away_score > home_score)):
        if was_behind[team]:
            acc[team].matches_when_behind += 1
            if won:
                acc[team].wins_when_behind += 1


def _update_shootout_stats(events, type_col, team_col, home, away, acc) -> None:
    so = events[events["period"] == 5]
    if so.empty or "shot_outcome" not in so.columns:
        return
    so_type = type_col.reindex(so.index)
    so_team = team_col.reindex(so.index)
    goal_mask = (so_type == "Shot") & (so["shot_outcome"] == "Goal")
    if not goal_mask.any():
        return
    so_goals: dict[str, int] = {home: 0, away: 0}
    for idx in so[goal_mask].index:
        t = so_team.get(idx, "")
        if t in so_goals:
            so_goals[t] += 1
    winner = max(so_goals, key=lambda t: so_goals[t])
    for team in (home, away):
        acc[team].shootouts += 1
    acc[winner].shootout_wins += 1


def _update_red_card_stats(
    events, type_col, team_col, home, away, home_score, away_score, acc
) -> None:
    red_mask = type_col == "Bad Behaviour"
    if not red_mask.any() or "bad_behaviour_card" not in events.columns:
        return
    red_events = events[
        red_mask
        & events["bad_behaviour_card"].apply(lambda x: isinstance(x, str) and "Red" in x)
    ]
    for idx in red_events.index:
        red_team = team_col.get(idx, "")
        if red_team not in (home, away):
            continue
        pts = (
            3 if (red_team == home and home_score > away_score)
            or (red_team == away and away_score > home_score)
            else (1 if home_score == away_score else 0)
        )
        acc[red_team].ten_man_matches += 1
        acc[red_team].ten_man_points += pts


def _update_invisible_stats(events, type_col, team_col, home, away, acc) -> None:
    for team in (home, away):
        t_mask = team_col == team
        acc[team].pressures += float((type_col[t_mask] == "Pressure").sum())
        acc[team].recoveries += float((type_col[t_mask] == "Ball Recovery").sum())

        # Progressive carries: ball advanced ≥ 10 pitch units forward
        carry_mask = t_mask & (type_col == "Carry")
        if carry_mask.any() and "carry_end_location" in events.columns and "location" in events.columns:
            carry_rows = events[carry_mask]
            starts = carry_rows["location"].apply(
                lambda x: float(x[0]) if isinstance(x, list) and x else 0.0
            )
            ends = carry_rows["carry_end_location"].apply(
                lambda x: float(x[0]) if isinstance(x, list) and x else 0.0
            )
            acc[team].prog_actions += float(((ends - starts) > 10).sum())
