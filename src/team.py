from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Team:
    name: str
    elo: float
    fifa_code: str = ""
    confederation: str = ""
    home_latitude: float = 0.0
    home_longitude: float = 0.0
    home_altitude_m: int = 0
    home_avg_temp_c: float = 20.0
    home_avg_humidity_pct: float = 60.0

    def __str__(self) -> str:
        return f"{self.name} ({self.elo:.0f})"

    def __repr__(self) -> str:
        return f"Team(name={self.name!r}, elo={self.elo})"

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Team) and self.name == other.name


@dataclass
class Tournament:
    name: str
    year: int
    host_country: str
    host_latitude: float = 0.0
    host_longitude: float = 0.0
    host_altitude_m: int = 0
    host_avg_temp_c: float = 25.0
    host_avg_humidity_pct: float = 65.0

    def __str__(self) -> str:
        return f"{self.name} {self.year} ({self.host_country})"
