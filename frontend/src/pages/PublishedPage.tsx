import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Copy, Download, LoaderCircle } from "lucide-react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import {
  ErrorState,
  LoadingState,
  NoDataState,
} from "../components/shared/LiveState";
import { api } from "../lib/api";
import { formatDate, normalizeScore } from "../lib/format";

export function PublishedPage() {
  const queryClient = useQueryClient();
  const published = useQuery({
    queryKey: ["reviews", "published"],
    queryFn: () => api.listReviews("published"),
  });
  const jobs = useQuery({
    queryKey: ["content-creation"],
    queryFn: api.listContentCreationJobs,
  });
  const exportPackage = useMutation({
    mutationFn: api.exportSocialPackage,
    onSuccess: async (response, campaignId) => {
      await queryClient.invalidateQueries({ queryKey: ["content-creation"] });
      const exported = response.items.find(
        (job) => job.campaign_id === campaignId,
      );
      if (exported) {
        window.location.assign(exported.social_export_url);
      }
      toast.success("Social publishing package ready.");
    },
    onError: (error: Error) => toast.error(error.message),
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
              <article
                key={item.analysis_id}
                className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm hover:border-blue-300"
              >
                <div className="flex items-start justify-between gap-4">
                  <Link
                    to={`/campaigns/${item.campaign_id}`}
                    className="font-semibold text-slate-950 hover:text-blue-700"
                  >
                    {item.campaign_title}
                  </Link>
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
                {job?.video_url ? (
                  <div className="mt-4 space-y-3 border-t border-slate-100 pt-4">
                    <video
                      controls
                      preload="metadata"
                      className="mx-auto max-h-80 rounded-xl bg-slate-950"
                      src={job.video_url}
                    />
                    <p className="text-sm leading-6 text-slate-700">
                      {job.social_caption}
                    </p>
                    <p className="text-sm font-medium text-blue-700">
                      {job.hashtags.join(" ")}
                    </p>
                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        onClick={() => {
                          void navigator.clipboard.writeText(
                            `${job.social_caption}\n\n${job.hashtags.join(" ")}`,
                          );
                          toast.success("Caption copied.");
                        }}
                        className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm font-semibold"
                      >
                        <Copy className="h-4 w-4" />
                        Copy caption
                      </button>
                      {job.social_export_url ? (
                        <a
                          href={job.social_export_url}
                          download
                          className="inline-flex items-center gap-2 rounded-xl bg-blue-700 px-3 py-2 text-sm font-semibold text-white"
                        >
                          <Download className="h-4 w-4" />
                          Download package
                        </a>
                      ) : (
                        <button
                          type="button"
                          disabled={exportPackage.isPending}
                          onClick={() => exportPackage.mutate(item.campaign_id)}
                          className="inline-flex items-center gap-2 rounded-xl bg-blue-700 px-3 py-2 text-sm font-semibold text-white disabled:opacity-50"
                        >
                          {exportPackage.isPending ? (
                            <LoaderCircle className="h-4 w-4 animate-spin" />
                          ) : (
                            <Download className="h-4 w-4" />
                          )}
                          Create publishing package
                        </button>
                      )}
                    </div>
                  </div>
                ) : null}
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
