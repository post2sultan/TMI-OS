import { useQuery } from "@tanstack/react-query";
import { Activity, CheckCircle2, Server } from "lucide-react";
import { ErrorState, LoadingState } from "../components/shared/LiveState";
import { API_BASE_URL, api } from "../lib/api";

export function SettingsPage() {
  const health = useQuery({
    queryKey: ["health"],
    queryFn: api.health,
  });
  const ready = useQuery({
    queryKey: ["ready"],
    queryFn: api.ready,
  });

  if (health.isLoading || ready.isLoading) {
    return <LoadingState label="Checking backend services..." />;
  }

  if (health.isError || ready.isError) {
    return (
      <ErrorState
        message="Backend health checks failed."
        onRetry={() => {
          void health.refetch();
          void ready.refetch();
        }}
      />
    );
  }

  return (
    <div className="space-y-7">
      <header>
        <p className="text-sm font-semibold text-blue-700">SYSTEM CONTROL</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
          Settings
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          Live environment and service status.
        </p>
      </header>

      <section className="grid gap-4 lg:grid-cols-2">
        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <Server className="h-5 w-5 text-blue-700" />
            <h2 className="font-semibold text-slate-950">API environment</h2>
          </div>
          <dl className="mt-5 space-y-4 text-sm">
            <div>
              <dt className="text-slate-400">Base URL</dt>
              <dd className="mt-1 break-all font-mono text-slate-800">
                {API_BASE_URL}
              </dd>
            </div>
            <div>
              <dt className="text-slate-400">Frontend mode</dt>
              <dd className="mt-1 font-medium text-slate-800">
                {import.meta.env.MODE}
              </dd>
            </div>
          </dl>
        </article>

        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <Activity className="h-5 w-5 text-emerald-700" />
            <h2 className="font-semibold text-slate-950">Service checks</h2>
          </div>
          <div className="mt-5 space-y-3">
            <div className="flex items-center justify-between rounded-xl bg-emerald-50 px-4 py-3">
              <span className="text-sm font-medium text-emerald-900">Health</span>
              <CheckCircle2 className="h-5 w-5 text-emerald-700" />
            </div>
            <div className="flex items-center justify-between rounded-xl bg-emerald-50 px-4 py-3">
              <span className="text-sm font-medium text-emerald-900">Ready</span>
              <CheckCircle2 className="h-5 w-5 text-emerald-700" />
            </div>
          </div>
        </article>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="font-semibold text-slate-950">Raw backend status</h2>
        <pre className="mt-4 overflow-x-auto rounded-xl bg-slate-950 p-4 text-xs leading-6 text-slate-100">
          {JSON.stringify(
            { health: health.data, ready: ready.data },
            null,
            2,
          )}
        </pre>
      </section>
    </div>
  );
}
