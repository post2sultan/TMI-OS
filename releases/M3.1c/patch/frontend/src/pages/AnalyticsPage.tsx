import { useQuery } from "@tanstack/react-query";
import { BarChart3, Database, Gauge, ShieldCheck } from "lucide-react";
import { ErrorState, LoadingState } from "../components/shared/LiveState";
import { MetricCard } from "../components/shared/MetricCard";
import { api } from "../lib/api";
import { formatPercent, normalizeScore } from "../lib/format";

export function AnalyticsPage() {
  const campaigns = useQuery({
    queryKey: ["campaigns"],
    queryFn: () => api.listCampaigns(),
  });
  const reviews = useQuery({
    queryKey: ["reviews"],
    queryFn: api.listReviews,
  });

  if (
    campaigns.isLoading ||
    reviews.isLoading ||
    !campaigns.data ||
    !reviews.data
  ) {
    return <LoadingState label="Calculating live analytics..." />;
  }

  if (campaigns.isError || reviews.isError) {
    return (
      <ErrorState
        message="Analytics could not be calculated from the backend."
        onRetry={() => {
          void campaigns.refetch();
          void reviews.refetch();
        }}
      />
    );
  }

  const items = reviews.data.items;
  const averageScore =
    items.length === 0
      ? 0
      : items.reduce((sum, item) => sum + item.total_score, 0) / items.length;
  const averageConfidence =
    items.length === 0
      ? 0
      : items.reduce((sum, item) => sum + item.confidence, 0) / items.length;
  const approved = items.filter((item) =>
    `${item.review_status} ${item.campaign_status ?? ""}`
      .toLowerCase()
      .includes("approv"),
  ).length;
  const approvalRate = items.length === 0 ? 0 : approved / items.length;

  const sources = campaigns.data.items.reduce<Record<string, number>>(
    (accumulator, campaign) => {
      accumulator[campaign.source] = (accumulator[campaign.source] ?? 0) + 1;
      return accumulator;
    },
    {},
  );

  const sourceRows = Object.entries(sources).sort((a, b) => b[1] - a[1]);

  return (
    <div className="space-y-7">
      <header>
        <p className="text-sm font-semibold text-blue-700">LIVE PERFORMANCE</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
          Analytics
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          Calculated directly from current campaign and review records.
        </p>
      </header>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Campaigns"
          value={campaigns.data.total}
          detail="Total stored campaign records"
          icon={Database}
        />
        <MetricCard
          label="Analyses"
          value={reviews.data.total}
          detail="Review records generated"
          icon={BarChart3}
        />
        <MetricCard
          label="Average Score"
          value={normalizeScore(averageScore)}
          detail="Across available analyses"
          icon={Gauge}
        />
        <MetricCard
          label="Approval Rate"
          value={formatPercent(approvalRate)}
          detail={`Average confidence ${formatPercent(averageConfidence)}`}
          icon={ShieldCheck}
        />
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="font-semibold text-slate-950">Campaign sources</h2>
        <p className="mt-1 text-sm text-slate-500">
          Distribution of records by stored source.
        </p>
        {sourceRows.length === 0 ? (
          <p className="mt-6 text-sm text-slate-500">No source data available.</p>
        ) : (
          <div className="mt-5 space-y-4">
            {sourceRows.map(([source, count]) => {
              const percentage =
                campaigns.data.total === 0
                  ? 0
                  : (count / campaigns.data.total) * 100;
              return (
                <div key={source}>
                  <div className="mb-2 flex items-center justify-between text-sm">
                    <span className="font-medium text-slate-700">{source}</span>
                    <span className="text-slate-500">{count}</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-blue-700"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
