import React, { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import {
  GitMerge,
  Play,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  Database,
  ChevronDown,
} from "lucide-react";
import { fetchers } from "../lib/api";
import { fmtNum, fmtCompact, timeAgo } from "../lib/format";
import { Card, MetricCard, SectionLabel, Spinner, ViewHeader, Pill, statusTone } from "../components/ui-kit";

const checkIcon = {
  pass: <CheckCircle2 className="w-4 h-4 text-emerald-400" />,
  warn: <AlertTriangle className="w-4 h-4 text-amber-400" />,
  fail: <XCircle className="w-4 h-4 text-rose-400" />,
};

export default function PipelinesView() {
  const qc = useQueryClient();
  const [running, setRunning] = useState(false);
  const [expanded, setExpanded] = useState(null);

  const { data, isLoading } = useQuery({
    queryKey: ["pipelines"],
    queryFn: fetchers.pipelines,
  });

  const runAll = async (forceIssue) => {
    setRunning(true);
    try {
      const r = await fetchers.runPipelines(forceIssue);
      qc.setQueryData(["pipelines"], r);
      const f = r.summary.failed;
      if (f > 0) toast.error(`Validation complete · ${f} pipeline(s) failing`);
      else toast.success(`Validation complete · ${r.summary.checksPassRate}% checks passed`);
    } catch {
      toast.error("Could not trigger validation run");
    } finally {
      setRunning(false);
    }
  };

  if (isLoading || !data) return <Spinner label="Loading pipelines" />;

  const s = data.summary;

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-4 mb-6">
        <ViewHeader
          eyebrow="Data Engineering"
          title="Data Quality & Pipelines"
          desc="Ingestion pipelines with automated data-quality validation. Market-data-backed pipelines run the real validation engine against the live quote feed — schema, completeness, freshness SLA, outlier bounds, row-count drift and duplicate checks."
        />
        <div className="flex gap-2 mb-2">
          <button
            data-testid="pipeline-trigger-validation-button"
            onClick={() => runAll(false)}
            disabled={running}
            className="flex items-center gap-2 bg-sky-500 hover:bg-sky-400 disabled:opacity-50 text-slate-950 font-medium text-sm px-4 py-2 rounded-full transition-colors duration-150"
          >
            <Play className="w-4 h-4" /> {running ? "Running…" : "Run validation"}
          </button>
          <button
            data-testid="pipeline-simulate-issue-button"
            onClick={() => runAll(true)}
            disabled={running}
            className="flex items-center gap-2 surface-2 border-hair hover:border-rose-500/40 text-muted-2 font-medium text-sm px-4 py-2 rounded-full transition-colors duration-150"
          >
            <AlertTriangle className="w-4 h-4" /> Simulate incident
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5 mb-6">
        <MetricCard testid="pipeline-passrate-metric" label="Checks Pass Rate" value={`${fmtNum(s.checksPassRate, 1)}%`} sub={`${s.total} pipelines`} subTone="text-muted-3" icon={CheckCircle2} />
        <MetricCard testid="pipeline-healthy-metric" label="Healthy" value={s.healthy} sub={`${s.degraded} degraded`} subTone="text-amber-400" icon={GitMerge} />
        <MetricCard testid="pipeline-failed-metric" label="Failing" value={s.failed} sub={s.failed ? "needs attention" : "all clear"} subTone={s.failed ? "text-rose-400" : "text-emerald-400"} icon={XCircle} />
        <MetricCard testid="pipeline-rows-metric" label="Rows Today" value={fmtCompact(s.rowsToday)} sub="ingested & validated" subTone="text-muted-3" icon={Database} />
      </div>

      <div className="space-y-4">
        {data.pipelines.map((p, i) => (
          <motion.div
            key={p.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04 }}
          >
            <Card className="overflow-hidden" data-testid={`pipeline-card-${p.id}`}>
              <button
                onClick={() => setExpanded(expanded === p.id ? null : p.id)}
                className="w-full px-6 py-4 flex items-center justify-between hover:bg-sky-500/[0.03] transition-colors duration-150"
              >
                <div className="flex items-center gap-4 text-left">
                  <div className={`w-2.5 h-2.5 rounded-full ${p.status === "healthy" ? "bg-emerald-400" : p.status === "degraded" ? "bg-amber-400" : "bg-rose-400"}`} />
                  <div>
                    <p className="font-medium text-sm">{p.name}</p>
                    <p className="font-mono text-xs text-muted-3 mt-0.5">{p.schedule} · {p.owner}</p>
                  </div>
                </div>
                <div className="flex items-center gap-5">
                  <div className="hidden sm:flex items-center gap-4 text-xs text-muted-2">
                    <span className="flex items-center gap-1 font-mono"><Clock className="w-3.5 h-3.5" /> {p.freshnessMin}m</span>
                    <span className="font-mono">{fmtNum(p.completeness, 1)}%</span>
                    <span className="font-mono text-muted-3">{timeAgo(p.lastRun)}</span>
                  </div>
                  <Pill tone={p.live ? "bull" : "muted"}>{p.live ? "Live data" : "Sample"}</Pill>
                  <Pill tone={statusTone(p.status)}>{p.passed}/{p.checks.length} checks</Pill>
                  <ChevronDown className={`w-4 h-4 text-muted-3 transition-transform duration-200 ${expanded === p.id ? "rotate-180" : ""}`} />
                </div>
              </button>
              <AnimatePresence>
                {expanded === p.id && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden border-t border-hair"
                  >
                    <div className="px-6 py-4 grid sm:grid-cols-2 gap-x-8 gap-y-2.5 surface-2">
                      {p.checks.map((c) => (
                        <div key={c.key} className="flex items-center justify-between py-1 gap-3" data-testid={`check-${p.id}-${c.key}`}>
                          <span className="flex items-center gap-2 text-sm text-muted-2 shrink-0">
                            {checkIcon[c.status]} {c.label}
                          </span>
                          <span className="font-mono text-xs text-muted-3 text-right truncate">{c.detail || `${fmtCompact(c.rows)} rows`}</span>
                        </div>
                      ))}
                      <div className="sm:col-span-2 flex items-center justify-between pt-2 mt-1 border-t border-hair text-xs text-muted-3 font-mono">
                        <span>duration {p.durationMs}ms</span>
                        <span>{fmtCompact(p.rowsProcessed)} rows processed</span>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
