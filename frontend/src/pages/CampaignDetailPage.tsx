import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Check,
  ExternalLink,
  LoaderCircle,
  Play,
  RefreshCw,
  X,
} from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { toast } from "sonner";
import { DimensionCard } from "../components/review/DimensionCard";
import {
  ErrorState,
  LoadingState,
  NoDataState,
} from "../components/shared/LiveState";
import { api, ApiError } from "../lib/api";
import {
  asText,
  formatDate,
  formatPercent,
  normalizeScore,
} from "../lib/format";

const REVIEWER = "Sultan Salahuddin";

function AnalysisList({
  title,
  items,
}: {
  title: string;
  items: unknown[];
}) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="font-semibold text-slate-950">{title}</h2>
      {items.length === 0 ? (
        <p className="mt-3 text-sm text-slate-500">No entries returned.</p>
      ) : (
        <ul className="mt-4 space-y-3">
          {items.map((item, index) => (
            <li
              key={`${title}-${index}`}
              className="rounded-xl bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-700"
            >
              {asText(item)}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function reviewBadgeClass(status?: string) {
  switch (status?.toLowerCase()) {
    case "approved":
      return "bg-emerald-100 text-emerald-800";
    case "rejected":
      return "bg-red-100 text-red-800";
    default:
      return "bg-amber-100 text-amber-800";
  }
}

export function CampaignDetailPage() {
  const { campaignId: campaignIdParam } = useParams();
  const campaignId = Number(campaignIdParam);
  const isValidCampaignId = Number.isInteger(campaignId) && campaignId > 0;
  const queryClient = useQueryClient();
  const [rejectionReason, setRejectionReason] = useState("");
  const [showRejectForm, setShowRejectForm] = useState(false);

  const campaign = useQuery({
    queryKey: ["campaign", campaignId],
    queryFn: () => api.getCampaign(campaignId),
    enabled: isValidCampaignId,
  });

  const analysis = useQuery({
    queryKey: ["analysis", campaignId],
    queryFn: () => api.getLatestAnalysis(campaignId),
    enabled: isValidCampaignId,
    retry: (failureCount, error) =>
      !(error instanceof ApiError && error.status === 404) &&
      failureCount < 1,
  });

  async function refreshCampaignData() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["campaign", campaignId] }),
      queryClient.invalidateQueries({ queryKey: ["analysis", campaignId] }),
      queryClient.invalidateQueries({ queryKey: ["campaigns"] }),
      queryClient.invalidateQueries({ queryKey: ["reviews"] }),
    ]);
  }

  const analyze = useMutation({
    mutationFn: () => api.analyzeCampaign(campaignId, false),
    onSuccess: async () => {
      toast.success("Campaign analysis completed.");
      await refreshCampaignData();
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const approve = useMutation({
    mutationFn: () => api.approveCampaign(campaignId, REVIEWER),
    onSuccess: async () => {
      toast.success("Campaign approved.");
      await refreshCampaignData();
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const reject = useMutation({
    mutationFn: (reason: string) =>
      api.rejectCampaign(campaignId, REVIEWER, reason),
    onSuccess: async () => {
      setRejectionReason("");
      setShowRejectForm(false);
      toast.success("Campaign rejected.");
      await refreshCampaignData();
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const reanalyze = useMutation({
    mutationFn: () => api.reanalyzeCampaign(campaignId),
    onSuccess: async () => {
      toast.success("Campaign reanalysis completed.");
      await refreshCampaignData();
    },
    onError: (error: Error) => toast.error(error.message),
  });

  if (!isValidCampaignId) {
    return <ErrorState message="Invalid campaign ID." />;
  }

  if (campaign.isLoading) {
    return <LoadingState label="Loading campaign..." />;
  }

  if (campaign.isError || !campaign.data) {
    return (
      <ErrorState
        message="The campaign could not be loaded."
        onRetry={() => void campaign.refetch()}
      />
    );
  }

  const record = campaign.data;
  const noAnalysis =
    analysis.error instanceof ApiError && analysis.error.status === 404;
  const isGovernancePending =
    approve.isPending || reject.isPending || reanalyze.isPending;

  return (
    <div className="space-y-7">
      <Link
        to="/campaign-radar"
        className="inline-flex items-center gap-2 text-sm font-semibold text-blue-700 hover:text-blue-900"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        Campaign Radar
      </Link>

      <header className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-bold uppercase tracking-wide text-blue-800">
                {record.source}
              </span>
              <span className="text-xs text-slate-400">
                Campaign #{record.id}
              </span>
            </div>
            <h1 className="mt-4 max-w-4xl text-3xl font-bold tracking-tight text-slate-950">
              {record.title}
            </h1>
            <p className="mt-3 max-w-4xl text-sm leading-6 text-slate-600">
              {record.description || "No description stored."}
            </p>
            <p className="mt-4 text-xs text-slate-400">
              Added {formatDate(record.created_at)}
            </p>
          </div>
          <a
            href={record.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          >
            Open source
            <ExternalLink className="h-4 w-4" aria-hidden="true" />
          </a>
        </div>
      </header>

      {analysis.isLoading ? (
        <LoadingState label="Loading latest analysis..." />
      ) : noAnalysis ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-6">
          <NoDataState
            title="No analysis exists"
            description="Run the scoring framework to create the first analysis record."
          />
          <button
            type="button"
            onClick={() => analyze.mutate()}
            disabled={analyze.isPending}
            className="mx-auto mt-5 flex items-center gap-2 rounded-xl bg-blue-700 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {analyze.isPending ? (
              <LoaderCircle className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <Play className="h-4 w-4" aria-hidden="true" />
            )}
            Analyze campaign
          </button>
        </div>
      ) : analysis.isError || !analysis.data ? (
        <ErrorState
          message="The latest campaign analysis could not be loaded."
          onRetry={() => void analysis.refetch()}
        />
      ) : (
        <>
          <section className="grid gap-4 md:grid-cols-3">
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Total score
              </p>
              <p className="mt-3 text-3xl font-bold text-slate-950">
                {normalizeScore(analysis.data.total_score)}
              </p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Confidence
              </p>
              <p className="mt-3 text-3xl font-bold text-slate-950">
                {formatPercent(analysis.data.confidence)}
              </p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Framework
              </p>
              <p className="mt-3 text-lg font-bold text-slate-950">
                {analysis.data.framework_name}
              </p>
              <p className="mt-1 text-xs text-slate-400">
                v{analysis.data.framework_version}
              </p>
            </div>
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="font-semibold text-slate-950">
                    Executive summary
                  </h2>
                  <span
                    className={`rounded-full px-2.5 py-1 text-xs font-bold uppercase tracking-wide ${reviewBadgeClass(
                      analysis.data.review_status,
                    )}`}
                  >
                    {analysis.data.review_status || "Pending"}
                  </span>
                </div>
                <p className="mt-3 max-w-5xl text-sm leading-7 text-slate-600">
                  {analysis.data.summary}
                </p>
                {analysis.data.rejection_reason ? (
                  <p className="mt-3 text-sm font-medium text-red-700">
                    Rejection reason: {analysis.data.rejection_reason}
                  </p>
                ) : null}
              </div>

              <div className="flex shrink-0 flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => approve.mutate()}
                  disabled={isGovernancePending}
                  className="inline-flex items-center gap-2 rounded-xl bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {approve.isPending ? (
                    <LoaderCircle className="h-4 w-4 animate-spin" />
                  ) : (
                    <Check className="h-4 w-4" />
                  )}
                  Approve
                </button>
                <button
                  type="button"
                  onClick={() => setShowRejectForm((visible) => !visible)}
                  disabled={isGovernancePending}
                  className="inline-flex items-center gap-2 rounded-xl bg-red-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-red-800 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <X className="h-4 w-4" />
                  Reject
                </button>
                <button
                  type="button"
                  onClick={() => reanalyze.mutate()}
                  disabled={isGovernancePending}
                  className="inline-flex items-center gap-2 rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {reanalyze.isPending ? (
                    <LoaderCircle className="h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCw className="h-4 w-4" />
                  )}
                  Reanalyze
                </button>
              </div>
            </div>

            {showRejectForm ? (
              <form
                className="mt-5 rounded-xl border border-red-200 bg-red-50 p-4"
                onSubmit={(event) => {
                  event.preventDefault();
                  const reason = rejectionReason.trim();
                  if (reason) reject.mutate(reason);
                }}
              >
                <label
                  htmlFor="rejection-reason"
                  className="text-sm font-semibold text-red-900"
                >
                  Reason for rejection
                </label>
                <textarea
                  id="rejection-reason"
                  value={rejectionReason}
                  onChange={(event) => setRejectionReason(event.target.value)}
                  rows={3}
                  required
                  disabled={reject.isPending}
                  className="mt-2 w-full rounded-xl border border-red-200 bg-white px-3 py-2 text-sm text-slate-800 outline-none focus:border-red-500 focus:ring-2 focus:ring-red-200"
                  placeholder="Explain why this campaign should be rejected."
                />
                <div className="mt-3 flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setShowRejectForm(false);
                      setRejectionReason("");
                    }}
                    disabled={reject.isPending}
                    className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={!rejectionReason.trim() || reject.isPending}
                    className="inline-flex items-center gap-2 rounded-xl bg-red-700 px-4 py-2 text-sm font-semibold text-white hover:bg-red-800 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {reject.isPending ? (
                      <LoaderCircle className="h-4 w-4 animate-spin" />
                    ) : (
                      <X className="h-4 w-4" />
                    )}
                    Confirm rejection
                  </button>
                </div>
              </form>
            ) : null}
          </section>

          <div className="grid gap-4 xl:grid-cols-3">
            <AnalysisList title="Strengths" items={analysis.data.strengths} />
            <AnalysisList title="Weaknesses" items={analysis.data.weaknesses} />
            <AnalysisList
              title="Recommendations"
              items={analysis.data.recommendations}
            />
          </div>

          <section>
            <h2 className="mb-4 text-xl font-bold text-slate-950">
              Analysis dimensions
            </h2>
            {analysis.data.dimensions.length === 0 ? (
              <NoDataState
                title="No dimensions returned"
                description="This analysis does not contain dimension-level scores."
              />
            ) : (
              <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
                {analysis.data.dimensions.map((dimension, index) => (
                  <DimensionCard
                    key={`${dimension.name}-${index}`}
                    {...dimension}
                  />
                ))}
              </div>
            )}
          </section>
        </>
      )}

      {record.content ? (
        <details className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <summary className="cursor-pointer font-semibold text-slate-950">
            Stored source content
          </summary>
          <p className="mt-4 whitespace-pre-wrap text-sm leading-7 text-slate-600">
            {record.content}
          </p>
        </details>
      ) : null}
    </div>
  );
}
