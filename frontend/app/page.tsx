"use client";

import { BackgroundPaths } from "@/components/ui/background-paths";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";

const features = [
  {
    icon: "⚽",
    title: "Dixon-Coles Model",
    description:
      "Bivariate Poisson simulation with low-score correction — more realistic than standard Poisson for football.",
  },
  {
    icon: "🧠",
    title: "10 Research Modules",
    description:
      "Climate adaptation, tournament DNA, pressure performance, chaos tolerance, and more — intangibles quantified.",
  },
  {
    icon: "📊",
    title: "XGBoost + SHAP",
    description:
      "Machine-learning match predictor reveals which modules add lift over raw Elo baseline.",
  },
  {
    icon: "🔴",
    title: "Live Elo Updates",
    description:
      "Elos recalculate after every WC result. Every prediction reflects the tournament in real time.",
  },
  {
    icon: "🔔",
    title: "Phone Notifications",
    description:
      "GitHub Actions cron pushes match results + updated projected winners to your phone via ntfy.",
  },
  {
    icon: "🗂️",
    title: "H2H + xG Analysis",
    description:
      "Head-to-head WC history, xG form, and tactical context feed directly into the prediction model.",
  },
];

const endpoints = [
  ["GET", "/teams", "All 32 teams with live Elo ratings"],
  ["POST", "/predict", "XGBoost 3-way probabilities + module delta"],
  ["POST", "/simulate", "Monte Carlo head-to-head simulation"],
  ["GET", "/analysis", "H2H + xG form + modules in one response"],
  ["GET", "/state", "Live Elo changes + recent results"],
  ["POST", "/ingest", "Pull latest results from football-data.org"],
] as const;

export default function Home() {
  const router = useRouter();

  return (
    <main className="min-h-screen bg-white dark:bg-neutral-950">
      {/* Hero */}
      <BackgroundPaths
        title="Raumdeuter"
        subtitle="WC 2026 prediction engine — Dixon-Coles, XGBoost, and 10 research modules that go beyond Elo."
        ctaLabel="Predict a Match"
        onCta={() => router.push("/predict")}
      />

      {/* Feature grid */}
      <section id="features" className="py-24 px-4 md:px-6">
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7 }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-neutral-900 dark:text-white mb-4">
              Beyond the Rankings
            </h2>
            <p className="text-neutral-500 dark:text-neutral-400 max-w-lg mx-auto">
              Most models stop at FIFA rankings. Raumdeuter models the
              intangibles — and measures whether they actually matter.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08, duration: 0.5 }}
                className="group p-6 rounded-2xl border border-neutral-200 dark:border-neutral-800
                  bg-white dark:bg-neutral-900 hover:border-neutral-300 dark:hover:border-neutral-700
                  hover:shadow-md dark:hover:shadow-neutral-900/50 transition-all duration-300"
              >
                <div className="text-3xl mb-4">{f.icon}</div>
                <h3 className="text-base font-semibold text-neutral-900 dark:text-white mb-2">
                  {f.title}
                </h3>
                <p className="text-sm text-neutral-500 dark:text-neutral-400 leading-relaxed">
                  {f.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* API strip */}
      <section className="py-20 px-4 md:px-6 border-t border-neutral-100 dark:border-neutral-800">
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-neutral-900 dark:text-white mb-4">
              REST API
            </h2>
            <p className="text-neutral-500 dark:text-neutral-400">
              Run locally with{" "}
              <code className="text-sm bg-neutral-100 dark:bg-neutral-800 px-2 py-0.5 rounded font-mono">
                uvicorn api:app --app-dir src
              </code>
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="rounded-2xl overflow-hidden border border-neutral-200 dark:border-neutral-800"
          >
            {/* Fake terminal bar */}
            <div className="bg-neutral-50 dark:bg-neutral-900 px-6 py-3 border-b border-neutral-200 dark:border-neutral-800 flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-red-400" />
              <span className="w-3 h-3 rounded-full bg-yellow-400" />
              <span className="w-3 h-3 rounded-full bg-green-400" />
              <span className="ml-3 text-xs font-mono text-neutral-400">
                http://localhost:8000
              </span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-neutral-50 dark:bg-neutral-900/60 border-b border-neutral-200 dark:border-neutral-800">
                    <th className="text-left px-6 py-3 font-medium text-neutral-500 dark:text-neutral-400 w-20">
                      Method
                    </th>
                    <th className="text-left px-6 py-3 font-medium text-neutral-500 dark:text-neutral-400 w-44">
                      Endpoint
                    </th>
                    <th className="text-left px-6 py-3 font-medium text-neutral-500 dark:text-neutral-400">
                      Description
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-100 dark:divide-neutral-800 bg-white dark:bg-neutral-950">
                  {endpoints.map(([method, endpoint, desc]) => (
                    <tr
                      key={endpoint}
                      className="hover:bg-neutral-50 dark:hover:bg-neutral-900/40 transition-colors"
                    >
                      <td className="px-6 py-4">
                        <span
                          className={`text-xs font-mono font-semibold px-2 py-1 rounded-md ${
                            method === "GET"
                              ? "bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400"
                              : "bg-blue-50 text-blue-600 dark:bg-blue-950/40 dark:text-blue-400"
                          }`}
                        >
                          {method}
                        </span>
                      </td>
                      <td className="px-6 py-4 font-mono text-neutral-900 dark:text-neutral-100 text-xs">
                        {endpoint}
                      </td>
                      <td className="px-6 py-4 text-neutral-500 dark:text-neutral-400">
                        {desc}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-10 px-4 border-t border-neutral-100 dark:border-neutral-800 text-center text-sm text-neutral-400 dark:text-neutral-600">
        <p>
          <em>Raumdeuter</em> — named after Jürgen Klinsmann&apos;s term for
          Thomas Müller. Finding the spaces between the data.
        </p>
      </footer>
    </main>
  );
}
