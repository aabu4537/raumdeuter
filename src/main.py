from __future__ import annotations

from team import Team, Tournament
from research_modules import (
    ClimateAdaptationIndex,
    TournamentResilienceRating,
    PressurePerformanceIndex,
    TournamentDNAScore,
    LeadershipStabilityScore,
    SquadFatigueModel,
    InjuryImpactEstimator,
    ModuleCompositor,
)
from match_simulator import MatchSimulator

# ---------------------------------------------------------------------------
# Tournament context
# ---------------------------------------------------------------------------

WC_2026 = Tournament(
    name="FIFA World Cup",
    year=2026,
    host_country="USA/Canada/Mexico",
    host_latitude=39.0,
    host_longitude=-98.0,
    host_altitude_m=300,
    host_avg_temp_c=24.0,
    host_avg_humidity_pct=55.0,
)

# ---------------------------------------------------------------------------
# 32-team field with Elo ratings and home climate data
# (Elo approximate as of mid-2025; climate data representative of home cities)
# ---------------------------------------------------------------------------

TEAMS: list[Team] = [
    Team("Argentina",    2150, "ARG", "CONMEBOL", -34.6,  -58.4,   25, 17.0, 75.0),
    Team("France",       2100, "FRA", "UEFA",      48.9,    2.3,   35, 11.0, 80.0),
    Team("England",      2050, "ENG", "UEFA",      51.5,   -0.1,   11,  9.0, 82.0),
    Team("Brazil",       2040, "BRA", "CONMEBOL", -15.8,  -47.9, 1100, 25.0, 70.0),
    Team("Spain",        2030, "ESP", "UEFA",      40.4,   -3.7,  650, 14.0, 60.0),
    Team("Portugal",     2000, "POR", "UEFA",      38.7,   -9.1,  100, 16.0, 70.0),
    Team("Germany",      1990, "GER", "UEFA",      52.5,   13.4,   35,  9.0, 77.0),
    Team("Netherlands",  1980, "NED", "UEFA",      52.4,    4.9,    1,  9.0, 82.0),
    Team("Belgium",      1960, "BEL", "UEFA",      50.8,    4.4,  100,  9.0, 82.0),
    Team("Italy",        1950, "ITA", "UEFA",      41.9,   12.5,   21, 14.0, 72.0),
    Team("Croatia",      1930, "CRO", "UEFA",      45.8,   16.0,  120, 12.0, 67.0),
    Team("Morocco",      1900, "MAR", "CAF",       34.0,   -6.8,  540, 18.0, 65.0),
    Team("Uruguay",      1890, "URU", "CONMEBOL", -34.9,  -56.2,   43, 16.0, 70.0),
    Team("USA",          1880, "USA", "CONCACAF",  38.9,  -77.0,  125, 14.0, 60.0),
    Team("Mexico",       1870, "MEX", "CONCACAF",  19.4,  -99.1, 2240, 18.0, 55.0),
    Team("Colombia",     1860, "COL", "CONMEBOL",   4.7,  -74.1, 2625, 14.0, 65.0),
    Team("Senegal",      1850, "SEN", "CAF",       14.7,  -17.4,   22, 28.0, 62.0),
    Team("Japan",        1840, "JPN", "AFC",       35.7,  139.7,   40, 13.0, 73.0),
    Team("South Korea",  1820, "KOR", "AFC",       37.6,  127.0,   49, 12.0, 67.0),
    Team("Ecuador",      1810, "ECU", "CONMEBOL",  -0.2,  -78.5, 2850, 14.0, 72.0),
    Team("Switzerland",  1800, "SUI", "UEFA",      47.4,    8.5,  430,  7.0, 75.0),
    Team("Austria",      1790, "AUT", "UEFA",      48.2,   16.4,  171,  8.0, 78.0),
    Team("Denmark",      1780, "DEN", "UEFA",      55.7,   12.6,   34,  8.0, 82.0),
    Team("Australia",    1760, "AUS", "AFC",      -33.9,  151.2,   58, 17.0, 65.0),
    Team("Cameroon",     1740, "CMR", "CAF",        3.9,   11.5,  726, 25.0, 80.0),
    Team("Ghana",        1720, "GHA", "CAF",        5.6,   -0.2,   61, 27.0, 78.0),
    Team("Tunisia",      1710, "TUN", "CAF",       36.8,   10.2,  198, 19.0, 65.0),
    Team("Poland",       1700, "POL", "UEFA",      52.2,   21.0,  110,  8.0, 76.0),
    Team("Serbia",       1690, "SRB", "UEFA",      44.8,   20.5,  120, 11.0, 72.0),
    Team("Iran",         1680, "IRN", "AFC",       35.7,   51.4, 1191, 16.0, 40.0),
    Team("Canada",       1670, "CAN", "CONCACAF",  45.4,  -75.7,   70,  7.0, 70.0),
    Team("Saudi Arabia", 1650, "KSA", "AFC",       24.7,   46.7,  612, 26.0, 30.0),
]

