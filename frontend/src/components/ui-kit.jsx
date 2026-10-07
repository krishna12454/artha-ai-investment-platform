import React from "react";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";

export const Card = ({ className = "", children, ...props }) => (
  <div
    className={`surface border-hair rounded-xl ${className}`}
    {...props}
  >
    {children}
  </div>
);

export const SectionLabel = ({ children, className = "" }) => (
  <p className={`overline ${className}`}>{children}</p>
);

export const Pill = ({ tone = "neutral", children, className = "", ...rest }) => {
  const tones = {
    bull: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    bear: "bg-rose-500/10 text-rose-400 border-rose-500/20",
    neutral: "bg-sky-500/10 text-sky-400 border-sky-500/20",
    warn: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    muted: "bg-slate-500/10 text-slate-400 border-slate-500/20",
  };
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${tones[tone]} ${className}`}
      {...rest}
    >
      {children}
    </span>
  );
};

export const MetricCard = ({ label, value, sub, subTone = "", icon: Icon, testid, delay = 0 }) => (
  <motion.div
    initial={{ opacity: 0, y: 12 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.3, delay }}
    data-testid={testid}
  >
    <Card className="p-5 h-full">
      <div className="flex items-start justify-between">
        <SectionLabel>{label}</SectionLabel>
        {Icon && <Icon className="w-4 h-4 text-muted-3" strokeWidth={1.75} />}
      </div>
      <p className="font-mono text-2xl font-semibold mt-3 tracking-tight">{value}</p>
      {sub && <p className={`text-sm mt-1 font-mono ${subTone}`}>{sub}</p>}
    </Card>
  </motion.div>
);

export const Spinner = ({ label = "Loading" }) => (
  <div className="flex items-center justify-center gap-3 py-20 text-muted-2">
    <Loader2 className="w-5 h-5 animate-spin text-sky-400" />
    <span className="text-sm">{label}…</span>
  </div>
);

export const ViewHeader = ({ eyebrow, title, desc }) => (
  <motion.div
    initial={{ opacity: 0, y: 8 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.25 }}
    className="mb-6"
  >
    <SectionLabel className="text-sky-400">{eyebrow}</SectionLabel>
    <h1 className="font-heading text-3xl sm:text-4xl font-semibold tracking-tight mt-1">{title}</h1>
    {desc && <p className="text-muted-2 mt-2 max-w-2xl text-sm">{desc}</p>}
  </motion.div>
);

export const statusTone = (s) => {
  const map = {
    healthy: "bull",
    operational: "bull",
    pass: "bull",
    degraded: "warn",
    warn: "warn",
    failed: "bear",
    down: "bear",
    fail: "bear",
  };
  return map[s] || "neutral";
};
