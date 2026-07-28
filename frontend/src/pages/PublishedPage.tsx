import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  ErrorState,
  LoadingState,
  NoDataState,
} from "../components/shared/LiveState";
import { api } from "../lib/api";
import { formatDate, normalizeScore } from "../lib/format";

export function PublishedPage() {
  const published = useQuery({
    queryKey: ["reviews", "published"],
    queryFn: () => api.listReviews("published"),
  });
  const jobs = useQuery({
    queryKey: ["content-creation"],
    queryFn: api.listContentCreationJobs,
  });

  if (published.isLoading || jobs.isLoading) {
    return <LoadingState label="Loading published campaigns..." />;
  }
  if (published.isError || jobs.isError || !published.data || !jobs.data) {
    return (
      <ErrorState
        message="Published campaigns could not be loaded."
        onRetry={() => {
          void published.refetch();
          void jobs.refetch();
        }}
      />
    );
  }

  const jobsByCampaign = new Map(
    jobs.data.items.map((job) => [job.campaign_id, job]),
  );

  return (
    <div className="space-y-7">
      <header>
        <p className="text-sm font-semibold text-blue-700">DISTRIBUTION</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
          Published
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          Published campaigns and their content-creation records.
        </p>
      </header>
      {published.data.items.length === 0 ? (
        <NoDataState
          title="No published campaigns"
          description="Approve a campaign, then publish it from the Approved screen."
        />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {published.data.items.map((item) => {
            const job = jobsByCampaign.get(item.campaign_id);
            return (
              <Link
                key={item.analysis_id}
                to={`/campaigns/${item.campaign_id}`}
                className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm hover:border-blue-300"
              >
                <div className="flex items-start justify-between gap-4">
                  <h2 className="font-semibold text-slate-950">
                    {item.campaign_title}
                  </h2>
                  <span className="rounded-full bg-blue-100 px-2.5 py-1 text-xs font-bold uppercase text-blue-800">
                    Published
                  </span>
                </div>
                <p className="mt-3 line-clamp-3 text-sm leading-6 text-slate-600">
                  {item.summary}
                </p>
                <div className="mt-5 flex flex-wrap justify-between gap-2 text-xs text-slate-400">
                  <span>Score {normalizeScore(item.total_score)}</span>
                  <span>Content log: {job?.status ?? "published"}</span>
                  <span>{formatDate(job?.published_at ?? item.created_at)}</span>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
