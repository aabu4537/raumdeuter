"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Nav } from "@/components/ui/nav";

const API = "http://localhost:8000";

interface Team {
  name: string;
  elo: number;
  elo_delta: number;
  confederation: string;
  fifa_code: string;
}

interface AnalysisResult {
  home_team: string;
  away_team: string;
  home_elo: number;
  away_elo: number;
  prediction: {
    home_win: number;
    draw: number;
    away_win: number;
    elo_baseline_home_win: number;
    matchup_adjustment: string;
  };
  head_to_head: {
    wc_meetings: number;
    home_wins: number;
    away_wins: number;
    draws: number;
    record: string;
    source: string;
  };
  xg_form: Record<
    string,
    | { xg_per_game: number; xg_against_per_game: number; wc_games_in_dataset: number }
    | string
  >;
  research_modules: Record<
    string,
    { [key: string]: number | string }
  >;
  composite_score: Record<string, number | string>;
}

function ProbBar({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex justify-between text-sm">
        <span className="text-neutral-600 dark:text-neutral-400">{label}</span>
        <span className="font-semibold text-neutral-900 dark:text-white">
          {(value * 100).toFixed(1)}%
        </span>
      </div>
      <div className="h-2 w-full bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden">
        <motion.div
          className={`h-full rounded-full ${color}`}
          initial={{ width: 0 }}
          animate={{ width: `${value * 100}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}

function ModuleRow({
  name,
  home,
  away,
  edge,
  homeTeam,
}: {
  name: string;
  home: number;
  away: number;
  edge: string;
  homeTeam: string;
}) {
  const homeLeads = home >= away;
  const label = name.replace(/_/g, " ");
  return (
    <tr className="border-b border-neutral-100 dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-900/40 transition-colors">
      <td className="py-2.5 pr-4 text-sm text-neutral-500 dark:text-neutral-400 capitalize">
        {label}
      </td>
      <td className="py-2.5 px-3 text-sm font-medium text-right tabular-nums text-neutral-900 dark:text-white">
        {home.toFixed(1)}
      </td>
      <td className="py-2.5 px-3 text-sm font-medium text-right tabular-nums text-neutral-900 dark:text-white">
        {away.toFixed(1)}
      </td>
      <td className="py-2.5 pl-3 text-right">
        <span
          className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
            homeLeads
              ? "bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400"
              : "bg-blue-50 text-blue-600 dark:bg-blue-950/40 dark:text-blue-400"
          }`}
        >
          {edge}
        </span>
      </td>
    </tr>
  );
}

export default function PredictPage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [home, setHome] = useState("");
  const [away, setAway] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState("");
  const [teamsLoading, setTeamsLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/teams`)
      .then((r) => r.json())
      .then((data: Team[]) => {
        setTeams(data);
        setTeamsLoading(false);
      })
      .catch(() => {
        setError("Could not reach the API. Make sure the backend is running on port 8000.");
        setTeamsLoading(false);
      });
  }, []);

  async function analyse() {
    if (!home || !away || home === away) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const r = await fetch(
        `${API}/analysis?home=${encodeURIComponent(home)}&away=${encodeURIComponent(away)}`
      );
      if (!r.ok) throw new Error(`API error ${r.status}`);
      setResult(await r.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  const confColour: Record<string, string> = {
    UEFA: "bg-blue-50 text-blue-600 dark:bg-blue-950/40 dark:text-blue-400",
    CONMEBOL: "bg-yellow-50 text-yellow-600 dark:bg-yellow-950/40 dark:text-yellow-500",
    AFC: "bg-red-50 text-red-600 dark:bg-red-950/40 dark:text-red-400",
    CAF: "bg-green-50 text-green-600 dark:bg-green-950/40 dark:text-green-400",
    CONCACAF: "bg-purple-50 text-purple-600 dark:bg-purple-950/40 dark:text-purple-400",
    OFC: "bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400",
  };

  return (
    <main className="min-h-screen bg-white dark:bg-neutral-950 pb-24">
      <Nav />

      <div className="max-w-5xl mx-auto px-4 md:px-6 pt-12">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-10"
        >
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-neutral-900 dark:text-white mb-2">
            Match Predictor
          </h1>
          <p className="text-neutral-500 dark:text-neutral-400">
            Select two teams to get XGBoost probabilities, H2H history, xG form, and module scores.
          </p>
        </motion.div>

        {/* Team picker */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="grid grid-cols-1 sm:grid-cols-[1fr_auto_1fr_auto] gap-3 items-end mb-8"
        >
          {/* Home team */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wide">
              Home team
            </label>
            <select
              value={home}
              onChange={(e) => setHome(e.target.value)}
              disabled={teamsLoading}
              className="w-full rounded-xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900
                text-neutral-900 dark:text-white px-4 py-3 text-sm focus:outline-none focus:ring-2
                focus:ring-neutral-900 dark:focus:ring-white/30 transition disabled:opacity-40"
            >
              <option value="">Select team…</option>
              {teams.map((t) => (
                <option key={t.name} value={t.name} disabled={t.name === away}>
                  {t.name} ({t.elo.toFixed(0)})
                </option>
              ))}
            </select>
          </div>

          {/* VS badge */}
          <div className="flex items-end pb-3">
            <span className="text-xs font-bold text-neutral-300 dark:text-neutral-700 px-1">
              VS
            </span>
          </div>

          {/* Away team */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wide">
              Away team
            </label>
            <select
              value={away}
              onChange={(e) => setAway(e.target.value)}
              disabled={teamsLoading}
              className="w-full rounded-xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900
                text-neutral-900 dark:text-white px-4 py-3 text-sm focus:outline-none focus:ring-2
                focus:ring-neutral-900 dark:focus:ring-white/30 transition disabled:opacity-40"
            >
              <option value="">Select team…</option>
              {teams.map((t) => (
                <option key={t.name} value={t.name} disabled={t.name === home}>
                  {t.name} ({t.elo.toFixed(0)})
                </option>
              ))}
            </select>
          </div>

          {/* Analyse button */}
          <button
            onClick={analyse}
            disabled={!home || !away || home === away || loading}
            className="rounded-xl px-6 py-3 text-sm font-semibold bg-neutral-900 dark:bg-white
              text-white dark:text-neutral-900 hover:bg-neutral-700 dark:hover:bg-neutral-100
              disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-200
              focus:outline-none focus:ring-2 focus:ring-neutral-900 dark:focus:ring-white/30"
          >
            {loading ? "Analysing…" : "Analyse →"}
          </button>
        </motion.div>

        {/* Error */}
        {error && (
          <div className="mb-6 rounded-xl border border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-950/20 px-4 py-3 text-sm text-red-600 dark:text-red-400">
            {error}
          </div>
        )}

        {/* Team cards while loading */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="flex flex-col items-center gap-3 text-neutral-400">
              <div className="w-8 h-8 border-2 border-neutral-200 dark:border-neutral-700 border-t-neutral-600 dark:border-t-neutral-300 rounded-full animate-spin" />
              <span className="text-sm">Running analysis…</span>
            </div>
          </div>
        )}

        {/* Results */}
        <AnimatePresence>
          {result && (
            <motion.div
              key="results"
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.5 }}
              className="space-y-6"
            >
              {/* Match header */}
              <div className="rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-6">
                <div className="flex items-center justify-between flex-wrap gap-4">
                  <div className="text-center flex-1">
                    <div className="text-2xl font-bold text-neutral-900 dark:text-white">
                      {result.home_team}
                    </div>
                    <div className="text-sm text-neutral-400 mt-1">
                      Elo {result.home_elo.toFixed(0)}
                    </div>
                    <span className={`mt-2 inline-block text-xs px-2 py-0.5 rounded-full ${confColour[teams.find(t => t.name === result.home_team)?.confederation ?? ""] ?? ""}`}>
                      {teams.find(t => t.name === result.home_team)?.confederation}
                    </span>
                  </div>
                  <div className="text-2xl font-light text-neutral-300 dark:text-neutral-700 px-4">
                    vs
                  </div>
                  <div className="text-center flex-1">
                    <div className="text-2xl font-bold text-neutral-900 dark:text-white">
                      {result.away_team}
                    </div>
                    <div className="text-sm text-neutral-400 mt-1">
                      Elo {result.away_elo.toFixed(0)}
                    </div>
                    <span className={`mt-2 inline-block text-xs px-2 py-0.5 rounded-full ${confColour[teams.find(t => t.name === result.away_team)?.confederation ?? ""] ?? ""}`}>
                      {teams.find(t => t.name === result.away_team)?.confederation}
                    </span>
                  </div>
                </div>
              </div>

              {/* Prediction + H2H row */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Prediction */}
                <div className="rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-6">
                  <h2 className="text-sm font-semibold text-neutral-900 dark:text-white mb-5 uppercase tracking-wide">
                    Prediction
                  </h2>
                  <div className="space-y-4">
                    <ProbBar
                      label={`${result.home_team} win`}
                      value={result.prediction.home_win}
                      color="bg-emerald-500"
                    />
                    <ProbBar
                      label="Draw"
                      value={result.prediction.draw}
                      color="bg-neutral-400"
                    />
                    <ProbBar
                      label={`${result.away_team} win`}
                      value={result.prediction.away_win}
                      color="bg-blue-500"
                    />
                  </div>
                  <div className="mt-5 pt-4 border-t border-neutral-100 dark:border-neutral-800 grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <div className="text-neutral-400 text-xs mb-0.5">Elo baseline</div>
                      <div className="font-medium text-neutral-900 dark:text-white">
                        {(result.prediction.elo_baseline_home_win * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div>
                      <div className="text-neutral-400 text-xs mb-0.5">Module adjustment</div>
                      <div className={`font-medium ${result.prediction.matchup_adjustment.startsWith("+") ? "text-emerald-600 dark:text-emerald-400" : "text-red-500 dark:text-red-400"}`}>
                        {result.prediction.matchup_adjustment}
                      </div>
                    </div>
                  </div>
                </div>

                {/* H2H */}
                <div className="rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-6">
                  <h2 className="text-sm font-semibold text-neutral-900 dark:text-white mb-5 uppercase tracking-wide">
                    Head-to-Head (WC)
                  </h2>
                  {result.head_to_head.wc_meetings === 0 ? (
                    <div className="text-sm text-neutral-400 italic">
                      No WC meetings in dataset (2018 + 2022)
                    </div>
                  ) : (
                    <>
                      <div className="text-sm text-neutral-600 dark:text-neutral-300 mb-4">
                        {result.head_to_head.record}
                      </div>
                      <div className="grid grid-cols-3 gap-3 text-center">
                        {[
                          [result.head_to_head.home_wins, result.home_team, "text-emerald-600 dark:text-emerald-400"],
                          [result.head_to_head.draws, "Draws", "text-neutral-500"],
                          [result.head_to_head.away_wins, result.away_team, "text-blue-600 dark:text-blue-400"],
                        ].map(([val, label, cls]) => (
                          <div key={String(label)} className="rounded-xl bg-neutral-50 dark:bg-neutral-800 p-3">
                            <div className={`text-2xl font-bold ${cls}`}>{val}</div>
                            <div className="text-xs text-neutral-400 mt-1 truncate">{label}</div>
                          </div>
                        ))}
                      </div>
                    </>
                  )}
                  <div className="mt-4 pt-3 border-t border-neutral-100 dark:border-neutral-800 text-xs text-neutral-400">
                    {result.head_to_head.source}
                  </div>
                </div>
              </div>

              {/* xG form */}
              <div className="rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-6">
                <h2 className="text-sm font-semibold text-neutral-900 dark:text-white mb-5 uppercase tracking-wide">
                  xG Form (WC dataset)
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  {[result.home_team, result.away_team].map((team) => {
                    const data = result.xg_form[team] as {
                      xg_per_game: number;
                      xg_against_per_game: number;
                      wc_games_in_dataset: number;
                    };
                    if (!data) return null;
                    return (
                      <div key={team}>
                        <div className="text-sm font-medium text-neutral-900 dark:text-white mb-3">
                          {team}
                          <span className="ml-2 text-xs text-neutral-400 font-normal">
                            {data.wc_games_in_dataset} WC games
                          </span>
                        </div>
                        <div className="space-y-3">
                          <div>
                            <div className="flex justify-between text-xs mb-1">
                              <span className="text-neutral-500">xG per game</span>
                              <span className="font-medium text-neutral-900 dark:text-white">{data.xg_per_game.toFixed(2)}</span>
                            </div>
                            <div className="h-1.5 w-full bg-neutral-100 dark:bg-neutral-800 rounded-full">
                              <motion.div
                                className="h-full rounded-full bg-emerald-500"
                                initial={{ width: 0 }}
                                animate={{ width: `${Math.min(data.xg_per_game / 3 * 100, 100)}%` }}
                                transition={{ duration: 0.8, ease: "easeOut" }}
                              />
                            </div>
                          </div>
                          <div>
                            <div className="flex justify-between text-xs mb-1">
                              <span className="text-neutral-500">xG against per game</span>
                              <span className="font-medium text-neutral-900 dark:text-white">{data.xg_against_per_game.toFixed(2)}</span>
                            </div>
                            <div className="h-1.5 w-full bg-neutral-100 dark:bg-neutral-800 rounded-full">
                              <motion.div
                                className="h-full rounded-full bg-red-400"
                                initial={{ width: 0 }}
                                animate={{ width: `${Math.min(data.xg_against_per_game / 3 * 100, 100)}%` }}
                                transition={{ duration: 0.8, ease: "easeOut" }}
                              />
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
                <div className="mt-5 pt-4 border-t border-neutral-100 dark:border-neutral-800 grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-neutral-400 text-xs">Attack edge</span>
                    <div className="font-medium text-neutral-900 dark:text-white mt-0.5">
                      {result.xg_form.attack_edge as string}
                    </div>
                  </div>
                  <div>
                    <span className="text-neutral-400 text-xs">Defense edge</span>
                    <div className="font-medium text-neutral-900 dark:text-white mt-0.5">
                      {result.xg_form.defense_edge as string}
                    </div>
                  </div>
                </div>
              </div>

              {/* Research modules */}
              <div className="rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-6">
                <div className="flex items-baseline justify-between mb-5">
                  <h2 className="text-sm font-semibold text-neutral-900 dark:text-white uppercase tracking-wide">
                    Research Modules
                  </h2>
                  <div className="flex gap-6 text-xs text-neutral-400">
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" />
                      {result.home_team}
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-blue-400 inline-block" />
                      {result.away_team}
                    </span>
                  </div>
                </div>
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-neutral-100 dark:border-neutral-800">
                      <th className="text-left text-xs font-medium text-neutral-400 pb-2 pr-4">Module</th>
                      <th className="text-right text-xs font-medium text-neutral-400 pb-2 px-3">{result.home_team.split(" ")[0]}</th>
                      <th className="text-right text-xs font-medium text-neutral-400 pb-2 px-3">{result.away_team.split(" ")[0]}</th>
                      <th className="text-right text-xs font-medium text-neutral-400 pb-2 pl-3">Edge</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(result.research_modules).map(([mod, scores]) => (
                      <ModuleRow
                        key={mod}
                        name={mod}
                        home={scores[result.home_team] as number}
                        away={scores[result.away_team] as number}
                        edge={scores.edge as string}
                        homeTeam={result.home_team}
                      />
                    ))}
                  </tbody>
                </table>
                <div className="mt-4 pt-4 border-t border-neutral-100 dark:border-neutral-800 flex items-center justify-between">
                  <span className="text-sm text-neutral-500">Composite score</span>
                  <div className="flex items-center gap-6 text-sm">
                    <span className="font-semibold text-neutral-900 dark:text-white">
                      {result.home_team.split(" ")[0]}: {(result.composite_score[result.home_team] as number).toFixed(1)}
                    </span>
                    <span className="font-semibold text-neutral-900 dark:text-white">
                      {result.away_team.split(" ")[0]}: {(result.composite_score[result.away_team] as number).toFixed(1)}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${
                      (result.composite_score[result.home_team] as number) >= (result.composite_score[result.away_team] as number)
                        ? "bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400"
                        : "bg-blue-50 text-blue-600 dark:bg-blue-950/40 dark:text-blue-400"
                    }`}>
                      {result.composite_score.edge as string}
                    </span>
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
