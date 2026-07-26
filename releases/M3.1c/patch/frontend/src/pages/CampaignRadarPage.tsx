import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ChevronLeft,
  ChevronRight,
  Clock3,
  ExternalLink,
  History,
  LoaderCircle,
  Radar,
  Search,
} from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { ErrorState, LoadingState, NoDataState } from "../components/shared/LiveState";
import { api } from "../lib/api";
import { formatDate } from "../lib/format";

export function CampaignRadarPage() {
  const historyPageSize = 10;
  const [prompt, setPrompt] = useState("");
  const [historyOffset, setHistoryOffset] = useState(0);
  const queryClient = useQueryClient();

  const campaigns = useQuery({
    queryKey: ["campaigns"],
    queryFn: () => api.listCampaigns(),
  });

  const history = useQuery({
    queryKey: ["discovery-history", historyPageSize, historyOffset],
    queryFn: () =>
      api.listDiscoveryHistory(historyPageSize, historyOffset),
  });

  const discovery = useMutation({
    mutationFn: api.discoverAndSave,
    onSuccess: async (result) => {
      toast.success(
        `Discovery complete: ${result.created} created, ${result.skipped} skipped.`,
      );
      setPrompt("");
      await queryClient.invalidateQueries({ queryKey: ["campaigns"] });
      await queryClient.invalidateQueries({ queryKey: ["reviews"] });
      setHistoryOffset(0);
      await queryClient.invalidateQueries({
        queryKey: ["discovery-history"],
      });
    },
    onError: (error: Error) => toast.error(error.message),
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = prompt.trim();
    if (!value) {
      toast.error("Enter a discovery brief.");
      return;
    }
    discovery.mutate(value);
  }

  return (
    <div className="space-y-7">
      <header>
        <p className="text-sm font-semibold text-blue-700">DISCOVERY ENGINE</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
          Campaign Radar
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          Search, qualify and save real campaign records through the backend.
        </p>
      </header>

      <form
        onSubmit={submit}
        className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
      >
        <label
          htmlFor="discovery-prompt"
          className="text-sm font-semibold text-slate-900"
        >
          Discovery brief
        </label>
        <div className="mt-3 flex flex-col gap-3 lg:flex-row">
          <textarea
            id="discovery-prompt"
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            rows={3}
            placeholder="Find recent Saudi campaigns across digital, outdoor and social media..."
            className="min-h-24 flex-1 resize-y rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none transition focus:border-blue-600 focus:ring-4 focus:ring-blue-100"
          />
          <button
            type="submit"
            disabled={discovery.isPending}
            className="inline-flex min-w-40 items-center justify-center gap-2 rounded-xl bg-blue-700 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {discovery.isPending ? (
              <LoaderCircle className="h-4 w-4 animate-spin" />
            ) : (
              <Search className="h-4 w-4" />
            )}
            Discover & save
          </button>
        </div>
      </form>

      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-col gap-3 border-b border-slate-200 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <History className="h-5 w-5 text-blue-700" />
              <h2 className="font-semibold text-slate-950">
                Discovery history
              </h2>
            </div>
            <p className="mt-1 text-sm text-slate-500">
              Provider execution status, results and runtime.
            </p>
          </div>
          {history.data ? (
            <p className="text-sm font-medium text-slate-500">
              {history.data.total} provider runs
            </p>
          ) : null}
        </div>

        {history.isLoading || !history.data ? (
          <div className="p-5">
            <LoadingState label="Loading discovery history..." />
          </div>
        ) : history.isError ? (
          <div className="p-5">
            <ErrorState
              message="Discovery history could not be loaded."
              onRetry={() => void history.refetch()}
            />
          </div>
        ) : history.data.items.length === 0 ? (
          <div className="p-5">
            <NoDataState
              title="No discovery runs yet"
              description="Run the discovery engine to record provider activity."
            />
          </div>
        ) : (
          <>
            <div className="divide-y divide-slate-100">
              {history.data.items.map((run) => (
                <article
                  key={run.id}
                  className="grid gap-3 px-5 py-4 lg:grid-cols-[minmax(0,1fr)_auto_auto_auto]"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-slate-950">
                      {run.query}
                    </p>
                    <p className="mt-1 text-xs text-slate-400">
                      {formatDate(run.created_at)}
                    </p>
                  </div>
                  <div className="text-sm">
                    <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                      Provider
                    </p>
                    <p className="mt-1 font-semibold text-slate-700">
                      {run.provider}
                    </p>
                  </div>
                  <div className="text-sm">
                    <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                      Results
                    </p>
                    <p className="mt-1 font-semibold text-slate-700">
                      {run.results_found}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 lg:min-w-44 lg:justify-end">
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                        run.status === "success"
                          ? "bg-emerald-50 text-emerald-700"
                          : "bg-rose-50 text-rose-700"
                      }`}
                    >
                      {run.status}
                    </span>
                    <span className="inline-flex items-center gap-1 text-xs text-slate-500">
                      <Clock3 className="h-3.5 w-3.5" />
                      {run.duration_ms} ms
                    </span>
                  </div>
                </article>
              ))}
            </div>

            <div className="flex items-center justify-between border-t border-slate-200 px-5 py-4">
              <p className="text-xs text-slate-500">
                Showing {historyOffset + 1}â€“
                {Math.min(
                  historyOffset + history.data.items.length,
                  history.data.total,
                )}{" "}
                of {history.data.total}
              </p>
              <div className="flex gap-2">
                <button
                  type="button"
                  aria-label="Previous discovery history page"
                  disabled={historyOffset === 0}
                  onClick={() =>
                    setHistoryOffset((offset) =>
                      Math.max(0, offset - historyPageSize),
                    )
                  }
                  className="rounded-lg border border-slate-200 p-2 text-slate-600 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  aria-label="Next discovery history page"
                  disabled={
                    historyOffset + history.data.items.length >=
                    history.data.total
                  }
                  onClick={() =>
                    setHistoryOffset((offset) => offset + historyPageSize)
                  }
                  className="rounded-lg border border-slate-200 p-2 text-slate-600 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          </>
        )}
      </section>

      {campaigns.isLoading || !campaigns.data ? (
        <LoadingState label="Loading campaign library..." />
      ) : campaigns.isError ? (
        <ErrorState
          message="Campaign records could not be loaded."
          onRetry={() => void campaigns.refetch()}
        />
      ) : campaigns.data.items.length === 0 ? (
        <NoDataState
          title="Campaign library is empty"
          description="Run the discovery engine above to save the first qualified campaigns."
        />
      ) : (
        <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
            <div>
              <h2 className="font-semibold text-slate-950">Campaign library</h2>
              <p className="mt-1 text-sm text-slate-500">
                {campaigns.data.total} live records
              </p>
            </div>
            <Radar className="h-5 w-5 text-blue-700" />
          </div>

          <div className="divide-y divide-slate-100">
            {campaigns.data.items.map((campaign) => (
              <article
                key={campaign.id}
                className="grid gap-4 px-5 py-5 hover:bg-slate-50 lg:grid-cols-[1fr_auto]"
              >
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <Link
                      to={`/campaigns/${campaign.id}`}
                      className="font-semibold text-slate-950 hover:text-blue-700"
                    >
                      {campaign.title}
                    </Link>
                    <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">
                      {campaign.source}
                    </span>
                  </div>
                  <p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-500">
                    {campaign.description || "No description stored."}
                  </p>
                  <p className="mt-3 text-xs text-slate-400">
                    Added {formatDate(campaign.created_at)}
                  </p>
                </div>
                <a
                  href={campaign.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex h-fit items-center gap-2 text-sm font-semibold text-blue-700 hover:text-blue-900"
                >
                  Source
                  <ExternalLink className="h-4 w-4" />
                </a>
              </article>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
