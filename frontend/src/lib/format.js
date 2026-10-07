export const fmtNum = (n, d = 2) =>
  n === null || n === undefined || isNaN(n)
    ? "—"
    : Number(n).toLocaleString("en-CH", { minimumFractionDigits: d, maximumFractionDigits: d });

export const fmtCur = (n, cur = "CHF", d = 2) =>
  n === null || n === undefined || isNaN(n) ? "—" : `${cur} ${fmtNum(n, d)}`;

export const fmtCompact = (n) => {
  if (n === null || n === undefined || isNaN(n) || n === 0) return "—";
  const abs = Math.abs(n);
  if (abs >= 1e12) return (n / 1e12).toFixed(2) + "T";
  if (abs >= 1e9) return (n / 1e9).toFixed(2) + "B";
  if (abs >= 1e6) return (n / 1e6).toFixed(2) + "M";
  if (abs >= 1e3) return (n / 1e3).toFixed(1) + "K";
  return n.toFixed(0);
};

export const fmtPct = (n, d = 2) =>
  n === null || n === undefined || isNaN(n) ? "—" : `${n > 0 ? "+" : ""}${Number(n).toFixed(d)}%`;

export const changeColor = (n) =>
  n > 0 ? "text-emerald-400" : n < 0 ? "text-rose-400" : "text-slate-400";

export const timeAgo = (iso) => {
  if (!iso) return "—";
  const s = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
};
