"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Nav } from "@/components/ui/nav";

const API = "http://localhost:8000";

interface TeamResult {
  team: string;
  confederation: string;
  elo: number;
  win_probability: number;
  finalist_probability: number;
  semifinalist_probability: number;
}

interface TournamentResult {
  n_simulations: number;
  teams: TeamResult[];
}

const confColour: Record<string, string> = {
  UEFA:     "bg-blue-50 text-blue-600 dark:bg-blue-950/40 dark:text-blue-400",
  CONMEBOL: "bg-yellow-50 text-yellow-600 dark:bg-yellow-950/40 dark:text-yellow-500",
  AFC:      "bg-red-50 text-red-600 dark:bg-red-950/40 dark:text-red-400",
  CAF:      "bg-green-50 text-green-600 dark:bg-green-950/40 dark:text-green-400",
  CONCACAF: "bg-purple-50 text-purple-600 dark:bg-purple-950/40 dark:text-purple-400",
  OFC:      "bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400",
};

function MiniBar({ value, color, max }: { value: number; color: string; max: number }) {
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-1.5 bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden flex-shrink-0">
        <motion.div
          className={`h-full rounded-full ${color}`}
          initial={{ width: 0 }}
          animate={{ width: `${(value / max) * 100}%` }}
          transition={{ duration: 0.7, ease: "easeOut" }}
        />
      </div>
      <span className="text-xs tabular-nums text-neutral-500 dark:text-neutral-400 w-10">
        {value > 0 ? `${(value * 100).toFixed(1)}%` : "—"}
      </span>
    </div>
  );
}