# ---------------------------------------------------------------------------
# Historical data for research modules
# (In production this comes from PostgreSQL via research_scores table)
# ---------------------------------------------------------------------------

TEAM_HISTORIES: dict[str, dict] = {
    "Argentina": {
        "comeback_wins": 8, "conceded_first_matches": 12,
        "shootout_wins": 4, "shootouts": 6,
        "underdog_wins": 3, "underdog_matches": 5,
        "finish_round_deltas": [1, 0, 2, 1, 3],
        "coach_tenure_years": 4.0, "captain_caps": 180,
        "distinct_formations_per_tournament": 2, "win_rate_after_formation_change": 0.70,
        "avg_key_player_minutes_last_30_days": 260, "travel_km_last_30_days": 8000,
        "key_players_injured": 0, "avg_injured_player_importance": 0.0,
    },
    "France": {
        "comeback_wins": 7, "conceded_first_matches": 10,
        "shootout_wins": 3, "shootouts": 5,
        "underdog_wins": 4, "underdog_matches": 6,
        "finish_round_deltas": [1, 2, 0, 1],
        "coach_tenure_years": 3.0, "captain_caps": 120,
        "distinct_formations_per_tournament": 3, "win_rate_after_formation_change": 0.65,
        "avg_key_player_minutes_last_30_days": 280, "travel_km_last_30_days": 7000,
        "key_players_injured": 1, "avg_injured_player_importance": 0.4,
    },
    "Brazil": {
        "comeback_wins": 9, "conceded_first_matches": 14,
        "shootout_wins": 2, "shootouts": 6,
        "underdog_wins": 2, "underdog_matches": 4,
        "finish_round_deltas": [-1, 0, 1, -1, 0],
        "coach_tenure_years": 1.5, "captain_caps": 95,
        "distinct_formations_per_tournament": 2, "win_rate_after_formation_change": 0.55,
        "avg_key_player_minutes_last_30_days": 300, "travel_km_last_30_days": 12000,
        "key_players_injured": 0, "avg_injured_player_importance": 0.0,
    },
    "England": {
        "comeback_wins": 5, "conceded_first_matches": 9,
        "shootout_wins": 2, "shootouts": 7,
        "underdog_wins": 2, "underdog_matches": 4,
        "finish_round_deltas": [0, 1, 0, 1, 0],
        "coach_tenure_years": 2.5, "captain_caps": 110,
        "distinct_formations_per_tournament": 2, "win_rate_after_formation_change": 0.50,
        "avg_key_player_minutes_last_30_days": 270, "travel_km_last_30_days": 7000,
        "key_players_injured": 0, "avg_injured_player_importance": 0.0,
    },
}


# ---------------------------------------------------------------------------
# Demo runners
# ---------------------------------------------------------------------------

