"""Ratings computation scaffold: StatsBomb events -> percentile ratings.

Documented stub. The aggregation shape is real; wire `load_events` to statsbombpy
and `persist` to PostgreSQL to make it live. Output conforms to ratings.schema.json.
"""
from dataclasses import dataclass


@dataclass
class PlayerAggregates:
    player: str
    team: str
    pos: str
    minutes: int
    pressures_p90: float
    pressure_regains_p90: float
    counterpressures_p90: float
    npxg_p90: float
    xa_p90: float
    progressive_actions_p90: float
    box_receptions_p90: float
    defensive_actions_p90: float


def possession_adjust(value_p90: float, team_possession: float) -> float:
    """Normalize defensive volume stats to a 50% possession baseline."""
    opponent_share = max(1e-6, 1.0 - team_possession)
    return value_p90 * (0.5 / opponent_share)


def to_percentile(value: float, position_pool: list[float]) -> int:
    """Rating = percentile within position group (min 1000 minutes), scaled 0-99."""
    below = sum(1 for v in position_pool if v < value)
    return round(99 * below / max(1, len(position_pool) - 1))


def compute_off_ball(agg: PlayerAggregates, pool: dict) -> dict:
    return {
        "prs": to_percentile(agg.pressures_p90, pool["pressures"]),
        "rgn": to_percentile(agg.pressure_regains_p90 + agg.counterpressures_p90, pool["regains"]),
        "mov": to_percentile(agg.box_receptions_p90, pool["receptions"]),
        "cov": to_percentile(agg.defensive_actions_p90, pool["def_actions"]),
    }


def compute_on_ball(agg: PlayerAggregates, pool: dict) -> dict:
    return {
        "fin": to_percentile(agg.npxg_p90, pool["npxg"]),
        "cre": to_percentile(agg.xa_p90, pool["xa"]),
        "prg": to_percentile(agg.progressive_actions_p90, pool["progressive"]),
    }


if __name__ == "__main__":
    print("Scaffold: wire load_events() to statsbombpy and persist() to PostgreSQL.")
