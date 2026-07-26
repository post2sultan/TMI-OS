import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { ErrorState, LoadingState, NoDataState } from "../components/shared/LiveState";
import { api } from "../lib/api";
import { formatDate, normalizeScore } from "../lib/format";

export function ApprovedPage() {
  const reviews = useQuery({
    queryKey: ["reviews"],
    queryFn: api.listReviews,
  });

  if (reviews.isLoading || !reviews.data) {
    return <LoadingState label="Loading approved campaigns..." />;
  }
  if (reviews.isError) {
    return (
      <ErrorState
        message="Approved campaigns could not be loaded."
        onRetry={() => void reviews.refetch()}
      />
    );
  }

  const approved = reviews.data.items.filter((item) =>
    `${item.review_status} ${item.campaign_status ?? ""}`
      .toLowerCase()
      .includes("approv"),
  );

  return (
    <div className="space-y-7">
      <header>
        <p className="text-sm font-semibold text-emerald-700">GOVERNED OUTPUT</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
          Approved
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          Campaign analyses approved through the live review workflow.
        </p>
      </header>

      {approved.length === 0 ? (
        <NoDataState
          title="No approved campaigns"
          description="Approved review records will appear here."
        />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {approved.map((item) => (
            <Link
              key={item.analysis_id}
              to={`/campaigns/${item.campaign_id}`}
              className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm hover:border-emerald-300"
            >
              <div className="flex items-start justify-between gap-4">
                <h2 className="font-semibold text-slate-950">
                  {item.campaign_title}
                </h2>
                <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-bold uppercase text-emerald-800">
                  Approved
                </span>
              </div>
              <p className="mt-3 line-clamp-3 text-sm leading-6 text-slate-600">
                {item.summary}
              </p>
              <div className="mt-5 flex items-center justify-between text-xs text-slate-400">
                <span>Score {normalizeScore(item.total_score)}</span>
                <span>{formatDate(item.created_at)}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
