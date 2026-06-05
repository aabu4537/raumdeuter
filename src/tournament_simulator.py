from __future__ import annotations
import random
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from multiprocessing import cpu_count

from team import Team, Tournament
from match_simulator import MatchSimulator
from research_modules import ModuleCompositor


@dataclass
class GroupStanding:
    team: Team
    points: int = 0
    goal_diff: int = 0
    goals_scored: int = 0

    def __lt__(self, other: GroupStanding) -> bool:
        if self.points != other.points:
            return self.points > other.points
        if self.goal_diff != other.goal_diff:
            return self.goal_diff > other.goal_diff
        return self.goals_scored > other.goals_scored


@dataclass
class SimulationResult:
    champion_counts: dict[str, int] = field(default_factory=dict)
    finalist_counts: dict[str, int] = field(default_factory=dict)
    semifinalist_counts: dict[str, int] = field(default_factory=dict)
    n_simulations: int = 0

    def win_probability(self, team_name: str) -> float:
        return self.champion_counts.get(team_name, 0) / max(self.n_simulations, 1)

    def finalist_probability(self, team_name: str) -> float:
        return self.finalist_counts.get(team_name, 0) / max(self.n_simulations, 1)

    def semifinalist_probability(self, team_name: str) -> float:
        return self.semifinalist_counts.get(team_name, 0) / max(self.n_simulations, 1)

    def top_n(self, n: int = 8) -> list[tuple[str, float]]:
        ranked = sorted(self.champion_counts.items(), key=lambda x: x[1], reverse=True)
        return [(name, count / self.n_simulations) for name, count in ranked[:n]]

    @classmethod
    def aggregate(cls, results: list[SimulationResult]) -> SimulationResult:
        combined = cls(n_simulations=sum(r.n_simulations for r in results))
        for r in results:
            for name, count in r.champion_counts.items():
                combined.champion_counts[name] = combined.champion_counts.get(name, 0) + count
            for name, count in r.finalist_counts.items():
                combined.finalist_counts[name] = combined.finalist_counts.get(name, 0) + count
            for name, count in r.semifinalist_counts.items():
                combined.semifinalist_counts[name] = combined.semifinalist_counts.get(name, 0) + count
        return combined


