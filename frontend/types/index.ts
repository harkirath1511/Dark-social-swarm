export type OpportunityStatus = 
  | 'DISCOVERED'
  | 'PROCESSING'
  | 'AWAITING_APPROVAL'
  | 'APPROVED'
  | 'EDITED'
  | 'REJECTED'
  | 'DISCARDED';

export type EngagementVerdict = 'engage' | 'maybe_engage' | 'do_not_engage';

export type RejectionReason = 
  | 'wrong_community'
  | 'too_promotional'
  | 'low_intent'
  | 'unsafe_topic'
  | 'not_relevant'
  | 'poor_evidence';

export interface RedditPost {
  thread_id: string;
  community_id?: string;
  subreddit: string;
  title: string;
  body: string;
  author: string;
  permalink: string;
  created_utc: number;
}

export interface AnalystOutput {
  core_problem: string;
  pain_point?: string;
  user_goal?: string;
  conversation_context?: string;
  community_context?: string;
  buying_intent: string;
  sentiment?: string;
  entities?: string[];
  brand_mentioned?: boolean;
  competitor_mentioned?: boolean;
  mentioned_brands?: string[];
  mentioned_competitors?: string[];
  evidence_quote: string;
  evidence?: string[];
  analyst_confidence?: number;
}

export interface StrategistOutput {
  opportunity_score: number;
  relevance_score?: number;
  intent_strength_score?: number;
  community_fit_score?: number;
  credibility_score?: number;
  engagement_risk_score?: number;
  strategist_confidence?: number;
  brand_risk?: string;
  verdict: EngagementVerdict;
  reasoning: string;
}

export interface CriticOutput {
  critic_passed: boolean;
  violation_category: string | null;
  critic_feedback: string | null;
}

export interface Opportunity {
  id: string;
  thread_data: RedditPost;
  analyst_output: AnalystOutput;
  strategist_output: StrategistOutput;
  draft_content: string;
  critic_output: CriticOutput;
  status: OpportunityStatus;
  sensitive_topic?: boolean;
  sensitive_topic_reason?: string | null;
  iteration_count: number;
  created_at: string;
}

export interface IngestedPost {
  thread_id: string;
  subreddit: string;
  title: string;
  author: string;
  timestamp: string;
  status: OpportunityStatus;
  score?: number;
  permalink?: string;
}

