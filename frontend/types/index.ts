export type OpportunityStatus = 
  | 'DISCOVERED'
  | 'PROCESSING'
  | 'AWAITING_APPROVAL'
  | 'APPROVED'
  | 'EDITED'
  | 'REJECTED'
  | 'DISCARDED';

export type EngagementVerdict = 'engage' | 'maybe_engage' | 'do_not_engage';

export interface RedditPost {
  thread_id: string;
  subreddit: string;
  title: string;
  body: string;
  author: string;
  permalink: string;
  created_utc: number;
}

export interface AnalystOutput {
  core_problem: string;
  buying_intent: 'high' | 'medium' | 'low' | 'informational';
  evidence_quote: string;
}

export interface StrategistOutput {
  opportunity_score: number;
  brand_risk: 'low' | 'medium' | 'high';
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
}
