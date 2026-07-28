import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileText, LoaderCircle, Send } from "lucide-react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { ErrorState, LoadingState, NoDataState } from "../components/shared/LiveState";
import { api } from "../lib/api";
import { formatDate, normalizeScore } from "../lib/format";

export function ApprovedPage() {
  const queryClient = useQueryClient();
  const reviews = useQuery({
    queryKey: ["reviews", "approved"],
    queryFn: () => api.listReviews("approved"),
  });
  const jobs = useQuery({
    queryKey: ["content-creation"],
    queryFn: api.listContentCreationJobs,
  });
  const publish = useMutation({
    mutationFn: api.publishCampaign,
    onSuccess: async () => {
      toast.success("Campaign published.");
      await queryClient.invalidateQueries({ queryKey: ["reviews"] });
      await queryClient.invalidateQueries({ queryKey: ["content-creation"] });
      await queryClient.invalidateQueries({ queryKey: ["campaigns"] });
    },
    onError: (error: Error) => toast.error(error.message),
  });
  const generate = useMutation({
    mutationFn: api.generateContentPackage,
    onSuccess: async () => {
      toast.success("Script and social copy generated.");
      await queryClient.invalidateQueries({ queryKey: ["content-creation"] });
    },
    onError: (error: Error) => toast.error(error.message),
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

  const approved = reviews.data.items;
  const jobByCampaign = new Map(
    (jobs.data?.items ?? []).map((job) => [job.campaign_id, job]),
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
            (() => {
              const job = jobByCampaign.get(item.campaign_id);
              const generated = Boolean(
                job?.video_script && job?.social_caption,
              );
              return (
            <article
              key={item.analysis_id}
              className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm hover:border-emerald-300"
            >
              <div className="flex items-start justify-between gap-4">
                <Link
                  to={`/campaigns/${item.campaign_id}`}
                  className="font-semibold text-slate-950 hover:text-blue-700"
                >
                  {item.campaign_title}
                </Link>
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
              <div className="mt-5 flex items-center justify-between border-t border-slate-100 pt-4">
                <span className="text-xs font-semibold uppercase text-blue-700">
                  Content {job?.status ?? "queued"}
                </span>
                <div className="flex gap-2">
                  <button
                    type="button"
                    disabled={generate.isPending}
                    onClick={() => generate.mutate(item.campaign_id)}
                    className="inline-flex items-center gap-2 rounded-xl border border-blue-200 px-4 py-2 text-sm font-semibold text-blue-700 hover:bg-blue-50 disabled:opacity-50"
                  >
                    {generate.isPending ? (
                      <LoaderCircle className="h-4 w-4 animate-spin" />
                    ) : (
                      <FileText className="h-4 w-4" />
                    )}
                    {generated ? "Regenerate" : "Generate content"}
                  </button>
                  <button
                    type="button"
                    disabled={!generated || publish.isPending}
                    onClick={() => publish.mutate(item.campaign_id)}
                    className="inline-flex items-center gap-2 rounded-xl bg-blue-700 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-800 disabled:opacity-50"
                  >
                    {publish.isPending ? (
                      <LoaderCircle className="h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="h-4 w-4" />
                    )}
                    Publish
                  </button>
                </div>
              </div>
              {generated ? (
                <div className="mt-4 space-y-3 rounded-xl bg-slate-50 p-4 text-sm text-slate-700">
                  <div>
                    <p className="font-semibold text-slate-950">Video script</p>
                    <p className="mt-1 whitespace-pre-wrap leading-6">
                      {job?.video_script}
                    </p>
                  </div>
                  <div>
                    <p className="font-semibold text-slate-950">Social caption</p>
                    <p className="mt-1 whitespace-pre-wrap leading-6">
                      {job?.social_caption}
                    </p>
                  </div>
                  <p className="font-medium text-blue-700">
                    {job?.hashtags.join(" ")}
                  </p>
                </div>
              ) : null}
            </article>
              );
            })()
          ))}
        </div>
      )}
    </div>
  );
}
