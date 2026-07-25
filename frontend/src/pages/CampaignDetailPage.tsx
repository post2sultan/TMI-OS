import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  ExternalLink,
  LoaderCircle,
  Play,
} from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { toast } from "sonner";
import { ErrorState, LoadingState, NoDataState } from "../components/shared/LiveState";
import { api, ApiError } from "../lib/api";
import { asText, formatDate, formatPercent, normalizeScore } from "../lib/format";

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

export function CampaignDetailPage() {
  const params = useParams();
  const campaignId = Number(params.campaignId);
  const queryClient = useQueryClient();

  const campaign = useQuery({
    queryKey: ["campaign", campaignId],
    queryFn: () => api.getCampaign(campaignId),
    enabled: Number.isInteger(campaignId) && campaignId > 0,
  });

  const analysis = useQuery({
    queryKey: ["analysis", campaignId],
    queryFn: () => api.getLatestAnalysis(campaignId),
    enabled: Number.isInteger(campaignId) && campaignId > 0,
    retry: (failureCount, error) => {
      if (error instanceof ApiError && error.status === 404) return false;
      return failureCount < 1;
    },
  });

  const analyze = useMutation({
    mutationFn: () => api.analyzeCampaign(campaignId, false),
    onSuccess: async () => {
      toast.success("Campaign analysis completed.");
      await queryClient.invalidateQueries({
        queryKey: ["analysis", campaignId],
      });
      await queryClient.invalidateQueries({ queryKey: ["reviews"] });
    },
    onError: (error: Error) => toast.error(error.message),
  });

  if (!Number.isInteger(campaignId) || campaignId < 1) {
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

  return (
    <div className="space-y-7">
      <Link
        to="/campaign-radar"
        className="inline-flex items-center gap-2 text-sm font-semibold text-blue-700 hover:text-blue-900"
      >
        <ArrowLeft className="h-4 w-4" />
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
            rel="noreferrer"
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          >
            Open source
            <ExternalLink className="h-4 w-4" />
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
            className="mx-auto mt-5 flex items-center gap-2 rounded-xl bg-blue-700 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-800 disabled:opacity-60"
          >
            {analyze.isPending ? (
              <LoaderCircle className="h-4 w-4 animate-spin" />
            ) : (
              <Play className="h-4 w-4" />
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
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div>
                <h2 className="font-semibold text-slate-950">Executive summary</h2>
                <p className="mt-3 max-w-5xl text-sm leading-7 text-slate-600">
                  {analysis.data.summary}
                </p>
              </div>
              <button
                type="button"
                onClick={() => analyze.mutate()}
                disabled={analyze.isPending}
                className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-60"
              >
                {analyze.isPending ? (
                  <LoaderCircle className="h-4 w-4 animate-spin" />
                ) : (
                  <Play className="h-4 w-4" />
                )}
                Run analysis
              </button>
            </div>
          </section>

          <div className="grid gap-4 xl:grid-cols-3">
            <AnalysisList title="Strengths" items={analysis.data.strengths} />
            <AnalysisList title="Weaknesses" items={analysis.data.weaknesses} />
            <AnalysisList
              title="Recommendations"
              items={analysis.data.recommendations}
            />
          </div>

          <AnalysisList title="Dimensions" items={analysis.data.dimensions} />
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
