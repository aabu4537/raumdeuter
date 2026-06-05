from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold

from team import Team, Tournament
from research_modules import (
    ModuleCompositor,
    ResearchModule,
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
)
from ml_model import XGBoostMatchPredictor, MatchSample, FeatureBuilder, generate_training_data


def brier_score(probabilities: list[float], outcomes: list[int]) -> float:
    """
    Brier score for binary P(home win).
    Lower = better. Naive baseline (always predict 0.5) = 0.25.
    """
    return float(np.mean([(p - o) ** 2 for p, o in zip(probabilities, outcomes)]))


def log_loss(probabilities: list[float], outcomes: list[int], eps: float = 1e-7) -> float:
    losses = [
        -o * np.log(max(p, eps)) - (1 - o) * np.log(max(1 - p, eps))
        for p, o in zip(probabilities, outcomes)
    ]
    return float(np.mean(losses))


class ModelValidator:
    """
    K-fold cross-validation comparing module configurations by Brier Score.

    Answers the core research question: does adding Module X improve
    calibrated probability estimates over the Elo-only baseline?

    Standard module configs to compare are available via default_configs().
    """

    def __init__(
        self,
        teams: list[Team],
        tournament: Tournament,
        team_histories: dict[str, dict] | None = None,
        n_samples: int = 5_000,
        n_folds: int = 5,
    ) -> None:
        self.teams = teams
        self.tournament = tournament
        self.team_histories = team_histories or {}
        self.n_samples = n_samples
        self.n_folds = n_folds

    def compare_configs(
        self,
        configs: dict[str, list[ResearchModule]],
        verbose: bool = True,
    ) -> pd.DataFrame:
        """
        Run k-fold CV for each module config. Returns a ranked DataFrame.
        Lower Brier Score = better calibrated probabilities.
        """
        if verbose:
            print(f"\n  {'Config':<32} {'Modules':>7}  {'Brier':>7}  {'LogLoss':>8}")
            print("  " + "-" * 60)

        rows = []
        for name, modules in configs.items():
            compositor = ModuleCompositor(modules)
            samples = generate_training_data(
                self.teams, self.tournament, compositor,
                self.team_histories, self.n_samples,
            )
            brier, ll = self._cross_validate(samples)
            rows.append({
                "config": name,
                "n_modules": len(modules),
                "brier_score": round(brier, 4),
                "log_loss": round(ll, 4),
            })
            if verbose:
                print(f"  {name:<32} {len(modules):>7}  {brier:>7.4f}  {ll:>8.4f}")

        df = pd.DataFrame(rows).sort_values("brier_score").reset_index(drop=True)
        df["brier_vs_baseline"] = (df["brier_score"] - df.loc[df["config"] == "elo_only", "brier_score"].values[0]).round(4)
        return df

    def _cross_validate(self, samples: list[MatchSample]) -> tuple[float, float]:
        kf = KFold(n_splits=self.n_folds, shuffle=True, random_state=42)
        brier_scores, log_losses = [], []

        for train_idx, val_idx in kf.split(samples):
            train = [samples[i] for i in train_idx]
            val = [samples[i] for i in val_idx]

            model = XGBoostMatchPredictor()
            model.train(train)

            probs, outcomes = [], []
            for s in val:
                p = model.predict_proba(
                    s.home_elo, s.away_elo,
                    s.home_module_scores, s.away_module_scores,
                )
                probs.append(p["home_win"])
                outcomes.append(1 if s.outcome == 1 else 0)

            brier_scores.append(brier_score(probs, outcomes))
            log_losses.append(log_loss(probs, outcomes))

        return float(np.mean(brier_scores)), float(np.mean(log_losses))

    @staticmethod
    def default_configs() -> dict[str, list[ResearchModule]]:
        """
        Standard A/B configs for module lift testing.
        Add new module combos here as hypotheses to test.
        """
        return {
            "elo_only": [],
            "elo_climate": [ClimateAdaptationIndex()],
            "elo_resilience": [TournamentResilienceRating()],
            "elo_dna": [TournamentDNAScore()],
            "elo_fatigue": [SquadFatigueModel()],
            "elo_climate_resilience": [ClimateAdaptationIndex(), TournamentResilienceRating()],
            "elo_climate_resilience_dna": [
                ClimateAdaptationIndex(), TournamentResilienceRating(), TournamentDNAScore()
            ],
            "full_10_modules": [
                ClimateAdaptationIndex(), TournamentResilienceRating(),
                PressurePerformanceIndex(), TournamentDNAScore(), ChaosTolerance(),
                LeadershipStabilityScore(), TacticalFlexibilityIndex(),
                InvisibleImpactScore(), SquadFatigueModel(), InjuryImpactEstimator(),
            ],
        }