export default function TournamentPage() {
  const [nSims, setNSims] = useState(300);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TournamentResult | null>(null);
  const [error, setError] = useState("");
  const [view, setView] = useState<"all" | "top8">("top8");

  async function simulate() {
    setLoading(true); setError(""); setResult(null);
    try {
      const r = await fetch(`${API}/tournament?n_sims=${nSims}`);
      if (!r.ok) throw new Error(`API error ${r.status}`);
      setResult(await r.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  const displayTeams = result
    ? view === "top8" ? result.teams.slice(0, 8) : result.teams
    : [];

  const maxWin = result ? Math.max(...result.teams.map((t) => t.win_probability), 0.01) : 0.01;

  return (
    <main className="min-h-screen bg-white dark:bg-neutral-950 pb-24">
      <Nav />
      <div className="max-w-5xl mx-auto px-4 md:px-6 pt-12">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }} className="mb-10">
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-neutral-900 dark:text-white mb-2">
            Tournament Simulator
          </h1>
          <p className="text-neutral-500 dark:text-neutral-400">
            Full WC 2026 bracket — group stage through final, projected win probabilities for all 32 teams.
          </p>
        </motion.div>

        {/* Controls */}
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}
          className="rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-6 mb-8"
        >
          <div className="flex flex-col sm:flex-row gap-6 items-end">
            <div className="flex-1 space-y-2">
              <div className="flex justify-between">
                <label className="text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wide">
                  Simulations
                </label>
                <span className="text-xs font-semibold text-neutral-900 dark:text-white tabular-nums">
                  {nSims.toLocaleString()}
                </span>
              </div>
              <input
                type="range" min={100} max={1000} step={50} value={nSims}
                onChange={(e) => setNSims(Number(e.target.value))}
                className="w-full accent-neutral-900 dark:accent-white"
              />
              <div className="flex justify-between text-xs text-neutral-400">
                <span>100 (fast)</span>
                <span>1,000 (accurate)</span>
              </div>
            </div>
            <button
              onClick={simulate}
              disabled={loading}
              className="sm:w-52 w-full rounded-xl py-3 px-6 text-sm font-semibold bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 hover:bg-neutral-700 dark:hover:bg-neutral-100 disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 dark:border-neutral-900/30 border-t-white dark:border-t-neutral-900 rounded-full animate-spin" />
                  Simulating…
                </>
              ) : (
                `Simulate ${nSims} × →`
              )}
            </button>
          </div>
          {loading && (
            <p className="mt-3 text-xs text-neutral-400">
              Running full group stage + knockout bracket {nSims.toLocaleString()} times — takes ~10s…
            </p>
          )}
        </motion.div>

        {error && (
          <div className="mb-6 rounded-xl border border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-950/20 px-4 py-3 text-sm text-red-600 dark:text-red-400">{error}</div>
        )}

        <AnimatePresence>
          {result && (
            <motion.div key="result" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.5 }}>
              <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
                <div className="text-sm text-neutral-500 dark:text-neutral-400">
                  <span className="font-medium text-neutral-900 dark:text-white">{result.n_simulations.toLocaleString()}</span> simulations completed
                </div>
                <div className="flex gap-2">
                  {(["top8", "all"] as const).map((v) => (
                    <button key={v} onClick={() => setView(v)}
                      className={`text-sm px-3 py-1.5 rounded-lg transition-colors ${
                        view === v
                          ? "bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 font-medium"
                          : "bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200"
                      }`}
                    >
                      {v === "top8" ? "Top 8" : "All 32"}
                    </button>
                  ))}
                </div>
              </div>

              <div className="rounded-2xl border border-neutral-200 dark:border-neutral-800 overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-neutral-50 dark:bg-neutral-900 border-b border-neutral-200 dark:border-neutral-800">
                      <th className="text-left px-6 py-3 font-medium text-neutral-400 w-10">#</th>
                      <th className="text-left px-4 py-3 font-medium text-neutral-400">Team</th>
                      <th className="text-left px-4 py-3 font-medium text-neutral-400 hidden sm:table-cell">Conf.</th>
                      <th className="text-right px-4 py-3 font-medium text-neutral-400 hidden md:table-cell">Elo</th>
                      <th className="px-4 py-3 font-medium text-neutral-400">
                        <span className="flex items-center gap-1">
                          <span className="w-2 h-2 rounded-full bg-amber-400 inline-block" />
                          Win
                        </span>
                      </th>
                      <th className="px-4 py-3 font-medium text-neutral-400 hidden lg:table-cell">
                        <span className="flex items-center gap-1">
                          <span className="w-2 h-2 rounded-full bg-blue-400 inline-block" />
                          Final
                        </span>
                      </th>
                      <th className="px-6 py-3 font-medium text-neutral-400 hidden lg:table-cell">
                        <span className="flex items-center gap-1">
                          <span className="w-2 h-2 rounded-full bg-neutral-300 inline-block" />
                          Semi
                        </span>
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-100 dark:divide-neutral-800 bg-white dark:bg-neutral-950">
                    {displayTeams.map((team, i) => (
                      <motion.tr
                        key={team.team}
                        initial={{ opacity: 0, x: -8 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.03, duration: 0.3 }}
                        className="hover:bg-neutral-50 dark:hover:bg-neutral-900/40 transition-colors"
                      >
                        <td className="px-6 py-3.5 text-neutral-300 dark:text-neutral-700 font-mono text-xs">
                          {i + 1}
                        </td>
                        <td className="px-4 py-3.5 font-medium text-neutral-900 dark:text-white">
                          {team.team}
                        </td>
                        <td className="px-4 py-3.5 hidden sm:table-cell">
                          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${confColour[team.confederation] ?? ""}`}>
                            {team.confederation}
                          </span>
                        </td>
                        <td className="px-4 py-3.5 text-right tabular-nums text-neutral-500 dark:text-neutral-400 hidden md:table-cell">
                          {team.elo.toFixed(0)}
                        </td>
                        <td className="px-4 py-3.5">
                          <MiniBar value={team.win_probability} color="bg-amber-400" max={maxWin} />
                        </td>
                        <td className="px-4 py-3.5 hidden lg:table-cell">
                          <MiniBar value={team.finalist_probability} color="bg-blue-400" max={1} />
                        </td>
                        <td className="px-6 py-3.5 hidden lg:table-cell">
                          <MiniBar value={team.semifinalist_probability} color="bg-neutral-300 dark:bg-neutral-600" max={1} />
                        </td>
                      </motion.tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </main>
  );
}
