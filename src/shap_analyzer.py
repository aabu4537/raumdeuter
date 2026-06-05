from __future__ import annotations

import numpy as np
import pandas as pd
import shap

from ml_model import XGBoostMatchPredictor, FeatureBuilder, MatchSample


class SHAPAnalyzer:
    """
    SHAP-based feature importance analysis for XGBoostMatchPredictor.

    Core research tool: answers which research modules genuinely drive
    predictions and which are noise layered on top of the Elo baseline.

    Uses TreeExplainer (exact, not approximate) since XGBoost is a tree model.
    SHAP values are additive: each feature's value is the contribution to the
    model output relative to the expected value (base rate).
    """

    def __init__(self, model: XGBoostMatchPredictor) -> None:
        if not model.is_trained:
            raise RuntimeError("Model must be trained before SHAP analysis")
        self.model = model
        self._explainer = shap.TreeExplainer(model._model)

    def explain_match(
        self,
        sample: MatchSample,
        outcome_class: str = "home_win",
    ) -> dict[str, float]:
        """
        SHAP values for a single match prediction.
        Positive value = feature pushed probability of outcome_class up.
        Negative value = feature pushed it down.
        """
        class_idx = self.model.OUTCOME_LABELS.index(outcome_class)
        X = FeatureBuilder.build(sample).reshape(1, -1)
        sv = self._explainer.shap_values(X)  # (1, n_features, n_classes)
        values = sv[0, :, class_idx]
        return dict(zip(self.model.feature_names_, values))

    def global_importance(self, samples: list[MatchSample]) -> pd.DataFrame:
        """
        Mean absolute SHAP values across all samples and all outcome classes.
        Higher = feature has more consistent directional impact on predictions.
        """
        X = FeatureBuilder.build_batch(samples)
        sv = self._explainer.shap_values(X)  # (n_samples, n_features, n_classes)
        mean_abs = np.abs(sv).mean(axis=(0, 2))  # average over samples and classes
        df = pd.DataFrame({
            "feature": self.model.feature_names_,
            "mean_abs_shap": mean_abs,
        }).sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)
        df["rank"] = range(1, len(df) + 1)
        return df

    def module_lift_table(self, samples: list[MatchSample]) -> pd.DataFrame:
        """
        Groups SHAP values by research module to show each module's total
        contribution vs the elo_diff baseline.

        This is the primary output for the research question:
        'Does Module X add lift beyond Elo?'
        """
        importance = self.global_importance(samples)
        total_shap = importance["mean_abs_shap"].sum()

        rows = []
        elo_shap = float(importance.loc[importance["feature"] == "elo_diff", "mean_abs_shap"].values[0])
        rows.append({
            "source": "elo_baseline",
            "total_shap": round(elo_shap, 4),
            "pct_of_total": round(elo_shap / total_shap * 100, 1),
            "verdict": "baseline",
        })

        for module in self.model.module_names:
            mask = importance["feature"].str.contains(module, regex=False)
            module_shap = float(importance.loc[mask, "mean_abs_shap"].sum())
            pct = module_shap / total_shap * 100
            verdict = "significant lift" if pct >= 5 else ("marginal" if pct >= 2 else "noise")
            rows.append({
                "source": module,
                "total_shap": round(module_shap, 4),
                "pct_of_total": round(pct, 1),
                "verdict": verdict,
            })

        return (
            pd.DataFrame(rows)
            .sort_values("total_shap", ascending=False)
            .reset_index(drop=True)
        )

    def plot_bar(self, samples: list[MatchSample], max_display: int = 20) -> None:
        """Bar chart of mean absolute SHAP values — requires matplotlib."""
        X = FeatureBuilder.build_batch(samples)
        sv = self._explainer.shap_values(X)  # (n_samples, n_features, n_classes)
        mean_shap = np.abs(sv).mean(axis=(0, 2))  # (n_features,)
        shap.summary_plot(
            mean_shap,
            X,
            feature_names=self.model.feature_names_,
            max_display=max_display,
            plot_type="bar",
        )
