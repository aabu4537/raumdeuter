# Prediction Track Record

Frozen **July 7, 2026** (before the last two Round of 16 matches and all quarterfinals), at the
default consensus weighting **α = 0.35**. These numbers will not be retroactively edited; the
Result column gets filled in as matches finish, with a short honest note on hits and misses.

## Match predictions (probability to advance, home / away)

| Round | Date · Venue | Fixture | Model | Result |
|---|---|---|---|---|
| Round of 16 | Jul 7 · Atlanta | Argentina v Egypt | 72.5% / 27.5% | TBD |
| Round of 16 | Jul 7 · Vancouver | Switzerland v Colombia | 55.2% / 44.8% | TBD |
| Quarter-final | Jul 9 · Boston | France v Morocco | 54.5% / 45.5% | TBD |
| Quarter-final | Jul 10 · Inglewood | Spain v Belgium | 55.9% / 44.1% | TBD |
| Quarter-final | Jul 11 · Miami | Norway v England | 34.3% / 65.7% | TBD |
| Quarter-final | Jul 11 · Kansas City | Argentina v Switzerland *(projected pairing)* | 63.0% / 37.0% | TBD |
| Semi-final | Jul 14 · Dallas | France v Spain *(projected pairing)* | 43.9% / 56.1% | TBD |
| Semi-final | Jul 15 · Atlanta | England v Argentina *(projected pairing)* | 50.8% / 49.2% | TBD |
| World Cup Final | Jul 19 · MetLife | Spain v England *(projected pairing)* | 47.7% / 52.3% | TBD |

*(projected pairing)* means the participants were not yet determined when frozen; the model shows
its most likely pairing. The champion odds below do NOT assume these pairings; they propagate over
every possible path.

## Championship odds (α = 0.35)

1. **England** 22.2%
2. **Spain** 17.5%
3. **Argentina** 14.6%
4. **France** 12.3%
5. **Belgium** 11.1%
6. **Morocco** 8.6%
7. **Norway** 6.1%
8. **Switzerland** 4.2%
9. **Colombia** 2.2%
10. **Egypt** 1.2%

## Scoring

When the tournament ends, this file gets a Brier score over the match predictions and a note on
which misses were model error versus variance. A probabilistic model is not judged on picking
every winner; it is judged on whether its 65% calls land about 65% of the time.
