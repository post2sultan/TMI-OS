import type {
  ActionResponse,
  AnalysisResponse,
  Campaign,
  CampaignCreateRequest,
  CampaignListResponse,
  ContentCreationListResponse,
  DiscoveryHistoryResponse,
  DiscoverySaveResponse,
  ReviewListResponse,
  RadarClusterListResponse,
  RadarPromotionResponse,
  RadarSourceListResponse,
  RadarWatchlistListResponse,
  ServiceStatus,
  VoicePreviewResponse,
} from "../types/api";

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "/api"
).replace(/\/$/, "");

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(message: string, status: number, detail: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
  });

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const message =
      typeof payload === "object" &&
      payload !== null &&
      "detail" in payload
        ? JSON.stringify(payload.detail)
        : `Request failed with status ${response.status}`;

    throw new ApiError(message, response.status, payload);
  }

  return payload as T;
}

export const api = {
  health: () => request<ServiceStatus>("/health"),
  ready: () => request<ServiceStatus>("/ready"),

  listCampaigns: (limit = 100, offset = 0) =>
    request<CampaignListResponse>(
      `/campaigns?limit=${limit}&offset=${offset}`,
    ),

  getCampaign: (campaignId: number) =>
    request<Campaign>(`/campaigns/${campaignId}`),

  createCampaign: (input: CampaignCreateRequest) =>
    request<Campaign>("/campaigns", {
      method: "POST",
      body: JSON.stringify(input),
    }),

  discoverAndSave: (prompt: string) =>
    request<DiscoverySaveResponse>("/radar/discover", {
      method: "POST",
      body: JSON.stringify({ prompt }),
    }),

  discoverWatchlist: (watchlistId: number) =>
    request<DiscoverySaveResponse>("/radar/discover", {
      method: "POST",
      body: JSON.stringify({ watchlist_id: watchlistId }),
    }),

  listRadarClusters: (status = "", sort = "trend", limit = 50) =>
    request<RadarClusterListResponse>(
      `/radar/clusters?sort=${encodeURIComponent(sort)}&status=${encodeURIComponent(status)}&limit=${limit}`,
    ),

  listRadarClustersByIds: (clusterIds: number[]) =>
    request<RadarClusterListResponse>(
      `/radar/clusters?sort=trend&limit=200&ids=${encodeURIComponent(clusterIds.join(","))}`,
    ),

  listRadarWatchlists: () =>
    request<RadarWatchlistListResponse>("/radar/watchlists"),

  listRadarSources: () =>
    request<RadarSourceListResponse>("/radar/sources"),

  promoteRadarCluster: (clusterId: number) =>
    request<RadarPromotionResponse>(`/radar/clusters/${clusterId}/promote`, {
      method: "POST",
    }),

  listDiscoveryHistory: (limit = 10, offset = 0) =>
    request<DiscoveryHistoryResponse>(
      `/discovery/history?limit=${limit}&offset=${offset}`,
    ),

  listReviews: (
    status: "pending" | "approved" | "rejected" | "published" = "pending",
  ) => request<ReviewListResponse>(`/reviews?status=${status}`),

  listContentCreationJobs: () =>
    request<ContentCreationListResponse>("/content-creation"),

  generateContentPackage: (campaignId: number) =>
    request<ContentCreationListResponse>(
      `/campaigns/${campaignId}/content/generate`,
      { method: "POST" },
    ),

  generateCampaignMedia: (campaignId: number, voiceName: string) =>
    request<ContentCreationListResponse>(
      `/campaigns/${campaignId}/media/generate`,
      { method: "POST", body: JSON.stringify({ voice_name: voiceName }) },
    ),

  generateVoicePreview: (voiceName: string) =>
    request<VoicePreviewResponse>(`/media/voices/${voiceName}/preview`, {
      method: "POST",
    }),

  exportSocialPackage: (campaignId: number) =>
    request<ContentCreationListResponse>(
      `/campaigns/${campaignId}/social/export`,
      { method: "POST" },
    ),

  getLatestAnalysis: (campaignId: number) =>
    request<AnalysisResponse>(
      `/campaigns/${campaignId}/analysis/latest`,
    ),

  analyzeCampaign: (campaignId: number, force = false) =>
    request<AnalysisResponse>(
      `/campaigns/${campaignId}/analyze?force=${force}`,
      { method: "POST" },
    ),

  approveCampaign: (campaignId: number, approvedBy: string) =>
    request<ActionResponse>(`/campaigns/${campaignId}/approve`, {
      method: "POST",
      body: JSON.stringify({ approved_by: approvedBy }),
    }),

  rejectCampaign: (
    campaignId: number,
    rejectedBy: string,
    reason: string,
  ) =>
    request<ActionResponse>(`/campaigns/${campaignId}/reject`, {
      method: "POST",
      body: JSON.stringify({
        rejected_by: rejectedBy,
        reason,
      }),
    }),

  reanalyzeCampaign: (campaignId: number) =>
    request<AnalysisResponse>(`/campaigns/${campaignId}/analyze?force=true`, {
      method: "POST",
    }),

  publishCampaign: (campaignId: number) =>
    request<ActionResponse>(`/campaigns/${campaignId}/publish`, {
      method: "POST",
    }),

  publishInstagramReel: (campaignId: number) =>
    request<ActionResponse>(`/campaigns/${campaignId}/publishing/instagram`, {
      method: "POST",
    }),
  publishInstagramStory: (campaignId: number) =>
    request<ActionResponse>(`/campaigns/${campaignId}/publishing/instagram-story`, { method: "POST" }),
  uploadTikTokDraft: (campaignId: number) =>
    request<ActionResponse>(`/campaigns/${campaignId}/publishing/tiktok`, { method: "POST" }),
  publishLinkedInVideo: (campaignId: number) =>
    request<ActionResponse>(`/campaigns/${campaignId}/publishing/linkedin`, { method: "POST" }),
};

export { API_BASE_URL };
