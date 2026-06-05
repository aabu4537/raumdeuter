from __future__ import annotations
import math
import random
from dataclasses import dataclass

from scipy.stats import poisson

from team import Team

HOME_ADVANTAGE = 1.1   # neutral-site tournaments still favour nominal "home" side slightly
RHO = 0.1              # Dixon-Coles correction strength for low-scoring results
ELO_BASELINE = 1800    # Elo value that maps to LAMBDA_BASELINE goals per match
LAMBDA_BASELINE = 1.25 # average goals/match at baseline Elo; calibrated on WC data


@dataclass
class MatchResult:
    home_team: Team
    away_team: Team
    home_goals: int
    away_goals: int
    extra_time: bool = False
    penalties: bool = False

    @property
    def winner(self) -> Team | None:
        if self.home_goals > self.away_goals:
            return self.home_team
        if self.away_goals > self.home_goals:
            return self.away_team
        return None  # draw — only valid in group stage

    @property
    def is_draw(self) -> bool:
        return self.home_goals == self.away_goals

    def __str__(self) -> str:
        suffix = " (aet)" if self.extra_time and not self.penalties else (
            " (pen)" if self.penalties else ""
        )
        return (
            f"{self.home_team.name} {self.home_goals}–"
            f"{self.away_goals} {self.away_team.name}{suffix}"
        )


class MatchSimulator:
    """
    Dixon-Coles bivariate Poisson match simulator.

    Converts Elo ratings (optionally adjusted by research module composite scores)
    into Poisson goal-rate parameters λ (home) and μ (away), applies the
    Dixon-Coles low-score correction, then samples a final scoreline.

    For knockout matches, draws are resolved via extra time and then penalties.
    """

    def __init__(
        self,
        home_advantage: float = HOME_ADVANTAGE,
        rho: float = RHO,
        module_weight: float = 0.3,
    ) -> None:
        self.home_advantage = home_advantage
        self.rho = rho
        self.module_weight = module_weight

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def elo_win_probability(self, team_a: Team, team_b: Team) -> float:
        """Standard Elo expected-score formula — used for quick comparisons."""
        return 1 / (1 + 10 ** ((team_b.elo - team_a.elo) / 400))

    def simulate(
        self,
        home: Team,
        away: Team,
        home_module_scores: dict[str, float] | None = None,
        away_module_scores: dict[str, float] | None = None,
        knockout: bool = False,
    ) -> MatchResult:
        lam_home = self._team_lambda(home, home_module_scores) * self.home_advantage
        lam_away = self._team_lambda(away, away_module_scores)

        home_goals, away_goals = self._sample_dc_score(lam_home, lam_away)
        extra_time = False
        penalties = False

        if knockout and home_goals == away_goals:
            home_goals, away_goals, extra_time, penalties = self._resolve_knockout(
                lam_home, lam_away, home_goals, away_goals
            )

        return MatchResult(home, away, home_goals, away_goals, extra_time, penalties)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _team_lambda(self, team: Team, module_scores: dict[str, float] | None) -> float:
        base_lambda = math.exp((team.elo - ELO_BASELINE) / 500) * LAMBDA_BASELINE
        if not module_scores:
            return base_lambda
        module_avg = sum(module_scores.values()) / (len(module_scores) * 100)
        adjustment = 1 + (module_avg - 0.5) * self.module_weight
        return base_lambda * adjustment

    def _dc_correction(self, h: int, a: int, lam: float, mu: float) -> float:
        rho = self.rho
        if h == 0 and a == 0:
            return 1 - lam * mu * rho
        if h == 0 and a == 1:
            return 1 + lam * rho
        if h == 1 and a == 0:
            return 1 + mu * rho
        if h == 1 and a == 1:
            return 1 - rho
        return 1.0

    def _sample_dc_score(self, lam: float, mu: float, max_goals: int = 8) -> tuple[int, int]:
        probs: dict[tuple[int, int], float] = {}
        total = 0.0
        for h in range(max_goals + 1):
            for a in range(max_goals + 1):
                p = (
                    poisson.pmf(h, lam)
                    * poisson.pmf(a, mu)
                    * self._dc_correction(h, a, lam, mu)
                )
                probs[(h, a)] = p
                total += p

        r = random.random() * total
        cumulative = 0.0
        for score, p in probs.items():
            cumulative += p
            if r <= cumulative:
                return score
        return (0, 0)

    def _resolve_knockout(
        self,
        lam_home: float,
        lam_away: float,
        home_goals: int,
        away_goals: int,
    ) -> tuple[int, int, bool, bool]:
        # Extra time: 30 min ≈ 33% of a 90-min match rate
        et_home, et_away = self._sample_dc_score(lam_home * 0.33, lam_away * 0.33)
        home_goals += et_home
        away_goals += et_away
        if home_goals != away_goals:
            return home_goals, away_goals, True, False

        # Penalties: flat 50/50 at base; TRR module can skew this in future
        if random.random() < 0.5:
            return home_goals + 1, away_goals, True, True
        return home_goals, away_goals + 1, True, True
