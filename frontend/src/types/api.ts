export interface Campaign {
  id: number;
  title: string;
  url: string;
  source: string;
  description: string;
  content: string;
  created_at: string;
}

export interface CampaignListResponse {
  items: Campaign[];
  total: number;
  limit: number;
  offset: number;
}

export interface CampaignCreateRequest {
  title: string;
  url: string;
  source: string;
  description?: string;
  content?: string;
}

export interface ReviewItem {
  campaign_id: number;
  campaign_title: string;
  campaign_status: string | null;
  analysis_id: number;
  total_score: number;
  confidence: number;
  summary: string;
  review_status: string;
  created_at: string;
}

export interface ReviewListResponse {
  items: ReviewItem[];
  total: number;
}

export interface ContentCreationItem {
  id: number;
  campaign_id: number;
  campaign_title: string;
  analysis_id: number;
  status: string;
  created_at: string;
  published_at: string | null;
  video_script: string;
  social_caption: string;
  hashtags: string[];
  generated_at: string | null;
  audio_url: string;
  video_url: string;
  media_generated_at: string | null;
  voice_name: string;
  social_export_url: string;
  exported_at: string | null;
  youtube_status: string;
  youtube_video_id: string;
  youtube_url: string;
  youtube_error: string;
  youtube_attempts: number;
  youtube_requested_at: string | null;
  instagram_status: string;
  instagram_media_id: string;
  instagram_url: string;
  instagram_error: string;
  instagram_attempts: number;
  instagram_requested_at: string | null;
  instagram_story_status: string;
  instagram_story_media_id: string;
  instagram_story_error: string;
  instagram_story_attempts: number;
  instagram_story_requested_at: string | null;
  tiktok_status: string;
  tiktok_publish_id: string;
  tiktok_error: string;
  tiktok_attempts: number;
  tiktok_requested_at: string | null;
  linkedin_status: string;
  linkedin_post_urn: string;
  linkedin_video_urn: string;
  linkedin_error: string;
  linkedin_attempts: number;
  linkedin_requested_at: string | null;
}

export interface VoicePreviewResponse {
  voice_name: string;
  preview_url: string;
}

export interface ContentCreationListResponse {
  items: ContentCreationItem[];
  total: number;
}

export interface AnalysisDimension {
  name: string;
  score: number;
  weight?: number;
  summary?: string;
  evidence?: string[];
}

export interface AnalysisResponse {
  id: number;
  campaign_id: number;

  total_score: number;
  confidence: number;

  framework_name: string;
  framework_version: string;
  constitution_version: string;
  model_name: string;

  summary: string;

  strengths: unknown[];
  weaknesses: unknown[];
  recommendations: unknown[];

  dimensions: AnalysisDimension[];

  review_status?: string;
  approved_by?: string;
  rejected_by?: string;
  rejection_reason?: string;

  created_at: string;
}

export interface DiscoverySaveResponse {
  query: string;
  discovered: number;
  qualified: number;
  rejected: number;
  created: number;
  skipped: number;
  rejection_reasons: Record<string, number>;
  campaign_ids: number[];
}

export interface DiscoveryHistoryItem {
  id: number;
  query: string;
  provider: string;
  status: string;
  results_found: number;
  credits_used: number;
  duration_ms: number;
  created_at: string;
}

export interface DiscoveryHistoryResponse {
  items: DiscoveryHistoryItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface RadarCluster {
  id: number;
  title: string;
  status: string;
  signal_count: number;
  source_count: number;
  confidence_score: number;
  trend_score: number;
  matched_entities: string[];
  score_rationale: string;
  last_seen_at: string;
  promoted_campaign_id: number | null;
}

export interface RadarClusterListResponse {
  items: RadarCluster[];
  total: number;
  limit: number;
  offset: number;
}

export interface RadarWatchlist {
  id: number;
  name: string;
  market: string;
  active: boolean;
}

export interface RadarWatchlistListResponse {
  items: RadarWatchlist[];
  total: number;
}

export interface RadarSource {
  id: number;
  name: string;
  source_type: string;
  enabled: boolean;
  last_status: string;
  last_error: string;
  last_results: number;
  last_polled_at: string | null;
}

export interface RadarSourceListResponse {
  items: RadarSource[];
  total: number;
}

export interface RadarPromotionResponse {
  cluster_id: number;
  campaign_id: number;
  created: boolean;
}

export type ServiceStatus = Record<string, string>;
export type ActionResponse = Record<string, string>;
