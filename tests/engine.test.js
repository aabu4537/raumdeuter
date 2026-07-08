// Property tests for the pure prediction engine.
import { describe, it, expect } from "vitest";
import { TEAMS } from "../src/data/teams.js";
import { matchModel, bracketProbs, teamStrength, dcTau, raumIndex, atkOn, atkOff } from "../src/model/engine.js";

const lineups = {}; for (const k in TEAMS) lineups[k] = TEAMS[k].xi;
const ESP = lineups.ESP, BEL = lineups.BEL, ENG = lineups.ENG, NOR = lineups.NOR;

describe("match model", () => {
  it("outcome probabilities sum to 1 at every alpha", () => {
    for (const a of [0, 0.25, 0.5, 0.75, 1]) {
      const m = matchModel(ESP, BEL, a);
      expect(m.w + m.d + m.l).toBeCloseTo(1, 6);
      expect(m.advH + m.advA).toBeCloseTo(1, 6);
    }
  });
  it("goal expectations stay in a realistic knockout range", () => {
    for (const h in lineups) for (const a in lineups) {
      if (h === a) continue;
      const m = matchModel(lineups[h], lineups[a], 0.35);
      expect(m.lh).toBeGreaterThan(0.2);
      expect(m.lh).toBeLessThan(3.5);
    }
  });
  it("a strictly better XI never lowers win probability", () => {
    const boosted = ESP.map(p => ({ ...p, fin: Math.min(99, p.fin + 10), mov: Math.min(99, p.mov + 10) }));
    for (const a of [0, 0.5, 1]) {
      expect(matchModel(boosted, BEL, a).advH)
        .toBeGreaterThanOrEqual(matchModel(ESP, BEL, a).advH);
    }
  });
});

describe("Dixon-Coles low-score correction (rho = -0.10)", () => {
  const lh = 1.2, la = 1.0;
  it("inflates 0-0 and 1-1", () => {
    expect(dcTau(0, 0, lh, la)).toBeGreaterThan(1);
    expect(dcTau(1, 1, lh, la)).toBeGreaterThan(1);
  });
  it("deflates 1-0 and 0-1", () => {
    expect(dcTau(1, 0, lh, la)).toBeLessThan(1);
    expect(dcTau(0, 1, lh, la)).toBeLessThan(1);
  });
  it("leaves every other scoreline untouched", () => {
    expect(dcTau(2, 1, lh, la)).toBe(1);
    expect(dcTau(0, 3, lh, la)).toBe(1);
  });
});

describe("alpha semantics", () => {
  it("at alpha=0 the model ignores off-ball stats entirely", () => {
    const ghostPress = ESP.map(p => p.pos === "GK" ? p : { ...p, prs: 1, rgn: 1, mov: 1 });
    const a0 = matchModel(ghostPress, BEL, 0);
    const base = matchModel(ESP, BEL, 0);
    expect(a0.lh).toBeCloseTo(base.lh, 6); // attack unchanged when off-ball zeroed at alpha 0
  });
  it("alpha reprices individuals: an off-ball swap can flip sign across alpha", () => {
    const watkins = TEAMS.ENG.bench.find(p => p.n === "Watkins");
    const eng2 = ENG.map(p => p.n === "Kane" ? watkins : p);
    const low = matchModel(NOR, eng2, 0).advA - matchModel(NOR, ENG, 0).advA;
    const high = matchModel(NOR, eng2, 0.8).advA - matchModel(NOR, ENG, 0.8).advA;
    expect(low).toBeLessThan(0);
    expect(high).toBeGreaterThan(0);
  });
});

describe("bracket propagation", () => {
  it("champion probabilities sum to 1 and cover all live teams", () => {
    for (const a of [0, 0.35, 1]) {
      const c = bracketProbs(lineups, a);
      const s = Object.values(c).reduce((x, y) => x + y, 0);
      expect(s).toBeCloseTo(1, 6);
      expect(Object.keys(c).length).toBe(10);
    }
  });
  it("every team has a strictly positive path to the title", () => {
    const c = bracketProbs(lineups, 0.35);
    for (const t in c) expect(c[t]).toBeGreaterThan(0);
  });
});

describe("player vectors", () => {
  it("raum index rewards the archetype: Merino outranks Kane off the ball", () => {
    const merino = TEAMS.ESP.bench.find(p => p.n === "Merino");
    const kane = TEAMS.ENG.xi.find(p => p.n === "Kane");
    expect(raumIndex(merino)).toBeGreaterThan(raumIndex(kane));
    expect(atkOn(kane)).toBeGreaterThan(atkOn(merino));
  });
});
