import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ExternalLink, LoaderCircle, Radar, Search } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { ErrorState, LoadingState, NoDataState } from "../components/shared/LiveState";
import { api } from "../lib/api";
import { formatDate } from "../lib/format";

export function CampaignRadarPage() {
  const [prompt, setPrompt] = useState("");
  const queryClient = useQueryClient();

  const campaigns = useQuery({
    queryKey: ["campaigns"],
    queryFn: () => api.listCampaigns(),
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

      {campaigns.isLoading ? (
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
