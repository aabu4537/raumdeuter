from __future__ import annotations
from abc import ABC, abstractmethod
import math

from team import Team, Tournament


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


class ResearchModule(ABC):
    """
    Abstract base for all research scoring modules.

    Each module encodes one hypothesis about what drives World Cup success
    beyond Elo. Subclasses implement compute() returning a score in [0, 100].
    """

    name: str
    weight: float = 1.0

    @abstractmethod
    def compute(
        self,
        team: Team,
        tournament: Tournament,
        history: dict | None = None,
    ) -> float:
        """Return a score in [0, 100]. Higher = better outcome for this team."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(weight={self.weight})"


class ClimateAdaptationIndex(ResearchModule):
    """Teams playing far from their home climate underperform relative to Elo."""

    name = "climate_adaptation"
    weight = 1.0

    def compute(self, team: Team, tournament: Tournament, history: dict | None = None) -> float:
        temp_delta = abs(team.home_avg_temp_c - tournament.host_avg_temp_c)
        altitude_delta = abs(team.home_altitude_m - tournament.host_altitude_m)
        travel_km = _haversine_km(
            team.home_latitude, team.home_longitude,
            tournament.host_latitude, tournament.host_longitude,
        )
        raw = 100 - (temp_delta * 2.5 + altitude_delta * 0.01 + travel_km * 0.005)
        return _clamp(raw)


class TournamentResilienceRating(ResearchModule):
    """Comeback wins, penalty shootout record, and underdog victories predict clutch performance."""

    name = "tournament_resilience"
    weight = 1.0

    def compute(self, team: Team, tournament: Tournament, history: dict | None = None) -> float:
        h = history or {}
        comeback_rate = h.get("comeback_wins", 0) / max(h.get("conceded_first_matches", 1), 1)
        shootout_rate = h.get("shootout_wins", 0) / max(h.get("shootouts", 1), 1)
        underdog_rate = h.get("underdog_wins", 0) / max(h.get("underdog_matches", 1), 1)
        raw = comeback_rate * 40 + shootout_rate * 35 + underdog_rate * 25
        return _clamp(raw)


class PressurePerformanceIndex(ResearchModule):
    """Teams with high-pressure club environments handle tournament pressure better."""

    name = "pressure_performance"
    weight = 1.0

    def compute(self, team: Team, tournament: Tournament, history: dict | None = None) -> float:
        h = history or {}
        ucl_rate = h.get("ucl_knockout_wins", 0) / max(h.get("ucl_knockout_matches", 1), 1)
        late_goal_rate = h.get("goals_after_80min", 0) / max(h.get("total_goals", 1), 1)
        behind_win_rate = h.get("wins_when_behind", 0) / max(h.get("matches_when_behind", 1), 1)
        raw = ucl_rate * 40 + late_goal_rate * 30 + behind_win_rate * 30
        return _clamp(raw)


class TournamentDNAScore(ResearchModule):
    """Captures teams that systematically outperform their pre-tournament Elo expectation."""

    name = "tournament_dna"
    weight = 1.0

    def compute(self, team: Team, tournament: Tournament, history: dict | None = None) -> float:
        h = history or {}
        deltas = h.get("finish_round_deltas", [])  # positive = outperformed Elo expectation
        if not deltas:
            return 50.0  # neutral prior when no history available
        mean_delta = sum(deltas) / len(deltas)
        return _clamp(mean_delta * 10 + 50)


class ChaosTolerance(ResearchModule):
    """Teams that maintain cohesion after red cards, injuries, and going behind."""

    name = "chaos_tolerance"
    weight = 1.0

    def compute(self, team: Team, tournament: Tournament, history: dict | None = None) -> float:
        h = history or {}
        ten_man_pct = h.get("ten_man_points_pct", 0.5)
        red_recovery = h.get("red_card_recovery_rate", 0.5)
        sub_impact = h.get("avg_sub_xg_improvement", 0.0)
        raw = ten_man_pct * 40 + red_recovery * 35 + _clamp(sub_impact * 100, 0, 25)
        return _clamp(raw)


class LeadershipStabilityScore(ResearchModule):
    """Experienced captains and stable coaching tenures correlate with overperformance."""

    name = "leadership_stability"
    weight = 1.0

    def compute(self, team: Team, tournament: Tournament, history: dict | None = None) -> float:
        h = history or {}
        tenure_years = h.get("coach_tenure_years", 1.0)
        captain_caps = h.get("captain_caps", 50)
        # Each component maxes out at 50pts (4+ years tenure, 150+ caps)
        coaching_score = _clamp(tenure_years / 4 * 50)
        captain_score = _clamp(captain_caps / 150 * 50)
        return _clamp(coaching_score + captain_score)


class TacticalFlexibilityIndex(ResearchModule):
    """Teams that shift formations mid-tournament adapt to bracket variance."""

    name = "tactical_flexibility"
    weight = 1.0

    def compute(self, team: Team, tournament: Tournament, history: dict | None = None) -> float:
        h = history or {}
        formations_used = h.get("distinct_formations_per_tournament", 1)
        win_rate_after_switch = h.get("win_rate_after_formation_change", 0.5)
        flex_score = _clamp(formations_used / 4 * 50)
        adapt_score = win_rate_after_switch * 50
        return _clamp(flex_score + adapt_score)


class InvisibleImpactScore(ResearchModule):
    """Off-ball contributions (pressing, recoveries, space creation) not in goals or assists."""

    name = "invisible_impact"
    weight = 0.8  # down-weighted — hardest to measure reliably

    def compute(self, team: Team, tournament: Tournament, history: dict | None = None) -> float:
        h = history or {}
        pressing = h.get("pressures_per_90", 20.0)
        recoveries = h.get("ball_recoveries_per_90", 8.0)
        progressive = h.get("progressive_actions_per_90", 10.0)
        raw = (
            _clamp(pressing / 30 * 40) +
            _clamp(recoveries / 12 * 30) +
            _clamp(progressive / 15 * 30)
        )
        return _clamp(raw)


class SquadFatigueModel(ResearchModule):
    """Players entering a tournament with high club-season workload carry elevated injury risk."""

    name = "squad_fatigue"
    weight = 1.0

    def compute(self, team: Team, tournament: Tournament, history: dict | None = None) -> float:
        h = history or {}
        avg_minutes = h.get("avg_key_player_minutes_last_30_days", 270)
        travel_km = h.get("travel_km_last_30_days", 5000)
        fatigue_penalty = _clamp(avg_minutes / 450 * 60) + _clamp(travel_km / 20000 * 40)
        return _clamp(100 - fatigue_penalty)


class InjuryImpactEstimator(ResearchModule):
    """Estimated performance drop from key player absences entering the tournament."""

    name = "injury_impact"
    weight = 1.0

    def compute(self, team: Team, tournament: Tournament, history: dict | None = None) -> float:
        h = history or {}
        injured = h.get("key_players_injured", 0)
        importance = h.get("avg_injured_player_importance", 0.0)  # 0–1
        impact = injured * importance * 20
        return _clamp(100 - impact)


ALL_MODULES: list[type[ResearchModule]] = [
    ClimateAdaptationIndex,
    TournamentResilienceRating,
    PressurePerformanceIndex,
    TournamentDNAScore,
    ChaosTolerance,
    LeadershipStabilityScore,
    TacticalFlexibilityIndex,
    InvisibleImpactScore,
    SquadFatigueModel,
    InjuryImpactEstimator,
]


class ModuleCompositor:
    """Aggregates enabled research module scores into per-team composite scores."""

    def __init__(self, modules: list[ResearchModule]) -> None:
        self.modules = modules

    def compute_all(
        self,
        team: Team,
        tournament: Tournament,
        history: dict | None = None,
    ) -> dict[str, float]:
        return {m.name: m.compute(team, tournament, history) for m in self.modules}

    def composite_score(
        self,
        team: Team,
        tournament: Tournament,
        history: dict | None = None,
    ) -> float:
        if not self.modules:
            return 50.0
        scores = self.compute_all(team, tournament, history)
        total_weight = sum(m.weight for m in self.modules)
        weighted = sum(scores[m.name] * m.weight for m in self.modules)
        return weighted / total_weight

    def __repr__(self) -> str:
        return f"ModuleCompositor(modules={[m.name for m in self.modules]})"
