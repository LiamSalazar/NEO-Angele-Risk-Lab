import type { RiskCategory } from "@/api/types";

export type RiskTone = {
  label: string;
  textClass: string;
  borderClass: string;
  bgClass: string;
  hex: string;
};

const fallback: RiskTone = {
  label: "Unknown",
  textClass: "text-slate-200",
  borderClass: "border-slate-500/35",
  bgClass: "bg-slate-500/10",
  hex: "#aeb8c5"
};

export const RISK_TONES: Record<string, RiskTone> = {
  low: {
    label: "Low",
    textClass: "text-emerald-200",
    borderClass: "border-emerald-300/30",
    bgClass: "bg-emerald-300/10",
    hex: "#8ff0c1"
  },
  moderate: {
    label: "Moderate",
    textClass: "text-cyan-200",
    borderClass: "border-cyan-300/35",
    bgClass: "bg-cyan-300/10",
    hex: "#42f2ff"
  },
  elevated: {
    label: "Elevated",
    textClass: "text-amber-200",
    borderClass: "border-amber-300/35",
    bgClass: "bg-amber-300/10",
    hex: "#f7c75f"
  },
  high: {
    label: "High",
    textClass: "text-orange-200",
    borderClass: "border-orange-300/35",
    bgClass: "bg-orange-300/10",
    hex: "#ff9a5c"
  },
  critical: {
    label: "Critical",
    textClass: "text-rose-200",
    borderClass: "border-rose-300/40",
    bgClass: "bg-rose-300/10",
    hex: "#ff5d73"
  }
};

export const normalizeCategory = (category?: RiskCategory | null) =>
  String(category || "unknown").trim().toLowerCase();

export const riskTone = (category?: RiskCategory | null) =>
  RISK_TONES[normalizeCategory(category)] ?? fallback;

export const scoreToCategory = (score?: number | null) => {
  const value = Number(score);
  if (!Number.isFinite(value)) {
    return "unknown";
  }
  if (value < 20) return "low";
  if (value < 40) return "moderate";
  if (value < 60) return "elevated";
  if (value < 80) return "high";
  return "critical";
};

export const scoreColor = (score?: number | null, category?: RiskCategory | null) =>
  riskTone(category || scoreToCategory(score)).hex;
