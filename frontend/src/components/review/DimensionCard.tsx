import { asText, normalizeScore } from "../../lib/format";

interface DimensionCardProps {
  name?: string;
  dimension?: string;
  score: number;
  weight?: number;
  summary?: string;
  reasoning?: string;
  evidence?: unknown[];
}

function scoreColor(score: number) {
  if (score >= 80) return "text-emerald-600";
  if (score >= 60) return "text-amber-600";
  return "text-rose-600";
}

function scoreBackground(score: number) {
  if (score >= 80) return "bg-emerald-50";
  if (score >= 60) return "bg-amber-50";
  return "bg-rose-50";
}

export function DimensionCard({
  name,
  dimension,
  score,
  weight,
  summary,
  reasoning,
  evidence,
}: DimensionCardProps) {
  const value = normalizeScore(score);
  const title = name || dimension || "Analysis dimension";
  const description = summary || reasoning;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition-all duration-200 hover:-translate-y-1 hover:shadow-lg">
      <div className="flex items-start justify-between">
        <div className="min-w-0">
          <h3 className="text-base font-semibold text-slate-900">
            {title.replaceAll("_", " ")}
          </h3>

          {weight !== undefined && (
            <p className="mt-1 text-xs text-slate-400">
              Weight {weight}%
            </p>
          )}
        </div>

        <div
          className={`rounded-xl px-4 py-2 ${scoreBackground(score)}`}
        >
          <div
            className={`text-2xl font-bold ${scoreColor(score)}`}
          >
            {value}
          </div>

          <div className="text-center text-xs text-slate-500">
            /100
          </div>
        </div>
      </div>

      {description && (
        <p className="mt-5 text-sm leading-7 text-slate-600">
          {description}
        </p>
      )}

      {evidence && evidence.length > 0 && (
        <div className="mt-5 border-t border-slate-100 pt-4">
          <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
            Evidence
          </p>

          <ul className="space-y-2">
            {evidence.map((item, index) => (
              <li
                key={index}
                className="flex gap-2 text-sm text-slate-600"
              >
                <span className="mt-1 h-2 w-2 rounded-full bg-blue-600" />
                <span>{asText(item)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
