export function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function formatPercent(value: number): string {
  const normalized = value <= 1 ? value * 100 : value;
  return `${Math.round(normalized)}%`;
}

export function normalizeScore(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

export function asText(value: unknown): string {
  if (typeof value === "string") return value;
  if (value === null || value === undefined) return "";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