def demo_head_to_head() -> None:
    print("\n=== Head-to-Head: Argentina vs France (10,000 match simulations) ===\n")

    compositor = ModuleCompositor([
        ClimateAdaptationIndex(),
        TournamentResilienceRating(),
        TournamentDNAScore(),
        LeadershipStabilityScore(),
        SquadFatigueModel(),
        InjuryImpactEstimator(),
    ])
    match_sim = MatchSimulator()

    argentina = next(t for t in TEAMS if t.name == "Argentina")
    france = next(t for t in TEAMS if t.name == "France")

    arg_scores = compositor.compute_all(argentina, WC_2026, TEAM_HISTORIES.get("Argentina"))
    fra_scores = compositor.compute_all(france, WC_2026, TEAM_HISTORIES.get("France"))

    results: dict[str, int] = {"Argentina": 0, "France": 0, "Draw": 0}
    for _ in range(10_000):
        result = match_sim.simulate(argentina, france, arg_scores, fra_scores, knockout=False)
        key = result.winner.name if result.winner else "Draw"
        results[key] += 1

    total = 10_000
    print(f"  Argentina win : {results['Argentina'] / total:.1%}")
    print(f"  Draw          : {results['Draw'] / total:.1%}")
    print(f"  France win    : {results['France'] / total:.1%}")


def demo_module_breakdown() -> None:
    print("\n=== Module Score Breakdown: Top 4 Teams ===\n")

    compositor = ModuleCompositor([
        ClimateAdaptationIndex(),
        TournamentResilienceRating(),
        PressurePerformanceIndex(),
        TournamentDNAScore(),
        LeadershipStabilityScore(),
        SquadFatigueModel(),
        InjuryImpactEstimator(),
    ])

    top4 = [t for t in TEAMS if t.name in ("Argentina", "France", "England", "Brazil")]
    col_w = 28

    header = f"  {'Module':<{col_w}}" + "".join(f"{t.name:>14}" for t in top4)
    print(header)
    print("  " + "-" * (col_w + 14 * len(top4)))

    all_scores = {
        t.name: compositor.compute_all(t, WC_2026, TEAM_HISTORIES.get(t.name))
        for t in top4
    }

    module_names = list(next(iter(all_scores.values())).keys())
    for module in module_names:
        row = f"  {module:<{col_w}}"
        for team in top4:
            row += f"{all_scores[team.name][module]:>14.1f}"
        print(row)

    print("  " + "-" * (col_w + 14 * len(top4)))
    for team in top4:
        composite = compositor.composite_score(team, WC_2026, TEAM_HISTORIES.get(team.name))
        print(f"  {'composite':<{col_w}}{composite:>14.1f}" if team == top4[0]
              else f"  {'':<{col_w}}{composite:>14.1f}")

    print("\n  Composite scores:")
    for team in top4:
        composite = compositor.composite_score(team, WC_2026, TEAM_HISTORIES.get(team.name))
        print(f"    {team.name:<16} {composite:.1f}")


def demo_elo_vs_modules() -> None:
    print("\n=== Elo-only vs Module-adjusted Win Probability (Argentina vs Brazil) ===\n")

    argentina = next(t for t in TEAMS if t.name == "Argentina")
    brazil = next(t for t in TEAMS if t.name == "Brazil")
    match_sim = MatchSimulator()

    elo_p = match_sim.elo_win_probability(argentina, brazil)
    print(f"  Elo-only P(Argentina wins): {elo_p:.1%}")

    compositor = ModuleCompositor([
        ClimateAdaptationIndex(),
        TournamentResilienceRating(),
        TournamentDNAScore(),
        SquadFatigueModel(),
    ])
    arg_scores = compositor.compute_all(argentina, WC_2026, TEAM_HISTORIES.get("Argentina"))
    bra_scores = compositor.compute_all(brazil, WC_2026, TEAM_HISTORIES.get("Brazil"))

    wins = 0
    n = 10_000
    for _ in range(n):
        result = match_sim.simulate(argentina, brazil, arg_scores, bra_scores)
        if result.winner == argentina:
            wins += 1
    print(f"  Module-adjusted P(Argentina wins): {wins / n:.1%}")
    print(f"  Delta: {(wins / n) - elo_p:+.1%}")


if __name__ == "__main__":
    demo_head_to_head()
    demo_module_breakdown()
    demo_elo_vs_modules()
