import React from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { LineChart, Line, ResponsiveContainer, YAxis, Tooltip } from "recharts";
import { Activity, Server, Zap, Users, Terminal } from "lucide-react";
import { fetchers } from "../lib/api";
import { fmtNum, timeAgo } from "../lib/format";
import { Card, MetricCard, SectionLabel, Spinner, ViewHeader, Pill, statusTone } from "../components/ui-kit";

const logTone = { INFO: "text-sky-400", WARN: "text-amber-400", ERROR: "text-rose-400" };

export default function MonitoringView() {
  const { data, isLoading } = useQuery({
    queryKey: ["monitoring"],
    queryFn: fetchers.monitoring,
    refetchInterval: 5000,
  });

  if (isLoading || !data) return <Spinner label="Loading telemetry" />;

  const allOk = data.services.every((s) => s.status === "operational");

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-4 mb-6">
        <ViewHeader
          eyebrow="Platform Reliability"
          title="System Monitoring"
          desc="Service health, synthetic latency, request throughput and a live log stream across the platform's ingestion, AI and data-store components."
        />
        <Pill tone={allOk ? "bull" : "warn"} className="mb-2">
          {allOk ? "All systems operational" : "Degraded components"}
        </Pill>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5 mb-6">
        <MetricCard testid="monitoring-rpm-metric" label="Requests / min" value={fmtNum(data.requestsPerMin, 0)} sub="across gateway" subTone="text-muted-3" icon={Activity} />
        <MetricCard testid="monitoring-p95-metric" label="p95 Latency" value={`${fmtNum(data.p95LatencyMs, 0)}ms`} sub="rolling 5m" subTone="text-muted-3" icon={Zap} />
        <MetricCard testid="monitoring-sessions-metric" label="Active Sessions" value={data.activeSessions} sub="PM & research users" subTone="text-muted-3" icon={Users} />
        <MetricCard testid="monitoring-services-metric" label="Services Up" value={`${data.services.filter((s) => s.status === "operational").length}/${data.services.length}`} sub="components" subTone="text-muted-3" icon={Server} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-6">
        {/* Services */}
        <Card className="lg:col-span-7 p-0 overflow-hidden" data-testid="monitoring-services-table">
          <div className="px-6 py-4 border-b border-hair">
            <SectionLabel>Service Health</SectionLabel>
          </div>
          <div className="divide-y divide-[var(--border)]">
            {data.services.map((s, i) => (
              <motion.div
                key={s.name}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.03 }}
                className="px-6 py-3.5 flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <span className={`w-2.5 h-2.5 rounded-full ${s.status === "operational" ? "bg-emerald-400" : s.status === "degraded" ? "bg-amber-400" : "bg-rose-400"}`} />
                  <div>
                    <p className="text-sm font-medium">{s.name}</p>
                    <p className="font-mono text-xs text-muted-3 mt-0.5">{s.component}</p>
                  </div>
                </div>
                <div className="flex items-center gap-6 text-right">
                  <div className="hidden sm:block">
                    <p className="font-mono text-xs">{fmtNum(s.uptime, 3)}%</p>
                    <p className="text-[10px] text-muted-3">uptime</p>
                  </div>
                  <div className="hidden sm:block">
                    <p className="font-mono text-xs">{fmtNum(s.latencyMs, 0)}ms</p>
                    <p className="text-[10px] text-muted-3">latency</p>
                  </div>
                  <Pill tone={statusTone(s.status)}>{s.status}</Pill>
                </div>
              </motion.div>
            ))}
          </div>
        </Card>

        {/* Latency chart */}
        <Card className="lg:col-span-5 p-6">
          <SectionLabel>Gateway Latency · last 30 samples</SectionLabel>
          <ResponsiveContainer width="100%" height={180} className="mt-4">
            <LineChart data={data.latencySeries}>
              <YAxis hide domain={[0, 160]} />
              <Tooltip
                contentStyle={{ background: "#1A202C", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 10, fontSize: 12 }}
                formatter={(v) => [`${v}ms`, "latency"]}
                labelFormatter={() => ""}
              />
              <Line type="monotone" dataKey="ms" stroke="#38BDF8" strokeWidth={2} dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
          <div className="grid grid-cols-3 gap-3 mt-4">
            <div className="surface-2 rounded-lg p-3 border-hair text-center">
              <p className="font-mono text-lg font-semibold">{fmtNum(Math.min(...data.latencySeries.map((d) => d.ms)), 0)}</p>
              <p className="text-[10px] text-muted-3 mt-0.5">min ms</p>
            </div>
            <div className="surface-2 rounded-lg p-3 border-hair text-center">
              <p className="font-mono text-lg font-semibold">{fmtNum(data.latencySeries.reduce((a, d) => a + d.ms, 0) / data.latencySeries.length, 0)}</p>
              <p className="text-[10px] text-muted-3 mt-0.5">avg ms</p>
            </div>
            <div className="surface-2 rounded-lg p-3 border-hair text-center">
              <p className="font-mono text-lg font-semibold">{fmtNum(Math.max(...data.latencySeries.map((d) => d.ms)), 0)}</p>
              <p className="text-[10px] text-muted-3 mt-0.5">max ms</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Logs */}
      <Card className="p-0 overflow-hidden" data-testid="monitoring-log-viewer">
        <div className="px-6 py-4 border-b border-hair flex items-center gap-2">
          <Terminal className="w-4 h-4 text-sky-400" />
          <SectionLabel>Live Log Stream</SectionLabel>
        </div>
        <div className="divide-y divide-[var(--border)] font-mono text-xs">
          {data.logs.map((l, i) => (
            <div key={i} className="px-6 py-2.5 flex items-start gap-4 hover:bg-sky-500/[0.03] transition-colors duration-150">
              <span className="text-muted-3 shrink-0">{timeAgo(l.ts)}</span>
              <span className={`shrink-0 w-12 font-semibold ${logTone[l.level]}`}>{l.level}</span>
              <span className="text-muted-3 shrink-0 w-36 truncate">{l.service}</span>
              <span className="text-muted-2">{l.message}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
