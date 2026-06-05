"""
Fetch new WC results, update Elos, and push a phone notification via ntfy.

Run manually:
  FD_API_KEY=<key> NTFY_TOPIC=<topic> python src/notify.py

Exits 0 silently when there are no new results (safe for cron).
"""
from __future__ import annotations

import os
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import httpx

from live_ingestion import fetch_and_update, load_live_elos
from main import TEAMS, WC_2026, TEAM_HISTORIES
from tournament_simulator import TournamentSimulator

BASE_ELOS = {t.name: t.elo for t in TEAMS}


def projected_winners(n: int = 500) -> list[tuple[str, float]]:
    live_elos = load_live_elos(BASE_ELOS)
    updated_teams = [replace(t, elo=live_elos.get(t.name, t.elo)) for t in TEAMS]
    sim = TournamentSimulator(team_histories=TEAM_HISTORIES)
    result = sim.run(WC_2026, updated_teams, n_simulations=n, parallel=False)
    return result.top_n(5)


def send_notification(message: str, topic: str) -> None:
    httpx.post(
        f"https://ntfy.sh/{topic}",
        content=message.encode(),
        headers={"Title": "Raumdeuter WC Alert"},
        timeout=10,
    )


if __name__ == "__main__":
    api_key = os.environ["FD_API_KEY"]
    topic = os.environ["NTFY_TOPIC"]

    new = fetch_and_update(api_key, BASE_ELOS)
    if not new:
        print("No new results — exiting silently.")
        sys.exit(0)

    print(f"{len(new)} new result(s). Computing projections...")
    winners = projected_winners()

    lines = [f"{e.home} {e.score} {e.away} ({e.stage})" for e in new]
    lines += ["", "Updated projections:"]
    lines += [f"  {team}: {pct:.0%}" for team, pct in winners]

    message = "\n".join(lines)
    print(message)
    send_notification(message, topic)
    print(f"Notification sent to ntfy topic: {topic}")
