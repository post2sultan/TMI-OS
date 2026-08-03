import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileText, LoaderCircle, Send, Video } from "lucide-react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { ErrorState, LoadingState, NoDataState } from "../components/shared/LiveState";
import { api } from "../lib/api";
import { formatDate, normalizeScore } from "../lib/format";

export function ApprovedPage() {
  const queryClient = useQueryClient();
  const [voiceByCampaign, setVoiceByCampaign] = useState<Record<number, string>>({});
  const [preview, setPreview] = useState({ campaignId: 0, url: "" });
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
      toast.success("Private YouTube upload queued.");
      await queryClient.invalidateQueries({ queryKey: ["reviews"] });
      await queryClient.invalidateQueries({ queryKey: ["content-creation"] });
      await queryClient.invalidateQueries({ queryKey: ["campaigns"] });
    },
    onError: (error: Error) => toast.error(error.message),
  });
  const publishInstagram = useMutation({
    mutationFn: api.publishInstagramReel,
    onSuccess: async () => {
      toast.success("Public Instagram Reel queued.");
      await queryClient.invalidateQueries({ queryKey: ["content-creation"] });
    },
    onError: (error: Error) => toast.error(error.message),
  });
  const publishStory = useMutation({
    mutationFn: api.publishInstagramStory,
    onSuccess: async () => { toast.success("Public Instagram Story queued."); await queryClient.invalidateQueries({ queryKey: ["content-creation"] }); },
    onError: (error: Error) => toast.error(error.message),
  });
  const uploadTikTok = useMutation({
    mutationFn: api.uploadTikTokDraft,
    onSuccess: async () => { toast.success("TikTok draft upload queued. Finish posting from TikTok Inbox."); await queryClient.invalidateQueries({ queryKey: ["content-creation"] }); },
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
  const generateMedia = useMutation({
    mutationFn: ({ campaignId, voiceName }: { campaignId: number; voiceName: string }) =>
      api.generateCampaignMedia(campaignId, voiceName),
    onSuccess: async () => {
      toast.success("Voiceover and vertical video generated.");
      await queryClient.invalidateQueries({ queryKey: ["content-creation"] });
    },
    onError: (error: Error) => toast.error(error.message),
  });
  const previewVoice = useMutation({
    mutationFn: ({
      campaignId,
      voiceName,
    }: {
      campaignId: number;
      voiceName: string;
    }) =>
      api.generateVoicePreview(voiceName).then((response) => ({
        campaignId,
        response,
      })),
    onSuccess: ({ campaignId, response }) =>
      setPreview({
        campaignId,
        url: `${response.preview_url}?t=${Date.now()}`,
      }),
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
        <div className="grid gap-4">
          {approved.map((item) => (
            (() => {
              const job = jobByCampaign.get(item.campaign_id);
              const generated = Boolean(
                job?.video_script && job?.social_caption,
              );
              const selectedVoice =
                voiceByCampaign[item.campaign_id] || job?.voice_name || "af_heart";
              return (
            <article
              key={item.analysis_id}
              className="min-w-0 overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm hover:border-emerald-300"
            >
              <div className="flex items-start justify-between gap-4">
                <Link
                  to={`/campaigns/${item.campaign_id}`}
                  className="min-w-0 break-words font-semibold text-slate-950 hover:text-blue-700"
                >
                  <span className="mb-1 block text-xs font-bold uppercase tracking-wide text-blue-700">
                    Campaign #{item.campaign_id}
                  </span>
                  <span className="block">{item.campaign_title}</span>
                </Link>
                <span className="shrink-0 rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-bold uppercase text-emerald-800">
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
              <div className="mt-5 flex flex-col gap-3 border-t border-slate-100 pt-4 xl:flex-row xl:items-start xl:justify-between">
                <span className="text-xs font-semibold uppercase text-blue-700">
                  Content {job?.status ?? "queued"}
                </span>
                <div className="flex min-w-0 flex-wrap gap-2">
                  <button
                    type="button"
                    disabled={generate.isPending}
                    onClick={() => generate.mutate(item.campaign_id)}
                    className="inline-flex items-center gap-2 whitespace-normal rounded-xl border border-blue-200 px-4 py-2 text-left text-sm font-semibold text-blue-700 hover:bg-blue-50 disabled:opacity-50"
                  >
                    {generate.isPending ? (
                      <LoaderCircle className="h-4 w-4 animate-spin" />
                    ) : (
                      <FileText className="h-4 w-4" />
                    )}
                    {generated ? "Regenerate content" : "Generate content"}
                  </button>
                  <select
                    aria-label="Narration voice"
                    value={selectedVoice}
                    onChange={(event) =>
                      setVoiceByCampaign((current) => ({
                        ...current,
                        [item.campaign_id]: event.target.value,
                      }))
                    }
                    className="max-w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
                  >
                    <option value="af_heart">Heart — US female (default)</option>
                    <option value="af_bella">Bella — US female</option>
                    <option value="af_nicole">Nicole — US female</option>
                    <option value="am_adam">Adam — US male</option>
                    <option value="am_michael">Michael — US male</option>
                    <option value="bf_emma">Emma — British female</option>
                    <option value="bm_george">George — British male</option>
                  </select>
                  <button
                    type="button"
                    disabled={previewVoice.isPending}
                    onClick={() =>
                      previewVoice.mutate({
                        campaignId: item.campaign_id,
                        voiceName: selectedVoice,
                      })
                    }
                    className="rounded-xl border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-50"
                  >
                    Preview
                  </button>
                  <button
                    type="button"
                    disabled={!generated || generateMedia.isPending}
                    onClick={() =>
                      generateMedia.mutate({
                        campaignId: item.campaign_id,
                        voiceName: selectedVoice,
                      })
                    }
                    className="inline-flex items-center gap-2 whitespace-normal rounded-xl border border-emerald-200 px-4 py-2 text-left text-sm font-semibold text-emerald-700 hover:bg-emerald-50 disabled:opacity-50"
                  >
                    {generateMedia.isPending ? (
                      <LoaderCircle className="h-4 w-4 animate-spin" />
                    ) : (
                      <Video className="h-4 w-4" />
                    )}
                    {job?.video_url ? "Regenerate video" : "Generate video"}
                  </button>
                  <button
                    type="button"
                    disabled={!generated || publish.isPending}
                    onClick={() => publish.mutate(item.campaign_id)}
                    className="inline-flex items-center gap-2 whitespace-normal rounded-xl bg-blue-700 px-4 py-2 text-left text-sm font-semibold text-white hover:bg-blue-800 disabled:opacity-50"
                  >
                    {publish.isPending ? (
                      <LoaderCircle className="h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="h-4 w-4" />
                    )}
                    Queue private YouTube upload
                  </button>
                  <button
                    type="button"
                    disabled={!job?.video_url || publishInstagram.isPending}
                    onClick={() => {
                      if (window.confirm("Publish this Reel publicly on Instagram?")) {
                        publishInstagram.mutate(item.campaign_id);
                      }
                    }}
                    className="inline-flex items-center gap-2 rounded-xl bg-pink-700 px-4 py-2 text-sm font-semibold text-white hover:bg-pink-800 disabled:opacity-50"
                  >
                    Publish Instagram Reel (public)
                  </button>
                  <button type="button" disabled={!job?.video_url || publishStory.isPending}
                    onClick={() => { if (window.confirm("Publish this Story publicly on Instagram?")) publishStory.mutate(item.campaign_id); }}
                    className="inline-flex items-center gap-2 rounded-xl bg-violet-700 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-800 disabled:opacity-50">
                    Publish Instagram Story (public)
                  </button>
                  <button type="button" disabled={!job?.video_url || uploadTikTok.isPending}
                    onClick={() => { if (window.confirm("Upload this video as a TikTok draft? You must finish posting from TikTok Inbox.")) uploadTikTok.mutate(item.campaign_id); }}
                    className="inline-flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-50">
                    Upload TikTok draft
                  </button>
                </div>
              </div>
              {preview.campaignId === item.campaign_id ? (
                <audio
                  className="mt-3 w-full"
                  controls
                  autoPlay
                  src={preview.url}
                />
              ) : null}
              {job?.youtube_status && job.youtube_status !== "not_queued" ? (
                <div className="mt-3 rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-900">
                  YouTube: {job.youtube_status}
                  {job.youtube_error ? ` — ${job.youtube_error}` : ""}
                </div>
              ) : null}
              {job?.instagram_status && job.instagram_status !== "not_queued" ? (
                <div className="mt-3 rounded-xl border border-pink-100 bg-pink-50 px-4 py-3 text-sm text-pink-900">
                  Instagram: {job.instagram_status}{job.instagram_error ? ` — ${job.instagram_error}` : ""}
                </div>
              ) : null}
              {job?.instagram_story_status && job.instagram_story_status !== "not_queued" ? (
                <div className="mt-3 rounded-xl border border-violet-100 bg-violet-50 px-4 py-3 text-sm text-violet-900">
                  Instagram Story: {job.instagram_story_status}{job.instagram_story_error ? ` — ${job.instagram_story_error}` : ""}
                </div>
              ) : null}
              {job?.tiktok_status && job.tiktok_status !== "not_queued" ? (
                <div className="mt-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900">
                  TikTok: {job.tiktok_status}{job.tiktok_error ? ` — ${job.tiktok_error}` : ""}
                  {job.tiktok_status === "uploaded_draft" ? " — Open TikTok Inbox to review and post." : ""}
                </div>
              ) : null}
              {job?.linkedin_status && job.linkedin_status !== "not_queued" ? (
                <div className="mt-3 rounded-xl border border-sky-100 bg-sky-50 px-4 py-3 text-sm text-sky-900">
                  LinkedIn: {job.linkedin_status}{job.linkedin_error ? ` — ${job.linkedin_error}` : ""}
                </div>
              ) : null}
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
                  {job?.video_url ? (
                    <div className="space-y-2">
                      <p className="font-semibold text-slate-950">
                        Generated vertical video
                      </p>
                      <video
                        controls
                        preload="metadata"
                        className="mx-auto max-h-[32rem] w-full max-w-sm rounded-xl bg-slate-950"
                        src={job.video_url}
                      />
                      <a
                        href={job.video_url}
                        download
                        className="inline-flex font-semibold text-emerald-700 hover:underline"
                      >
                        Download MP4
                      </a>
                      <a
                        href={job.video_url.replace("video.mp4", "video-landscape.mp4")}
                        download
                        className="ml-4 inline-flex font-semibold text-sky-700 hover:underline"
                      >
                        Download landscape MP4
                      </a>
                      <a
                        href={job.video_url.replace("video.mp4", "stock/media-manifest.json")}
                        download
                        className="ml-4 inline-flex font-semibold text-slate-700 hover:underline"
                      >
                        Stock credits
                      </a>
                    </div>
                  ) : null}
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
