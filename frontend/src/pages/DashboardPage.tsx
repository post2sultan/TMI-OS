import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  BadgeCheck,
  Database,
  Radar,
} from "lucide-react";
import { Link } from "react-router-dom";
import { ErrorState, LoadingState, NoDataState } from "../components/shared/LiveState";
import { MetricCard } from "../components/shared/MetricCard";
import { api } from "../lib/api";
import { formatDate, normalizeScore } from "../lib/format";

export function DashboardPage() {
  const campaigns = useQuery({
    queryKey: ["campaigns"],
    queryFn: () => api.listCampaigns(),
  });
  const reviews = useQuery({
    queryKey: ["reviews"],
    queryFn: api.listReviews,
  });
  const health = useQuery({
    queryKey: ["health"],
    queryFn: api.health,
    refetchInterval: 30000,
  });

  if (campaigns.isLoading || reviews.isLoading) {
    return <LoadingState label="Loading TMI command centre..." />;
  }

  if (campaigns.isError || reviews.isError) {
    return (
      <ErrorState
        message="The dashboard could not reach the live backend."
        onRetry={() => {
          void campaigns.refetch();
          void reviews.refetch();
        }}
      />
    );
  }

  const campaignItems = campaigns.data?.items ?? [];
  const reviewItems = reviews.data?.items ?? [];
  const approved = reviewItems.filter((item) =>
    `${item.review_status} ${item.campaign_status ?? ""}`
      .toLowerCase()
      .includes("approv"),
  ).length;
  const pending = reviewItems.filter((item) =>
    `${item.review_status}`.toLowerCase().includes("pending"),
  ).length;
  const latest = [...reviewItems]
    .sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at))
    .slice(0, 5);

  return (
    <div className="space-y-7">
      <header>
        <p className="text-sm font-semibold text-blue-700">LIVE OPERATIONS</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
          Dashboard
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          Real-time campaign discovery, analysis and review activity.
        </p>
      </header>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Campaigns"
          value={campaigns.data?.total ?? 0}
          detail="Stored in the live campaign library"
          icon={Database}
        />
        <MetricCard
          label="Review Queue"
          value={pending}
          detail="Campaigns awaiting a decision"
          icon={Radar}
        />
        <MetricCard
          label="Approved"
          value={approved}
          detail="Approved review records"
          icon={BadgeCheck}
        />
        <MetricCard
          label="Backend"
          value={health.isSuccess ? "Online" : "Checking"}
          detail="FastAPI service connection"
          icon={Activity}
        />
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
          <div>
            <h2 className="font-semibold text-slate-950">Latest reviews</h2>
            <p className="mt-1 text-sm text-slate-500">
              Most recent analysis records from the backend.
            </p>
          </div>
          <Link
            to="/review-queue"
            className="text-sm font-semibold text-blue-700 hover:text-blue-900"
          >
            Open queue
          </Link>
        </div>

        {latest.length === 0 ? (
          <div className="p-5">
            <NoDataState
              title="No reviews yet"
              description="Discover campaigns and run analysis to populate the review queue."
            />
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {latest.map((item) => (
              <Link
                key={item.analysis_id}
                to={`/campaigns/${item.campaign_id}`}
                className="grid gap-3 px-5 py-4 hover:bg-slate-50 md:grid-cols-[1fr_auto_auto]"
              >
                <div>
                  <p className="font-semibold text-slate-900">
                    {item.campaign_title}
                  </p>
                  <p className="mt-1 line-clamp-1 text-sm text-slate-500">
                    {item.summary}
                  </p>
                </div>
                <div className="text-sm">
                  <span className="font-semibold text-slate-900">
                    {normalizeScore(item.total_score)}
                  </span>
                  <span className="ml-1 text-slate-500">score</span>
                </div>
                <time className="text-sm text-slate-500">
                  {formatDate(item.created_at)}
                </time>
              </Link>
            ))}
          </div>
        )}
      </section>

      <p className="text-xs text-slate-400">
        Loaded {campaignItems.length} campaign records in this view.
      </p>
    </div>
  );
}
