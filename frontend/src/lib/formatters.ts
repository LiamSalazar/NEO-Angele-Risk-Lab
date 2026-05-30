import type { RiskObject } from "@/api/types";

export const formatNumber = (
  value: unknown,
  options: Intl.NumberFormatOptions = { maximumFractionDigits: 2 }
) => {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return "n/a";
  }
  return new Intl.NumberFormat("en-US", options).format(numeric);
};

export const formatPercent = (value: unknown, maximumFractionDigits = 1) => {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return "n/a";
  }
  return `${new Intl.NumberFormat("en-US", { maximumFractionDigits }).format(numeric * 100)}%`;
};

export const formatScore = (value: unknown) =>
  formatNumber(value, { minimumFractionDigits: 1, maximumFractionDigits: 1 });

export const formatBoolean = (value: unknown) => {
  if (typeof value === "boolean") {
    return value ? "yes" : "no";
  }
  if (typeof value === "number") {
    return value === 1 ? "yes" : value === 0 ? "no" : "n/a";
  }
  if (typeof value === "string") {
    const normalized = value.toLowerCase();
    if (["true", "1", "yes", "y"].includes(normalized)) {
      return "yes";
    }
    if (["false", "0", "no", "n"].includes(normalized)) {
      return "no";
    }
  }
  return "n/a";
};

export const objectDisplayName = (object?: RiskObject | null) => {
  if (!object) {
    return "Unknown object";
  }
  return String(object.full_name || object.name || object.des || object.object_key || object.spkid);
};

export const objectKey = (object?: RiskObject | null) => {
  if (!object) {
    return "";
  }
  return String(object.object_key || object.spkid || object.des || object.full_name || object.name || "");
};

export const formatTimestamp = (value?: string | null) => {
  if (!value) {
    return "No timestamp";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(date);
};

export const compactPath = (path?: string) => {
  if (!path) {
    return "n/a";
  }
  const parts = path.replace(/\\/g, "/").split("/");
  return parts.slice(-3).join("/");
};
