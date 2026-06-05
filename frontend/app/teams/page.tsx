"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Nav } from "@/components/ui/nav";

const API = "http://localhost:8000";

interface Team {
  name: string;
  elo: number;
  elo_base: number;
  elo_delta: number;
  fifa_code: string;
  confederation: string;
}

const confColour: Record<string, string> = {
  UEFA:     "bg-blue-50 text-blue-600 dark:bg-blue-950/40 dark:text-blue-400",
  CONMEBOL: "bg-yellow-50 text-yellow-600 dark:bg-yellow-950/40 dark:text-yellow-500",
  AFC:      "bg-red-50 text-red-600 dark:bg-red-950/40 dark:text-red-400",
  CAF:      "bg-green-50 text-green-600 dark:bg-green-950/40 dark:text-green-400",
  CONCACAF: "bg-purple-50 text-purple-600 dark:bg-purple-950/40 dark:text-purple-400",
  OFC:      "bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400",
};

export default function TeamsPage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sort, setSort] = useState<"elo" | "delta" | "name">("elo");

  useEffect(() => {
    fetch(`${API}/teams`)
      .then((r) => r.json())
      .then((data: Team[]) => { setTeams(data); setLoading(false); })
      .catch(() => { setError("Could not reach the API."); setLoading(false); });
  }, []);

  const sorted = [...teams].sort((a, b) => {
    if (sort === "elo") return b.elo - a.elo;
    if (sort === "delta") return b.elo_delta - a.elo_delta;
    return a.name.localeCompare(b.name);
  });

  return (
    <main className="min-h-screen bg-white dark:bg-neutral-950 pb-24">
      <Nav />
      <div className="max-w-5xl mx-auto px-4 md:px-6 pt-12">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="flex items-end justify-between mb-8 flex-wrap gap-4"
        >
          <div>
            <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-neutral-900 dark:text-white mb-2">
              Teams
            </h1>
            <p className="text-neutral-500 dark:text-neutral-400">
              All 32 WC 2026 teams — Elo ratings update live as results come in.
            </p>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className="text-neutral-400">Sort:</span>
            {(["elo", "delta", "name"] as const).map((s) => (
              <button
                key={s}
                onClick={() => setSort(s)}
                className={`px-3 py-1.5 rounded-lg transition-colors capitalize ${
                  sort === s
                    ? "bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 font-medium"
                    : "bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200 dark:hover:bg-neutral-700"
                }`}
              >
                {s === "delta" ? "Change" : s === "elo" ? "Elo" : "Name"}
              </button>
            ))}
          </div>
        </motion.div>

        {error && (
          <div className="mb-6 rounded-xl border border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-950/20 px-4 py-3 text-sm text-red-600 dark:text-red-400">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex justify-center py-20">
            <div className="w-8 h-8 border-2 border-neutral-200 dark:border-neutral-700 border-t-neutral-600 dark:border-t-neutral-300 rounded-full animate-spin" />
          </div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.4 }}
            className="rounded-2xl border border-neutral-200 dark:border-neutral-800 overflow-hidden"
          >
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-neutral-50 dark:bg-neutral-900 border-b border-neutral-200 dark:border-neutral-800">
                  <th className="text-left px-6 py-3 font-medium text-neutral-400 w-10">#</th>
                  <th className="text-left px-4 py-3 font-medium text-neutral-400">Team</th>
                  <th className="text-left px-4 py-3 font-medium text-neutral-400">Conf.</th>
                  <th className="text-right px-4 py-3 font-medium text-neutral-400">Base Elo</th>
                  <th className="text-right px-4 py-3 font-medium text-neutral-400">Live Elo</th>
                  <th className="text-right px-6 py-3 font-medium text-neutral-400">Change</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100 dark:divide-neutral-800 bg-white dark:bg-neutral-950">
                {sorted.map((team, i) => (
                  <motion.tr
                    key={team.name}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.015, duration: 0.3 }}
                    className="hover:bg-neutral-50 dark:hover:bg-neutral-900/40 transition-colors"
                  >
                    <td className="px-6 py-3.5 text-neutral-300 dark:text-neutral-700 font-mono text-xs">
                      {i + 1}
                    </td>
                    <td className="px-4 py-3.5 font-medium text-neutral-900 dark:text-white">
                      {team.name}
                      <span className="ml-2 text-xs font-mono text-neutral-400">
                        {team.fifa_code}
                      </span>
                    </td>
                    <td className="px-4 py-3.5">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${confColour[team.confederation] ?? ""}`}>
                        {team.confederation}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-right tabular-nums text-neutral-500 dark:text-neutral-400">
                      {team.elo_base.toFixed(0)}
                    </td>
                    <td className="px-4 py-3.5 text-right tabular-nums font-semibold text-neutral-900 dark:text-white">
                      {team.elo.toFixed(0)}
                    </td>
                    <td className="px-6 py-3.5 text-right tabular-nums">
                      {team.elo_delta === 0 ? (
                        <span className="text-neutral-300 dark:text-neutral-700">—</span>
                      ) : (
                        <span className={team.elo_delta > 0
                          ? "text-emerald-600 dark:text-emerald-400 font-medium"
                          : "text-red-500 dark:text-red-400 font-medium"
                        }>
                          {team.elo_delta > 0 ? "+" : ""}{team.elo_delta.toFixed(1)}
                        </span>
                      )}
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </motion.div>
        )}
      </div>
    </main>
  );
}
