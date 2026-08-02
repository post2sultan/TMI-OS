import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Activity, CheckCircle2, LoaderCircle, Radar, RefreshCw, Search, ShieldCheck, Signal, TrendingUp } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { ErrorState, LoadingState, NoDataState } from "../components/shared/LiveState";
import { api } from "../lib/api";
import { formatDate } from "../lib/format";

function scoreTone(score: number) {
  if (score >= 70) return "bg-emerald-100 text-emerald-800";
  if (score >= 40) return "bg-amber-100 text-amber-800";
  return "bg-slate-100 text-slate-700";
}

export function CampaignRadarPage() {
  const [prompt, setPrompt] = useState("");
  const [status, setStatus] = useState("");
  const [watchlistId, setWatchlistId] = useState<number | null>(null);
  const queryClient = useQueryClient();

  const clusters = useQuery({
    queryKey: ["radar-clusters", status],
    queryFn: () => api.listRadarClusters(status),
  });
  const watchlists = useQuery({ queryKey: ["radar-watchlists"], queryFn: api.listRadarWatchlists });
  const sources = useQuery({ queryKey: ["radar-sources"], queryFn: api.listRadarSources });

  const refreshRadar = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["radar-clusters"] }),
      queryClient.invalidateQueries({ queryKey: ["radar-sources"] }),
    ]);
  };

  const discovery = useMutation({
    mutationFn: () => watchlistId ? api.discoverWatchlist(watchlistId) : api.discoverAndSave(prompt.trim()),
    onSuccess: async (result) => {
      toast.success(`Scan complete: ${result.created} new signals, ${result.skipped} seen again.`);
      setPrompt("");
      await refreshRadar();
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const promotion = useMutation({
    mutationFn: api.promoteRadarCluster,
    onSuccess: async (result) => {
      toast.success(`Candidate moved to campaign #${result.campaign_id}.`);
      await refreshRadar();
      await queryClient.invalidateQueries({ queryKey: ["campaigns"] });
    },
    onError: (error: Error) => toast.error(error.message),
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!watchlistId && !prompt.trim()) return toast.error("Select a watchlist or enter a discovery brief.");
    discovery.mutate();
  }

  const candidates = clusters.data?.items ?? [];
  const corroborated = candidates.filter((item) => item.status === "corroborated").length;
  const healthySources = sources.data?.items.filter((item) => item.last_status === "healthy").length ?? 0;

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-sm font-semibold text-blue-700">CAMPAIGN INTELLIGENCE</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">Radar command center</h1>
          <p className="mt-2 text-sm text-slate-500">Signals become campaigns only after your confirmation.</p>
        </div>
        <button type="button" onClick={() => void refreshRadar()} className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50">
          <RefreshCw className="h-4 w-4" /> Refresh
        </button>
      </header>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[
          [Radar, "Candidates", clusters.data?.total ?? 0, "Ranked local clusters"],
          [ShieldCheck, "Corroborated", corroborated, "Multiple supporting signals"],
          [Activity, "Healthy sources", `${healthySources}/${sources.data?.total ?? 0}`, "Free monitored sources"],
          [Signal, "Paid credits", "0", "Local-first intelligence"],
        ].map(([Icon, label, value, note]) => {
          const MetricIcon = Icon as typeof Radar;
          return <article key={String(label)} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between"><p className="text-sm font-medium text-slate-500">{String(label)}</p><MetricIcon className="h-5 w-5 text-blue-700" /></div>
            <p className="mt-3 text-3xl font-bold text-slate-950">{String(value)}</p><p className="mt-1 text-xs text-slate-400">{String(note)}</p>
          </article>;
        })}
      </section>

      <form onSubmit={submit} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="grid gap-4 lg:grid-cols-[260px_minmax(0,1fr)_auto] lg:items-end">
          <label className="text-sm font-semibold text-slate-900">Watchlist
            <select value={watchlistId ?? ""} onChange={(event) => setWatchlistId(event.target.value ? Number(event.target.value) : null)} className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-3 py-3 text-sm text-slate-900 focus:border-blue-600 focus:ring-4 focus:ring-blue-100">
              <option value="">Custom discovery brief</option>
              {watchlists.data?.items.filter((item) => item.active).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
          </label>
          <label className="text-sm font-semibold text-slate-900">Discovery brief
            <input value={prompt} disabled={watchlistId !== null} onChange={(event) => setPrompt(event.target.value)} placeholder="Saudi outdoor, digital or social campaign..." className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 text-sm text-slate-900 disabled:bg-slate-100 disabled:text-slate-500" />
          </label>
          <button disabled={discovery.isPending} className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-700 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-800 disabled:opacity-60">
            {discovery.isPending ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />} Run scan
          </button>
        </div>
      </form>

      <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-col gap-3 border-b border-slate-200 p-5 sm:flex-row sm:items-center sm:justify-between">
          <div><h2 className="font-semibold text-slate-950">Campaign candidates</h2><p className="mt-1 text-sm text-slate-500">Ranked by trend, confidence, corroboration and recency.</p></div>
          <select value={status} onChange={(event) => setStatus(event.target.value)} className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900">
            <option value="">All candidates</option><option value="corroborated">Corroborated</option><option value="candidate">Early signals</option><option value="promoted">Promoted</option>
          </select>
        </div>
        {clusters.isLoading ? <div className="p-5"><LoadingState label="Ranking candidates..." /></div> : clusters.isError ? <div className="p-5"><ErrorState message="Radar candidates could not be loaded." onRetry={() => void clusters.refetch()} /></div> : candidates.length === 0 ? <div className="p-5"><NoDataState title="No candidates in this view" description="Run a scan or change the filter." /></div> : (
          <div className="grid gap-4 p-5 xl:grid-cols-2">
            {candidates.map((candidate) => <article key={candidate.id} className="min-w-0 rounded-2xl border border-slate-200 p-5 hover:border-blue-200 hover:shadow-sm">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0"><p className="text-xs font-semibold uppercase tracking-wide text-blue-700">Candidate #{candidate.id}</p><h3 className="mt-1 font-semibold leading-6 text-slate-950">{candidate.title}</h3></div>
                <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${candidate.status === "corroborated" ? "bg-emerald-100 text-emerald-800" : candidate.status === "promoted" ? "bg-blue-100 text-blue-800" : "bg-slate-100 text-slate-700"}`}>{candidate.status}</span>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
                <div><p className="text-xs text-slate-400">Trend</p><p className={`mt-1 inline-flex rounded-lg px-2 py-1 text-sm font-bold ${scoreTone(candidate.trend_score)}`}>{candidate.trend_score}</p></div>
                <div><p className="text-xs text-slate-400">Confidence</p><p className="mt-2 text-sm font-bold text-slate-800">{Math.round(candidate.confidence_score * 100)}%</p></div>
                <div><p className="text-xs text-slate-400">Signals</p><p className="mt-2 text-sm font-bold text-slate-800">{candidate.signal_count}</p></div>
                <div><p className="text-xs text-slate-400">Sources</p><p className="mt-2 text-sm font-bold text-slate-800">{candidate.source_count}</p></div>
              </div>
              {candidate.matched_entities.length > 0 && <div className="mt-4 flex flex-wrap gap-2">{candidate.matched_entities.map((entity) => <span key={entity} className="rounded-full bg-violet-50 px-2.5 py-1 text-xs font-medium text-violet-700">{entity}</span>)}</div>}
              <p className="mt-4 text-xs leading-5 text-slate-500">{candidate.score_rationale}</p>
              <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4">
                <span className="inline-flex items-center gap-1 text-xs text-slate-400"><TrendingUp className="h-3.5 w-3.5" /> Seen {formatDate(candidate.last_seen_at)}</span>
                {candidate.promoted_campaign_id ? <Link to={`/campaigns/${candidate.promoted_campaign_id}`} className="inline-flex items-center gap-2 rounded-xl bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-700"><CheckCircle2 className="h-4 w-4" /> Campaign #{candidate.promoted_campaign_id}</Link> : <button type="button" disabled={promotion.isPending} onClick={() => promotion.mutate(candidate.id)} className="rounded-xl bg-blue-700 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-800 disabled:opacity-60">Confirm as campaign</button>}
              </div>
            </article>)}
          </div>
        )}
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="font-semibold text-slate-950">Source health</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {sources.data?.items.map((source) => <div key={source.id} className="rounded-xl border border-slate-200 p-4"><div className="flex items-center justify-between gap-2"><p className="truncate text-sm font-semibold text-slate-800">{source.name}</p><span className={`h-2.5 w-2.5 rounded-full ${source.last_status === "healthy" ? "bg-emerald-500" : source.last_status === "error" ? "bg-rose-500" : "bg-amber-400"}`} /></div><p className="mt-2 text-xs text-slate-500">{source.source_type.toUpperCase()} · {source.last_results} latest results</p>{source.last_error && <p className="mt-2 line-clamp-2 text-xs text-rose-600">{source.last_error}</p>}</div>)}
        </div>
      </section>
    </div>
  );
}
