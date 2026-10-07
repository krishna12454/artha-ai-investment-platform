import React from "react";
import { motion } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import {
  Briefcase,
  BrainCircuit,
  Newspaper,
  GitMerge,
  Activity,
  Sun,
  Moon,
  Radio,
} from "lucide-react";
import { useTheme } from "../context/ThemeContext";
import { fetchers } from "../lib/api";
import { timeAgo } from "../lib/format";

export const NAV = [
  { id: "portfolio", label: "Portfolio", icon: Briefcase },
  { id: "ai-valuation", label: "AI Valuation", icon: BrainCircuit },
  { id: "market-insights", label: "Market Intel", icon: Newspaper },
  { id: "data-pipelines", label: "Data Pipelines", icon: GitMerge },
  { id: "system-monitoring", label: "Reliability", icon: Activity },
];

export const Header = ({ active, onNavigate }) => {
  const { theme, toggle } = useTheme();
  const { data: feed } = useQuery({
    queryKey: ["feed"],
    queryFn: () => fetchers.securities().then((d) => d.feed),
    refetchInterval: 5000,
  });

  return (
    <header className="sticky top-0 z-50 backdrop-blur-xl border-b border-hair" style={{ background: "color-mix(in srgb, var(--bg) 80%, transparent)" }}>
      <div className="max-w-[1500px] mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg grid place-items-center surface-2 border-hair">
              <span className="font-serif-brand text-xl leading-none text-sky-400">Ā</span>
            </div>
            <div className="leading-tight">
              <p className="font-heading font-semibold tracking-tight text-[15px]">
                Artha <span className="text-sky-400">AI</span>
              </p>
              <p className="text-[10px] text-muted-3 tracking-wide -mt-0.5">
                Investment Intelligence
              </p>
            </div>
          </div>

          {/* Nav */}
          <nav className="hidden lg:flex items-center gap-1 surface-2 border-hair rounded-full p-1">
            {NAV.map((n) => {
              const Icon = n.icon;
              const on = active === n.id;
              return (
                <button
                  key={n.id}
                  data-testid={`nav-${n.id}-tab`}
                  onClick={() => onNavigate(n.id)}
                  className="relative px-3.5 py-1.5 rounded-full text-sm font-medium transition-colors duration-150"
                >
                  {on && (
                    <motion.span
                      layoutId="nav-pill"
                      className="absolute inset-0 rounded-full bg-sky-500/15 border border-sky-500/30"
                      transition={{ type: "spring", stiffness: 380, damping: 30 }}
                    />
                  )}
                  <span className={`relative flex items-center gap-1.5 ${on ? "text-sky-300" : "text-muted-2 hover:text-[var(--text)]"}`}>
                    <Icon className="w-3.5 h-3.5" strokeWidth={2} />
                    {n.label}
                  </span>
                </button>
              );
            })}
          </nav>

          {/* Right */}
          <div className="flex items-center gap-2">
            <div className="hidden md:flex items-center gap-2 surface-2 border-hair rounded-full px-3 py-1.5" data-testid="live-feed-badge">
              <span className="relative inline-flex w-2 h-2">
                <span className="absolute inline-flex w-2 h-2 rounded-full bg-emerald-400 live-dot" />
                <span className="relative inline-flex w-2 h-2 rounded-full bg-emerald-400" />
              </span>
              <Radio className={`w-3.5 h-3.5 ${feed?.live ? "text-emerald-400" : "text-amber-400"}`} />
              <span className="text-[11px] font-mono text-muted-2">
                {feed ? (feed.live ? `LIVE ${feed.liveCount}/${feed.total}` : "SIM") : "—"}
              </span>
            </div>
            <button
              data-testid="theme-toggle-button"
              onClick={toggle}
              className="w-9 h-9 grid place-items-center rounded-full surface-2 border-hair text-muted-2 hover:text-[var(--text)] transition-colors duration-150"
              aria-label="Toggle theme"
            >
              {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Mobile nav */}
        <nav className="lg:hidden flex items-center gap-1 overflow-x-auto pb-2 -mx-1 px-1">
          {NAV.map((n) => {
            const Icon = n.icon;
            const on = active === n.id;
            return (
              <button
                key={n.id}
                data-testid={`nav-${n.id}-tab-mobile`}
                onClick={() => onNavigate(n.id)}
                className={`flex items-center gap-1.5 whitespace-nowrap px-3 py-1.5 rounded-full text-xs font-medium border transition-colors duration-150 ${
                  on ? "bg-sky-500/15 border-sky-500/30 text-sky-300" : "surface-2 border-hair text-muted-2"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {n.label}
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};
