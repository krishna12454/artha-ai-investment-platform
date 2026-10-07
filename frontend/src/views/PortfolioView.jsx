import React from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import { Wallet, TrendingUp, Layers, Activity } from "lucide-react";
import { fetchers } from "../lib/api";
import { fmtNum, fmtPct, fmtCompact, changeColor } from "../lib/format";
import { Card, MetricCard, SectionLabel, Spinner, ViewHeader, Pill } from "../components/ui-kit";

const SECTOR_COLORS = ["#38BDF8", "#10B981", "#F59E0B", "#A78BFA", "#F43F5E", "#2DD4BF", "#FB923C"];

export default function PortfolioView() {
  const { data, isLoading } = useQuery({
    queryKey: ["portfolio"],
    queryFn: fetchers.portfolio,
    refetchInterval: 6000,
  });

  if (isLoading || !data) return <Spinner label="Loading mandate" />;

  const perfChange = data.performance.length
    ? data.performance[data.performance.length - 1].portfolio - 100
    : 0;

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-4 mb-6">
        <ViewHeader
          eyebrow="Discretionary Mandate"
          title="Portfolio Management"
          desc={data.mandate}
        />
        <Pill tone="neutral" className="mb-2">Base currency · {data.baseCurrency}</Pill>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-6">
        <MetricCard
          testid="portfolio-total-value-metric"
          label="Total Value"
          value={`CHF ${fmtNum(data.totalValue, 0)}`}
          sub={`Cost CHF ${fmtNum(data.totalCost, 0)}`}
          subTone="text-muted-3"
          icon={Wallet}
          delay={0}
        />
        <MetricCard
          testid="portfolio-day-pnl-metric"
          label="Day P&L"
          value={`${data.dayPnl > 0 ? "+" : ""}${fmtNum(data.dayPnl, 0)}`}
          sub={fmtPct(data.dayPnlPct)}
          subTone={changeColor(data.dayPnl)}
          icon={Activity}
          delay={0.05}
        />
        <MetricCard
          testid="portfolio-total-pnl-metric"
          label="Unrealised P&L"
          value={`${data.totalPnl > 0 ? "+" : ""}${fmtNum(data.totalPnl, 0)}`}
          sub={fmtPct(data.totalPnlPct)}
          subTone={changeColor(data.totalPnl)}
          icon={TrendingUp}
          delay={0.1}
        />
        <MetricCard
          testid="portfolio-positions-metric"
          label="Positions"
          value={data.positions.length}
          sub={`${data.allocation.length} sectors`}
          subTone="text-muted-3"
          icon={Layers}
          delay={0.15}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-6">
        {/* Performance */}
        <Card className="lg:col-span-8 p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <SectionLabel>Performance · indexed to 100</SectionLabel>
              <p className="font-heading text-lg font-semibold mt-1">
                Portfolio vs SPI Benchmark{" "}
                <span className={`font-mono text-sm ${changeColor(perfChange)}`}>
                  {fmtPct(perfChange)}
                </span>
              </p>
            </div>
            <div className="flex items-center gap-4 text-xs">
              <span className="flex items-center gap-1.5 text-muted-2">
                <span className="w-2.5 h-2.5 rounded-sm bg-sky-400" /> Portfolio
              </span>
              <span className="flex items-center gap-1.5 text-muted-2">
                <span className="w-2.5 h-2.5 rounded-sm bg-slate-500" /> Benchmark
              </span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={data.performance} margin={{ left: -18, right: 6, top: 6 }}>
              <defs>
                <linearGradient id="gPort" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#38BDF8" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#38BDF8" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.12)" vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#64748B" }} tickLine={false} axisLine={false} minTickGap={48} />
              <YAxis tick={{ fontSize: 10, fill: "#64748B" }} tickLine={false} axisLine={false} domain={["dataMin - 2", "dataMax + 2"]} />
              <Tooltip
                contentStyle={{ background: "#1A202C", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 10, fontSize: 12 }}
                labelStyle={{ color: "#94A3B8" }}
              />
              <Area type="monotone" dataKey="benchmark" stroke="#64748B" strokeWidth={1.5} fill="none" dot={false} isAnimationActive={false} />
              <Area type="monotone" dataKey="portfolio" stroke="#38BDF8" strokeWidth={2} fill="url(#gPort)" dot={false} isAnimationActive={false} />
            </AreaChart>
          </ResponsiveContainer>
        </Card>

        {/* Allocation */}
        <Card className="lg:col-span-4 p-6">
          <SectionLabel>Asset Allocation</SectionLabel>
          <div className="relative mt-2">
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={data.allocation} dataKey="value" nameKey="sector" innerRadius={58} outerRadius={82} paddingAngle={2} stroke="none" isAnimationActive={false}>
                  {data.allocation.map((_, i) => (
                    <Cell key={i} fill={SECTOR_COLORS[i % SECTOR_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(v) => `CHF ${fmtCompact(v)}`}
                  contentStyle={{ background: "#1A202C", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 10, fontSize: 12 }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="space-y-2 mt-3">
            {data.allocation.map((a, i) => (
              <div key={a.sector} className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-2 text-muted-2">
                  <span className="w-2.5 h-2.5 rounded-sm" style={{ background: SECTOR_COLORS[i % SECTOR_COLORS.length] }} />
                  {a.sector}
                </span>
                <span className="font-mono text-xs">{fmtNum(a.weight, 1)}%</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Holdings table */}
      <Card className="p-0 overflow-hidden" data-testid="portfolio-holdings-table">
        <div className="px-6 pt-5 pb-3 border-b border-hair">
          <SectionLabel>Holdings</SectionLabel>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-muted-3 text-xs">
                <th className="px-6 py-3 font-medium">Security</th>
                <th className="px-4 py-3 font-medium">Sector</th>
                <th className="px-4 py-3 font-medium text-right">Qty</th>
                <th className="px-4 py-3 font-medium text-right">Price</th>
                <th className="px-4 py-3 font-medium text-right">Day</th>
                <th className="px-4 py-3 font-medium text-right">Mkt Value</th>
                <th className="px-4 py-3 font-medium text-right">P&L</th>
                <th className="px-6 py-3 font-medium text-right">Weight</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)]">
              {data.positions.map((p, i) => (
                <motion.tr
                  key={p.ticker}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.02 }}
                  className="hover:bg-sky-500/[0.04] transition-colors duration-150"
                >
                  <td className="px-6 py-3">
                    <p className="font-mono text-xs text-sky-400">{p.ticker}</p>
                    <p className="text-muted-2 text-xs mt-0.5 max-w-[180px] truncate">{p.name}</p>
                  </td>
                  <td className="px-4 py-3 text-muted-2 text-xs">{p.sector}</td>
                  <td className="px-4 py-3 text-right font-mono text-xs">{fmtNum(p.quantity, 0)}</td>
                  <td className="px-4 py-3 text-right font-mono text-xs">{fmtNum(p.price)}</td>
                  <td className={`px-4 py-3 text-right font-mono text-xs ${changeColor(p.changePct)}`}>{fmtPct(p.changePct)}</td>
                  <td className="px-4 py-3 text-right font-mono text-xs">{fmtCompact(p.marketValue)}</td>
                  <td className={`px-4 py-3 text-right font-mono text-xs ${changeColor(p.pnl)}`}>{fmtPct(p.pnlPct)}</td>
                  <td className="px-6 py-3 text-right font-mono text-xs text-muted-2">{fmtNum(p.weight, 1)}%</td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
