from __future__ import annotations
import random
from dataclasses import dataclass

import numpy as np
from xgboost import XGBClassifier

from team import Team, Tournament
from research_modules import ModuleCompositor
from match_simulator import MatchSimulator

# Canonical module order — must stay consistent across training and inference
MODULE_NAMES = [
    "climate_adaptation",
    "tournament_resilience",
    "pressure_performance",
    "tournament_dna",
    "chaos_tolerance",
    "leadership_stability",
    "tactical_flexibility",
    "invisible_impact",
    "squad_fatigue",
    "injury_impact",
]


@dataclass
class MatchSample:
    """A single training or prediction sample for the XGBoost model."""
    home_elo: float
    away_elo: float
    home_module_scores: dict[str, float]
    away_module_scores: dict[str, float]
    outcome: int  # 1 = home win, 0 = draw, -1 = away win


class FeatureBuilder:
    """
    Converts a MatchSample into a flat feature vector.

    Feature layout (per match):
      - elo_diff                          : home Elo − away Elo (baseline signal)
      - home_{module}, away_{module},
        {module}_delta                    : per-module home score, away score, delta
      - home_composite, away_composite,
        composite_delta                   : weighted average across all modules

    The delta features (module_delta, composite_delta) are the most predictive
    because they encode relative advantage. The individual home/away values
    capture asymmetric effects (e.g. one team is great at penalties, the other
    is neutral — the delta alone misses the absolute level).
    """

    @staticmethod
    def feature_names(module_names: list[str] = MODULE_NAMES) -> list[str]:
        names = ["elo_diff"]
        for m in module_names:
            names += [f"home_{m}", f"away_{m}", f"{m}_delta"]
        names += ["home_composite", "away_composite", "composite_delta"]
        return names

    @staticmethod
    def build(sample: MatchSample) -> np.ndarray:
        home = sample.home_module_scores
        away = sample.away_module_scores
        module_names = list(home.keys()) or MODULE_NAMES

        features: list[float] = [sample.home_elo - sample.away_elo]
        for m in module_names:
            h, a = home.get(m, 50.0), away.get(m, 50.0)
            features += [h, a, h - a]

        home_comp = sum(home.values()) / max(len(home), 1)
        away_comp = sum(away.values()) / max(len(away), 1)
        features += [home_comp, away_comp, home_comp - away_comp]
        return np.array(features, dtype=np.float32)

    @staticmethod
    def build_batch(samples: list[MatchSample]) -> np.ndarray:
        return np.vstack([FeatureBuilder.build(s) for s in samples])


class XGBoostMatchPredictor:
    """
    XGBoost 3-class match outcome predictor (home win / draw / away win).

    Trained on module-enriched feature vectors. Use alongside SHAPAnalyzer
    to identify which research modules add measurable lift over Elo alone.

    NOTE on architecture:
      - Tournament simulation uses Dixon-Coles (needs scorelines, not just probs)
      - This model handles probability prediction and research — they're complementary
      - Future: use XGBoost probabilities to re-weight Dixon-Coles sampling
      - Single-match deep analysis (matchup head-to-head, tactical context) will
        plug in here as additional features in the feature vector
    """

    OUTCOME_MAP = {-1: 0, 0: 1, 1: 2}    # away win=0, draw=1, home win=2
    OUTCOME_LABELS = ["away_win", "draw", "home_win"]

    def __init__(
        self,
        module_names: list[str] | None = None,
        n_estimators: int = 200,
        max_depth: int = 4,
        learning_rate: float = 0.05,
    ) -> None:
        self.module_names = module_names or MODULE_NAMES
        self.feature_names_ = FeatureBuilder.feature_names(self.module_names)
        self._model = XGBClassifier(
            objective="multi:softprob",
            num_class=3,
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="mlogloss",
            random_state=42,
            verbosity=0,
        )
        self.is_trained = False

    def train(self, samples: list[MatchSample]) -> None:
        # Infer actual module names from training data so feature_names_ stays consistent
        actual_modules = list(samples[0].home_module_scores.keys())
        self.module_names = actual_modules
        self.feature_names_ = FeatureBuilder.feature_names(actual_modules)

        X = FeatureBuilder.build_batch(samples)
        y = np.array([self.OUTCOME_MAP[s.outcome] for s in samples])
        self._model.fit(X, y)
        self.is_trained = True

    def predict_proba(
        self,
        home_elo: float,
        away_elo: float,
        home_module_scores: dict[str, float],
        away_module_scores: dict[str, float],
    ) -> dict[str, float]:
        if not self.is_trained:
            raise RuntimeError("Call train() before predict_proba()")
        sample = MatchSample(home_elo, away_elo, home_module_scores, away_module_scores, 0)
        X = FeatureBuilder.build(sample).reshape(1, -1)
        probs = self._model.predict_proba(X)[0]
        return dict(zip(self.OUTCOME_LABELS, map(float, probs)))

    def feature_importance(self) -> dict[str, float]:
        if not self.is_trained:
            raise RuntimeError("Call train() before feature_importance()")
        return dict(zip(self.feature_names_, self._model.feature_importances_))

    def __repr__(self) -> str:
        status = "trained" if self.is_trained else "untrained"
        return f"XGBoostMatchPredictor({status}, modules={len(self.module_names)})"


def generate_training_data(
    teams: list[Team],
    tournament: Tournament,
    compositor: ModuleCompositor,
    team_histories: dict[str, dict] | None = None,
    n_samples: int = 5_000,
) -> list[MatchSample]:
    """
    Generate synthetic training samples by running Dixon-Coles simulations.

    Module scores are computed from team attributes + history; match outcomes
    come from the Dixon-Coles model. XGBoost then learns which features
    best predict those outcomes — SHAP reveals which modules it relies on.

    Synthetic data caveat: this validates that XGBoost recovers the same signal
    encoded in our module formulas. Real historical WC match data should replace
    this once the DB ingestion pipeline is wired up.
    """
    histories = team_histories or {}
    match_sim = MatchSimulator()
    samples: list[MatchSample] = []

    for _ in range(n_samples):
        home, away = random.sample(teams, 2)
        home_scores = compositor.compute_all(home, tournament, histories.get(home.name))
        away_scores = compositor.compute_all(away, tournament, histories.get(away.name))
        result = match_sim.simulate(home, away, home_scores, away_scores, knockout=False)

        if result.winner == home:
            outcome = 1
        elif result.winner == away:
            outcome = -1
        else:
            outcome = 0

        samples.append(MatchSample(home.elo, away.elo, home_scores, away_scores, outcome))

    return samples
