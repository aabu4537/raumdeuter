"""
Single-match deep analysis: head-to-head history + xG form features.

These become additional XGBoost features (feeding matchup-specific signal that
per-team aggregate stats miss) and power the /analysis API endpoint display.
"""
from __future__ import annotations

_DEFAULT_XG = 1.3  # neutral prior when a team has no StatsBomb WC data


def compute_matchup_features(
    home_name: str,
    away_name: str,
    team_histories: dict[str, dict],
    h2h_data: dict[str, dict],
) -> dict[str, float]:
    """
    Return a flat dict of 6 matchup-specific features for home vs away.
    All values have safe defaults so this never raises on missing data.
    """
    key = "|".join(sorted([home_name, away_name]))
    h2h = h2h_data.get(key, {})
    meetings = int(h2h.get("meetings", 0))
    h2h_win_rate = (
        int(h2h.get(f"{home_name}_wins", 0)) / meetings if meetings > 0 else 0.5
    )

    home_hist = team_histories.get(home_name, {})
    away_hist = team_histories.get(away_name, {})
    home_xg = float(home_hist.get("xg_for_per_game", _DEFAULT_XG))
    away_xg = float(away_hist.get("xg_for_per_game", _DEFAULT_XG))
    home_xga = float(home_hist.get("xg_against_per_game", _DEFAULT_XG))
    away_xga = float(away_hist.get("xg_against_per_game", _DEFAULT_XG))

    return {
        "h2h_win_rate": h2h_win_rate,
        "h2h_meetings": float(meetings),
        "home_xg_per_game": home_xg,
        "away_xg_per_game": away_xg,
        "xg_form_diff": home_xg - away_xg,
        "xg_against_diff": home_xga - away_xga,
    }


def h2h_summary(
    home_name: str,
    away_name: str,
    h2h_data: dict[str, dict],
) -> dict:
    """Return a display-ready h2h breakdown for the /analysis endpoint."""
    key = "|".join(sorted([home_name, away_name]))
    h2h = h2h_data.get(key, {})
    meetings = int(h2h.get("meetings", 0))
    home_wins = int(h2h.get(f"{home_name}_wins", 0))
    away_wins = int(h2h.get(f"{away_name}_wins", 0))
    draws = int(h2h.get("draws", 0))

    if meetings == 0:
        record = "No WC meetings in dataset (WC 2018 + 2022)"
    else:
        record = f"{home_name} {home_wins}W – {draws}D – {away_wins}W {away_name}"

    return {
        "wc_meetings": meetings,
        "home_wins": home_wins,
        "away_wins": away_wins,
        "draws": draws,
        "record": record,
        "source": "StatsBomb WC 2018 + 2022 open data",
    }


def xg_summary(
    home_name: str,
    away_name: str,
    team_histories: dict[str, dict],
) -> dict:
    """Return a display-ready xG form breakdown for the /analysis endpoint."""
    home_hist = team_histories.get(home_name, {})
    away_hist = team_histories.get(away_name, {})

    home_xg = float(home_hist.get("xg_for_per_game", _DEFAULT_XG))
    away_xg = float(away_hist.get("xg_for_per_game", _DEFAULT_XG))
    home_xga = float(home_hist.get("xg_against_per_game", _DEFAULT_XG))
    away_xga = float(away_hist.get("xg_against_per_game", _DEFAULT_XG))
    home_games = int(home_hist.get("games", 0))
    away_games = int(away_hist.get("games", 0))

    attack_edge = home_xg - away_xg
    defense_edge = away_xga - home_xga  # positive = home defends better

    if abs(attack_edge) < 0.05:
        attack_label = "Even"
    elif attack_edge > 0:
        attack_label = f"{home_name} +{attack_edge:.2f}"
    else:
        attack_label = f"{away_name} +{-attack_edge:.2f}"

    if abs(defense_edge) < 0.05:
        defense_label = "Even"
    elif defense_edge > 0:
        defense_label = f"{home_name} +{defense_edge:.2f} xG conceded"
    else:
        defense_label = f"{away_name} +{-defense_edge:.2f} xG conceded"

    return {
        home_name: {
            "xg_per_game": round(home_xg, 2),
            "xg_against_per_game": round(home_xga, 2),
            "wc_games_in_dataset": home_games,
        },
        away_name: {
            "xg_per_game": round(away_xg, 2),
            "xg_against_per_game": round(away_xga, 2),
            "wc_games_in_dataset": away_games,
        },
        "attack_edge": attack_label,
        "defense_edge": defense_label,
    }
