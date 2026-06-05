from __future__ import annotations

from team import Team, Tournament
from data_ingestion import load_team_histories
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
from ml_model import XGBoostMatchPredictor, generate_training_data
from shap_analyzer import SHAPAnalyzer
from validation import ModelValidator

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
# Historical data for research modules — sourced from StatsBomb open WC data.
# Cached to data/team_histories.json after the first run.
# ---------------------------------------------------------------------------

TEAM_HISTORIES: dict[str, dict] = load_team_histories()


# ---------------------------------------------------------------------------
# Team picker
# ---------------------------------------------------------------------------

def pick_teams() -> tuple[Team, Team]:
    print("\n" + "=" * 50)
    print("  RAUMDEUTER — Head-to-Head Predictor")
    print("=" * 50)
    print("\n  Available teams:\n")
    for i, team in enumerate(TEAMS, 1):
        print(f"  {i:>2}. {team.name:<16} (Elo {team.elo:.0f})")

    def pick(prompt: str, exclude: Team | None = None) -> Team:
        while True:
            raw = input(f"\n{prompt}").strip()
            # Accept number
            if raw.isdigit():
                idx = int(raw) - 1
                if 0 <= idx < len(TEAMS):
                    team = TEAMS[idx]
                    if exclude and team == exclude:
                        print("  Pick a different team.")
                        continue
                    return team
            # Accept partial name (case-insensitive)
            matches = [t for t in TEAMS if raw.lower() in t.name.lower()]
            if len(matches) == 1:
                if exclude and matches[0] == exclude:
                    print("  Pick a different team.")
                    continue
                return matches[0]
            if len(matches) > 1:
                print(f"  Multiple matches: {', '.join(t.name for t in matches)}. Be more specific.")
                continue
            print("  Team not found. Try a number from the list or part of the name.")

    team_a = pick("  Select home team (number or name): ")
    print(f"  → {team_a.name} selected.")
    team_b = pick("  Select away team (number or name): ", exclude=team_a)
    print(f"  → {team_b.name} selected.")
    return team_a, team_b


# ---------------------------------------------------------------------------
# Analysis runners
# ---------------------------------------------------------------------------

_COMPOSITOR = ModuleCompositor([
    ClimateAdaptationIndex(),
    TournamentResilienceRating(),
    PressurePerformanceIndex(),
    TournamentDNAScore(),
    LeadershipStabilityScore(),
    SquadFatigueModel(),
    InjuryImpactEstimator(),
])


def run_head_to_head(team_a: Team, team_b: Team) -> None:
    print(f"\n=== Head-to-Head: {team_a.name} vs {team_b.name} (2,000 simulations) ===\n")

    match_sim = MatchSimulator()
    a_scores = _COMPOSITOR.compute_all(team_a, WC_2026, TEAM_HISTORIES.get(team_a.name))
    b_scores = _COMPOSITOR.compute_all(team_b, WC_2026, TEAM_HISTORIES.get(team_b.name))

    counts: dict[str, int] = {team_a.name: 0, team_b.name: 0, "Draw": 0}
    for _ in range(2_000):
        result = match_sim.simulate(team_a, team_b, a_scores, b_scores, knockout=False)
        key = result.winner.name if result.winner else "Draw"
        counts[key] += 1

    total = 2_000
    elo_p = match_sim.elo_win_probability(team_a, team_b)
    print(f"  {team_a.name} win  : {counts[team_a.name] / total:.1%}  (Elo-only: {elo_p:.1%})")
    print(f"  Draw         : {counts['Draw'] / total:.1%}")
    print(f"  {team_b.name} win  : {counts[team_b.name] / total:.1%}  (Elo-only: {1 - elo_p:.1%})")
    print(f"\n  Module delta vs Elo: {(counts[team_a.name] / total) - elo_p:+.1%} for {team_a.name}")


def run_module_breakdown(team_a: Team, team_b: Team) -> None:
    print(f"\n=== Module Score Breakdown: {team_a.name} vs {team_b.name} ===\n")

    teams = [team_a, team_b]
    col_w = 28
    header = f"  {'Module':<{col_w}}" + "".join(f"{t.name:>16}" for t in teams)
    print(header)
    print("  " + "-" * (col_w + 16 * len(teams)))

    all_scores = {
        t.name: _COMPOSITOR.compute_all(t, WC_2026, TEAM_HISTORIES.get(t.name))
        for t in teams
    }

    for module in list(all_scores[team_a.name].keys()):
        row = f"  {module:<{col_w}}"
        for t in teams:
            row += f"{all_scores[t.name][module]:>16.1f}"
        print(row)

    print("  " + "-" * (col_w + 16 * len(teams)))
    row = f"  {'composite':<{col_w}}"
    for t in teams:
        composite = _COMPOSITOR.composite_score(t, WC_2026, TEAM_HISTORIES.get(t.name))
        row += f"{composite:>16.1f}"
    print(row)


def run_xgboost_prediction(team_a: Team, team_b: Team) -> None:
    print(f"\n=== XGBoost Prediction: {team_a.name} vs {team_b.name} ===\n")

    print("  Training XGBoost on 2,000 simulated matches...")
    samples = generate_training_data(TEAMS, WC_2026, _COMPOSITOR, TEAM_HISTORIES, n_samples=2_000)
    model = XGBoostMatchPredictor()
    model.train(samples)

    a_scores = _COMPOSITOR.compute_all(team_a, WC_2026, TEAM_HISTORIES.get(team_a.name))
    b_scores = _COMPOSITOR.compute_all(team_b, WC_2026, TEAM_HISTORIES.get(team_b.name))
    probs = model.predict_proba(team_a.elo, team_b.elo, a_scores, b_scores)

    print(f"\n  {'Outcome':<14} {'Probability':>12}")
    print("  " + "-" * 28)
    labels = {
        "home_win": f"{team_a.name} win",
        "draw": "Draw",
        "away_win": f"{team_b.name} win",
    }
    for key, label in labels.items():
        print(f"  {label:<14} {probs[key]:>11.1%}")

    analyzer = SHAPAnalyzer(model)
    lift = analyzer.module_lift_table(samples)
    print(f"\n  Top contributing factors (SHAP):")
    for _, row in lift[lift["verdict"] != "noise"].iterrows():
        print(f"    {row['source']:<28} {row['pct_of_total']:>5.1f}%  {row['verdict']}")


if __name__ == "__main__":
    team_a, team_b = pick_teams()
    run_head_to_head(team_a, team_b)
    run_module_breakdown(team_a, team_b)
    run_xgboost_prediction(team_a, team_b)
