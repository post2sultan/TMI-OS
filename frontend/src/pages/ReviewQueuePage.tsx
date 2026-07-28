import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Check,
  LoaderCircle,
  RefreshCw,
  X,
} from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { ErrorState, LoadingState, NoDataState } from "../components/shared/LiveState";
import { api } from "../lib/api";
import { formatDate, formatPercent, normalizeScore } from "../lib/format";

const REVIEWER = "Sultan Salahuddin";

export function ReviewQueuePage() {
  const queryClient = useQueryClient();
  const [busyId, setBusyId] = useState<number | null>(null);

  const reviews = useQuery({
    queryKey: ["reviews", "pending"],
    queryFn: () => api.listReviews("pending"),
  });

  async function refresh() {
    await queryClient.invalidateQueries({ queryKey: ["reviews"] });
    await queryClient.invalidateQueries({ queryKey: ["campaigns"] });
  }

  const approve = useMutation({
    mutationFn: (campaignId: number) =>
      api.approveCampaign(campaignId, REVIEWER),
    onMutate: (campaignId) => setBusyId(campaignId),
    onSuccess: async () => {
      toast.success("Campaign approved.");
      await refresh();
    },
    onError: (error: Error) => toast.error(error.message),
    onSettled: () => setBusyId(null),
  });

  const reject = useMutation({
    mutationFn: ({
      campaignId,
      reason,
    }: {
      campaignId: number;
      reason: string;
    }) => api.rejectCampaign(campaignId, REVIEWER, reason),
    onMutate: ({ campaignId }) => setBusyId(campaignId),
    onSuccess: async () => {
      toast.success("Campaign rejected.");
      await refresh();
    },
    onError: (error: Error) => toast.error(error.message),
    onSettled: () => setBusyId(null),
  });

  const reanalyze = useMutation({
    mutationFn: api.reanalyzeCampaign,
    onMutate: (campaignId) => setBusyId(campaignId),
    onSuccess: async () => {
      toast.success("Campaign reanalysis completed.");
      await refresh();
    },
    onError: (error: Error) => toast.error(error.message),
    onSettled: () => setBusyId(null),
  });

  function rejectCampaign(campaignId: number) {
    const reason = window.prompt("Reason for rejection:");
    if (reason?.trim()) {
      reject.mutate({ campaignId, reason: reason.trim() });
    }
  }

  if (reviews.isLoading || !reviews.data) {
    return <LoadingState label="Loading live review queue..." />;
  }

  if (reviews.isError) {
    return (
      <ErrorState
        message="The review queue could not be loaded."
        onRetry={() => void reviews.refetch()}
      />
    );
  }

  const items = reviews.data.items;

  return (
    <div className="space-y-7">
      <header>
        <p className="text-sm font-semibold text-blue-700">HUMAN GOVERNANCE</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
          Review Queue
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          Approve, reject or re-run the latest campaign analyses.
        </p>
      </header>

      {items.length === 0 ? (
        <NoDataState
          title="Review queue is clear"
          description="No analysis records currently require review."
        />
      ) : (
        <div className="space-y-4">
          {items.map((item) => {
            const isBusy = busyId === item.campaign_id;
            return (
              <article
                key={item.analysis_id}
                className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
              >
                <div className="grid gap-5 xl:grid-cols-[1fr_auto]">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <Link
                        to={`/campaigns/${item.campaign_id}`}
                        className="text-lg font-semibold text-slate-950 hover:text-blue-700"
                      >
                        {item.campaign_title}
                      </Link>
                      <span className="rounded-full bg-amber-100 px-2.5 py-1 text-xs font-bold uppercase tracking-wide text-amber-800">
                        {item.review_status}
                      </span>
                    </div>
                    <p className="mt-3 max-w-4xl text-sm leading-6 text-slate-600">
                      {item.summary}
                    </p>

                    <div className="mt-5 flex flex-wrap gap-5 text-sm">
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                          Score
                        </p>
                        <p className="mt-1 font-bold text-slate-950">
                          {normalizeScore(item.total_score)}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                          Confidence
                        </p>
                        <p className="mt-1 font-bold text-slate-950">
                          {formatPercent(item.confidence)}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                          Created
                        </p>
                        <p className="mt-1 font-medium text-slate-700">
                          {formatDate(item.created_at)}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-wrap content-start gap-2 xl:max-w-72 xl:justify-end">
                    <button
                      type="button"
                      disabled={isBusy}
                      onClick={() => approve.mutate(item.campaign_id)}
                      className="inline-flex items-center gap-2 rounded-xl bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-800 disabled:opacity-50"
                    >
                      {isBusy ? (
                        <LoaderCircle className="h-4 w-4 animate-spin" />
                      ) : (
                        <Check className="h-4 w-4" />
                      )}
                      Approve
                    </button>
                    <button
                      type="button"
                      disabled={isBusy}
                      onClick={() => rejectCampaign(item.campaign_id)}
                      className="inline-flex items-center gap-2 rounded-xl bg-red-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-red-800 disabled:opacity-50"
                    >
                      <X className="h-4 w-4" />
                      Reject
                    </button>
                    <button
                      type="button"
                      disabled={isBusy}
                      onClick={() => reanalyze.mutate(item.campaign_id)}
                      className="inline-flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                    >
                      <RefreshCw className="h-4 w-4" />
                      Reanalyze
                    </button>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
