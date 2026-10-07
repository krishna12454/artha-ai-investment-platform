import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import {
  BrainCircuit,
  Search,
  TrendingUp,
  TrendingDown,
  ShieldAlert,
  Sparkles,
  ArrowRight,
  FileDown,
} from "lucide-react";
import { fetchers, pdfUrls, downloadFile } from "../lib/api";
import { fmtNum, fmtPct, changeColor } from "../lib/format";
import { Card, SectionLabel, Spinner, ViewHeader, Pill } from "../components/ui-kit";

const ratingTone = (r) =>
  r === "Buy" ? "bull" : r === "Sell" ? "bear" : "warn";

export default function ValuationView() {
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(null);
  const [result, setResult] = useState(null);
  const [running, setRunning] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["securities"],
    queryFn: fetchers.securities,
    refetchInterval: 8000,
  });

  const securities = data?.securities || [];
  const filtered = query
    ? securities.filter(
        (s) =>
          s.ticker.toLowerCase().includes(query.toLowerCase()) ||
          s.name.toLowerCase().includes(query.toLowerCase())
      )
    : securities;

  const runValuation = async (ticker) => {
    setRunning(true);
    setResult(null);
    try {
      const r = await fetchers.runValuation(ticker);
      setResult(r);
      toast.success(`${r.rating} · ${r.name}`, { description: `Fair value ${r.currency} ${fmtNum(r.fairValue)}` });
    } catch (e) {
      toast.error("Valuation engine error", { description: e?.response?.data?.detail || "Please retry" });
    } finally {
      setRunning(false);
    }
  };

  if (isLoading) return <Spinner label="Loading universe" />;

  return (
    <div>
      <ViewHeader
        eyebrow="Claude Sonnet Engine"
        title="AI Investment Valuation"
        desc="Select a security to run an automated fair-value check. The AI engine synthesises fundamentals from the simulated Bloomberg feed into a research-desk thesis with bull/bear scenarios and key risks."
      />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Security picker */}
        <Card className="lg:col-span-4 p-0 overflow-hidden h-fit">
          <div className="p-4 border-b border-hair">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-3" />
              <input
                data-testid="portfolio-security-search-input"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search ticker or name…"
                className="w-full surface-2 border-hair rounded-lg pl-9 pr-3 py-2 text-sm outline-none focus:border-sky-500/50 transition-colors duration-150"
              />
            </div>
          </div>
          <div className="max-h-[520px] overflow-y-auto divide-y divide-[var(--border)]">
            {filtered.map((s) => (
              <button
                key={s.ticker}
                data-testid={`security-row-${s.ticker}`}
                onClick={() => {
                  setSelected(s.ticker);
                  runValuation(s.ticker);
                }}
                className={`w-full text-left px-4 py-3 flex items-center justify-between hover:bg-sky-500/[0.05] transition-colors duration-150 ${
                  selected === s.ticker ? "bg-sky-500/[0.08]" : ""
                }`}
              >
                <div>
                  <p className="font-mono text-xs text-sky-400">{s.ticker}</p>
                  <p className="text-xs text-muted-2 mt-0.5 max-w-[150px] truncate">{s.name}</p>
                </div>
                <div className="text-right">
                  <p className="font-mono text-xs">{fmtNum(s.price)}</p>
                  <p className={`font-mono text-xs mt-0.5 ${changeColor(s.changePct)}`}>{fmtPct(s.changePct)}</p>
                </div>
              </button>
            ))}
          </div>
        </Card>

        {/* Result panel */}
        <div className="lg:col-span-8">
          <AnimatePresence mode="wait">
            {running ? (
              <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <Card className="p-10">
                  <div className="flex flex-col items-center justify-center text-center py-10">
                    <div className="relative mb-5">
                      <BrainCircuit className="w-10 h-10 text-sky-400 animate-pulse" />
                    </div>
                    <p className="font-heading text-lg font-semibold">Running valuation check…</p>
                    <p className="text-muted-2 text-sm mt-1">Claude Sonnet is analysing fundamentals & building the thesis</p>
                  </div>
                </Card>
              </motion.div>
            ) : result ? (
              <motion.div
                key={result.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                data-testid="valuation-result-panel"
              >
                <div className="flex items-center justify-between mb-4">
                  <SectionLabel>Valuation Report</SectionLabel>
                  <button
                    data-testid="valuation-export-pdf-button"
                    onClick={() => downloadFile(pdfUrls.valuation(result.id))}
                    className="flex items-center gap-1.5 surface-2 border-hair hover:border-sky-500/40 text-muted-2 hover:text-[var(--text)] text-xs font-medium px-3 py-1.5 rounded-full transition-colors duration-150"
                  >
                    <FileDown className="w-3.5 h-3.5" /> Export PDF
                  </button>
                </div>
                <Card className="p-6 mb-6">
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <p className="font-mono text-xs text-sky-400">{result.ticker}</p>
                      <h2 className="font-heading text-2xl font-semibold tracking-tight mt-1">{result.name}</h2>
                      <div className="flex items-center gap-2 mt-3">
                        <Pill tone={ratingTone(result.rating)} className="text-sm px-3 py-1" data-testid="valuation-rating-badge">
                          {result.rating === "Buy" ? <TrendingUp className="w-3.5 h-3.5" /> : result.rating === "Sell" ? <TrendingDown className="w-3.5 h-3.5" /> : <ArrowRight className="w-3.5 h-3.5" />}
                          {result.rating}
                        </Pill>
                        <Pill tone="muted">Confidence · {result.confidence}</Pill>
                        <Pill tone="muted" title={result.engine}>
                          {result.engine?.startsWith("Claude") ? "Claude · Anthropic" : "Quant model"}
                        </Pill>
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-5 text-right">
                      <div>
                        <SectionLabel>Price</SectionLabel>
                        <p className="font-mono text-lg font-semibold mt-1">{fmtNum(result.price)}</p>
                      </div>
                      <div>
                        <SectionLabel>Fair Value</SectionLabel>
                        <p className="font-mono text-lg font-semibold mt-1 text-sky-400">{fmtNum(result.fairValue)}</p>
                      </div>
                      <div>
                        <SectionLabel>Upside</SectionLabel>
                        <p className={`font-mono text-lg font-semibold mt-1 ${changeColor(result.upsidePct)}`}>{fmtPct(result.upsidePct)}</p>
                      </div>
                    </div>
                  </div>

                  <div className="mt-6 p-4 surface-2 rounded-lg border-hair">
                    <SectionLabel className="flex items-center gap-1.5"><Sparkles className="w-3 h-3" /> Investment Thesis</SectionLabel>
                    <p className="text-sm leading-relaxed mt-2 text-muted-2">{result.thesis}</p>
                    {result.valuationNote && (
                      <p className="text-xs leading-relaxed mt-3 text-muted-3 italic">{result.valuationNote}</p>
                    )}
                  </div>
                </Card>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Card className="p-5">
                    <SectionLabel className="flex items-center gap-1.5 text-emerald-400"><TrendingUp className="w-3.5 h-3.5" /> Bull Case</SectionLabel>
                    <ul className="mt-3 space-y-2">
                      {result.bullCase?.map((b, i) => (
                        <li key={i} className="flex gap-2 text-sm text-muted-2">
                          <span className="text-emerald-400 mt-0.5">▸</span> {b}
                        </li>
                      ))}
                    </ul>
                  </Card>
                  <Card className="p-5">
                    <SectionLabel className="flex items-center gap-1.5 text-rose-400"><TrendingDown className="w-3.5 h-3.5" /> Bear Case</SectionLabel>
                    <ul className="mt-3 space-y-2">
                      {result.bearCase?.map((b, i) => (
                        <li key={i} className="flex gap-2 text-sm text-muted-2">
                          <span className="text-rose-400 mt-0.5">▸</span> {b}
                        </li>
                      ))}
                    </ul>
                  </Card>
                </div>

                <Card className="p-5 mt-6">
                  <SectionLabel className="flex items-center gap-1.5 text-amber-400"><ShieldAlert className="w-3.5 h-3.5" /> Key Risks</SectionLabel>
                  <div className="flex flex-wrap gap-2 mt-3">
                    {result.keyRisks?.map((r, i) => (
                      <Pill key={i} tone="warn">{r}</Pill>
                    ))}
                  </div>
                </Card>
              </motion.div>
            ) : (
              <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <Card className="p-10">
                  <div className="flex flex-col items-center justify-center text-center py-16">
                    <BrainCircuit className="w-12 h-12 text-muted-3 mb-4" strokeWidth={1.25} />
                    <p className="font-heading text-lg font-semibold">Select a security to begin</p>
                    <p className="text-muted-2 text-sm mt-1 max-w-sm">
                      Choose any instrument from the universe to generate an AI-powered fair-value assessment and research thesis.
                    </p>
                  </div>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
