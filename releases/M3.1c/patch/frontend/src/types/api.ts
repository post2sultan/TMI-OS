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
  dimensions: unknown[];
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

export type ServiceStatus = Record<string, string>;
export type ActionResponse = Record<string, string>;
