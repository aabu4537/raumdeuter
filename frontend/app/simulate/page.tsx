"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Nav } from "@/components/ui/nav";

const API = "http://localhost:8000";

interface Team { name: string; elo: number; }
interface SimResult {
  home_team: string;
  away_team: string;
  n_sims: number;
  knockout: boolean;
  home_win_pct: number;
  draw_pct: number;
  away_win_pct: number;
  elo_home_win: number;
}

function ProbBar({ label, value, sub, color }: { label: string; value: number; sub?: string; color: string }) {
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-sm">
        <div>
          <span className="font-medium text-neutral-900 dark:text-white">{label}</span>
          {sub && <span className="ml-2 text-xs text-neutral-400">{sub}</span>}
        </div>
        <span className="font-bold text-neutral-900 dark:text-white tabular-nums">
          {(value * 100).toFixed(1)}%
        </span>
      </div>
      <div className="h-3 w-full bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden">
        <motion.div
          className={`h-full rounded-full ${color}`}
          initial={{ width: 0 }}
          animate={{ width: `${value * 100}%` }}
          transition={{ duration: 0.9, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}

export default function SimulatePage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [home, setHome] = useState("");
  const [away, setAway] = useState("");
  const [nSims, setNSims] = useState(2000);
  const [knockout, setKnockout] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SimResult | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API}/teams`)
      .then((r) => r.json())
      .then(setTeams)
      .catch(() => setError("Could not reach the API."));
  }, []);

  async function simulate() {
    if (!home || !away || home === away) return;
    setLoading(true); setError(""); setResult(null);
    try {
      const r = await fetch(`${API}/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ home, away, n_sims: nSims, knockout }),
      });
      if (!r.ok) throw new Error(`API error ${r.status}`);
      setResult(await r.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  const selectCls = "w-full rounded-xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 text-neutral-900 dark:text-white px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-neutral-900 dark:focus:ring-white/30 transition disabled:opacity-40";

  return (
    <main className="min-h-screen bg-white dark:bg-neutral-950 pb-24">
      <Nav />
      <div className="max-w-5xl mx-auto px-4 md:px-6 pt-12">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }} className="mb-10">
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-neutral-900 dark:text-white mb-2">
            Monte Carlo Simulator
          </h1>
          <p className="text-neutral-500 dark:text-neutral-400">
            Run thousands of Dixon-Coles simulations for any matchup.
          </p>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}
          className="rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-6 mb-8 space-y-6"
        >
          {/* Team pickers */}
          <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto_1fr] gap-3 items-end">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wide">Home team</label>
              <select value={home} onChange={(e) => setHome(e.target.value)} className={selectCls}>
                <option value="">Select team…</option>
                {teams.map((t) => <option key={t.name} value={t.name} disabled={t.name === away}>{t.name} ({t.elo.toFixed(0)})</option>)}
              </select>
            </div>
            <div className="flex items-end pb-3">
              <span className="text-xs font-bold text-neutral-300 dark:text-neutral-700 px-1">VS</span>
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wide">Away team</label>
              <select value={away} onChange={(e) => setAway(e.target.value)} className={selectCls}>
                <option value="">Select team…</option>
                {teams.map((t) => <option key={t.name} value={t.name} disabled={t.name === home}>{t.name} ({t.elo.toFixed(0)})</option>)}
              </select>
            </div>
          </div>

          {/* Controls */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div className="space-y-2">
              <div className="flex justify-between">
                <label className="text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wide">Simulations</label>
                <span className="text-xs font-semibold text-neutral-900 dark:text-white tabular-nums">{nSims.toLocaleString()}</span>
              </div>
              <input
                type="range" min={100} max={10000} step={100} value={nSims}
                onChange={(e) => setNSims(Number(e.target.value))}
                className="w-full accent-neutral-900 dark:accent-white"
              />
              <div className="flex justify-between text-xs text-neutral-400">
                <span>100</span><span>10,000</span>
              </div>
            </div>

            <div className="flex flex-col justify-between">
              <label className="text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wide mb-3">Match type</label>
              <div className="flex gap-3">
                {[false, true].map((k) => (
                  <button
                    key={String(k)}
                    onClick={() => setKnockout(k)}
                    className={`flex-1 py-2.5 rounded-xl text-sm font-medium transition-colors border ${
                      knockout === k
                        ? "bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 border-transparent"
                        : "border-neutral-200 dark:border-neutral-700 text-neutral-600 dark:text-neutral-400 hover:border-neutral-300"
                    }`}
                  >
                    {k ? "Knockout" : "Group stage"}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <button
            onClick={simulate}
            disabled={!home || !away || home === away || loading}
            className="w-full rounded-xl py-3 text-sm font-semibold bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 hover:bg-neutral-700 dark:hover:bg-neutral-100 disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-200"
          >
            {loading ? "Simulating…" : `Run ${nSims.toLocaleString()} simulations →`}
          </button>
        </motion.div>

        {error && (
          <div className="mb-6 rounded-xl border border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-950/20 px-4 py-3 text-sm text-red-600 dark:text-red-400">{error}</div>
        )}

        {loading && (
          <div className="flex justify-center py-16">
            <div className="flex flex-col items-center gap-3 text-neutral-400">
              <div className="w-8 h-8 border-2 border-neutral-200 dark:border-neutral-700 border-t-neutral-600 dark:border-t-neutral-300 rounded-full animate-spin" />
              <span className="text-sm">Running {nSims.toLocaleString()} simulations…</span>
            </div>
          </div>
        )}

        <AnimatePresence>
          {result && (
            <motion.div key="result" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.5 }}
              className="rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-6 space-y-6"
            >
              <div className="flex items-center justify-between flex-wrap gap-2">
                <h2 className="text-sm font-semibold text-neutral-900 dark:text-white uppercase tracking-wide">
                  Results — {result.n_sims.toLocaleString()} simulations
                </h2>
                <span className={`text-xs px-2.5 py-1 rounded-full font-medium border ${
                  result.knockout
                    ? "border-amber-200 text-amber-600 bg-amber-50 dark:bg-amber-950/30 dark:text-amber-400 dark:border-amber-900/50"
                    : "border-neutral-200 text-neutral-500 bg-neutral-50 dark:bg-neutral-800 dark:text-neutral-400 dark:border-neutral-700"
                }`}>
                  {result.knockout ? "Knockout (ET + pens)" : "Group stage"}
                </span>
              </div>

              <div className="space-y-5">
                <ProbBar label={result.home_team} sub="(home)" value={result.home_win_pct} color="bg-emerald-500" />
                {!result.knockout && <ProbBar label="Draw" value={result.draw_pct} color="bg-neutral-400" />}
                <ProbBar label={result.away_team} sub="(away)" value={result.away_win_pct} color="bg-blue-500" />
              </div>

              <div className="pt-4 border-t border-neutral-100 dark:border-neutral-800 grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="text-xs text-neutral-400 mb-0.5">Elo baseline (home win)</div>
                  <div className="font-semibold text-neutral-900 dark:text-white">{(result.elo_home_win * 100).toFixed(1)}%</div>
                </div>
                <div>
                  <div className="text-xs text-neutral-400 mb-0.5">Simulation vs Elo</div>
                  <div className={`font-semibold ${result.home_win_pct - result.elo_home_win >= 0 ? "text-emerald-600 dark:text-emerald-400" : "text-red-500 dark:text-red-400"}`}>
                    {result.home_win_pct - result.elo_home_win >= 0 ? "+" : ""}
                    {((result.home_win_pct - result.elo_home_win) * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </main>
  );
}