class TournamentSimulator:
    """
    Monte Carlo FIFA World Cup bracket simulator.

    Draws 32 teams into 8 groups of 4, runs round-robin group stages to determine
    16 knockout qualifiers, then simulates R16 → QF → SF → Final.

    Module scores are pre-computed once and reused across all n_simulations,
    so the expensive research module computation scales O(n_teams), not O(n_sims).
    """

    N_GROUPS = 8
    TEAMS_PER_GROUP = 4

    def __init__(
        self,
        match_simulator: MatchSimulator | None = None,
        compositor: ModuleCompositor | None = None,
        team_histories: dict[str, dict] | None = None,
    ) -> None:
        self.match_sim = match_simulator or MatchSimulator()
        self.compositor = compositor
        self.team_histories = team_histories or {}

    def run(
        self,
        tournament: Tournament,
        teams: list[Team],
        n_simulations: int = 10_000,
        parallel: bool = True,
    ) -> SimulationResult:
        if len(teams) != 32:
            raise ValueError(f"Expected 32 teams, got {len(teams)}")

        module_scores = self._precompute_module_scores(teams, tournament)

        if parallel and n_simulations >= 1000:
            return self._run_parallel(teams, module_scores, n_simulations)
        return self._run_serial(teams, module_scores, n_simulations)

    # ------------------------------------------------------------------
    # Score pre-computation
    # ------------------------------------------------------------------

    def _precompute_module_scores(
        self, teams: list[Team], tournament: Tournament
    ) -> dict[str, dict[str, float]]:
        if not self.compositor:
            return {}
        return {
            team.name: self.compositor.compute_all(
                team, tournament, self.team_histories.get(team.name)
            )
            for team in teams
        }

    # ------------------------------------------------------------------
    # Execution strategies
    # ------------------------------------------------------------------

    def _run_serial(
        self,
        teams: list[Team],
        module_scores: dict[str, dict[str, float]],
        n: int,
    ) -> SimulationResult:
        result = SimulationResult(n_simulations=n)
        for _ in range(n):
            champion, finalists, semi_finalists = self._single_simulation(
                teams, module_scores
            )
            result.champion_counts[champion.name] = result.champion_counts.get(champion.name, 0) + 1
            for t in finalists:
                result.finalist_counts[t.name] = result.finalist_counts.get(t.name, 0) + 1
            for t in semi_finalists:
                result.semifinalist_counts[t.name] = result.semifinalist_counts.get(t.name, 0) + 1
        return result

    def _run_parallel(
        self,
        teams: list[Team],
        module_scores: dict[str, dict[str, float]],
        n: int,
    ) -> SimulationResult:
        workers = min(cpu_count(), 8)
        chunks = [n // workers] * workers
        chunks[-1] += n - sum(chunks)

        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = [
                pool.submit(_parallel_worker, teams, module_scores, self.match_sim, c)
                for c in chunks
            ]
            partial_results = [f.result() for f in as_completed(futures)]

        return SimulationResult.aggregate(partial_results)

    # ------------------------------------------------------------------
    # Single tournament simulation
    # ------------------------------------------------------------------

    def _single_simulation(
        self,
        teams: list[Team],
        module_scores: dict[str, dict[str, float]],
    ) -> tuple[Team, list[Team], list[Team]]:
        qualifiers: list[Team] = []
        for group in self._make_groups(teams):
            qualifiers.extend(self._simulate_group(group, module_scores))

        random.shuffle(qualifiers)
        r16_winners = self._simulate_knockout_round(qualifiers, module_scores)
        qf_winners = self._simulate_knockout_round(r16_winners, module_scores)
        sf_winners = self._simulate_knockout_round(qf_winners, module_scores)  # finalists

        final = self.match_sim.simulate(
            sf_winners[0], sf_winners[1],
            module_scores.get(sf_winners[0].name),
            module_scores.get(sf_winners[1].name),
            knockout=True,
        )
        champion = final.winner or sf_winners[0]  # guard — winner is always set in knockout

        return champion, sf_winners, qf_winners

    def _make_groups(self, teams: list[Team]) -> list[list[Team]]:
        shuffled = teams[:]
        random.shuffle(shuffled)
        return [
            shuffled[i * self.TEAMS_PER_GROUP:(i + 1) * self.TEAMS_PER_GROUP]
            for i in range(self.N_GROUPS)
        ]

    def _simulate_group(
        self,
        group: list[Team],
        module_scores: dict[str, dict[str, float]],
    ) -> list[Team]:
        standings = {t: GroupStanding(t) for t in group}
        pairs = [(group[i], group[j]) for i in range(4) for j in range(i + 1, 4)]

        for home, away in pairs:
            result = self.match_sim.simulate(
                home, away,
                module_scores.get(home.name),
                module_scores.get(away.name),
                knockout=False,
            )
            if result.winner == home:
                standings[home].points += 3
            elif result.winner == away:
                standings[away].points += 3
            else:
                standings[home].points += 1
                standings[away].points += 1

            gd = result.home_goals - result.away_goals
            standings[home].goal_diff += gd
            standings[away].goal_diff -= gd
            standings[home].goals_scored += result.home_goals
            standings[away].goals_scored += result.away_goals

        return [s.team for s in sorted(standings.values())[:2]]

    def _simulate_knockout_round(
        self,
        teams: list[Team],
        module_scores: dict[str, dict[str, float]],
    ) -> list[Team]:
        winners: list[Team] = []
        for i in range(0, len(teams), 2):
            result = self.match_sim.simulate(
                teams[i], teams[i + 1],
                module_scores.get(teams[i].name),
                module_scores.get(teams[i + 1].name),
                knockout=True,
            )
            winners.append(result.winner or teams[i])
        return winners


def _parallel_worker(
    teams: list[Team],
    module_scores: dict[str, dict[str, float]],
    match_sim: MatchSimulator,
    n: int,
) -> SimulationResult:
    """Module-level function required for ProcessPoolExecutor pickling."""
    sim = TournamentSimulator(match_simulator=match_sim)
    return sim._run_serial(teams, module_scores, n)
