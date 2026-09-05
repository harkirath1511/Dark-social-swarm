import { IngestedPost, Opportunity } from '../types';

export const INITIAL_OPPORTUNITIES: Opportunity[] = [{
  id: 't3_preview_video_tools',
  thread_data: { thread_id: 't3_preview_video_tools', subreddit: 'r/SaaS', title: 'Which video clipping tool keeps the context intact?', body: 'I need highlights that respect the story rather than cutting on silence.', author: 'signal_seeker', permalink: 'https://www.reddit.com/r/SaaS/', created_utc: Date.now() / 1000 - 3600 },
  analyst_output: { core_problem: 'Automated clipping tools lose narrative context.', buying_intent: 'high', evidence_quote: 'I need highlights that respect the story rather than cutting on silence.', analyst_confidence: 0.9 },
  strategist_output: { opportunity_score: 86, verdict: 'engage', reasoning: 'Clear product pain with a specific workflow need.' },
  draft_content: 'Token-level alignment is usually a stronger starting point than silence detection for preserving context.',
  critic_output: { critic_passed: true, violation_category: null, critic_feedback: 'Value-first response is safe to review.' },
  status: 'AWAITING_APPROVAL', iteration_count: 1, created_at: new Date().toISOString(),
}];

export const INITIAL_LIVE_POSTS: IngestedPost[] = [
  { thread_id: 't3_preview_video_tools', subreddit: 'r/SaaS', title: 'Which video clipping tool keeps the context intact?', author: 'signal_seeker', timestamp: '12m ago', status: 'AWAITING_APPROVAL', score: 86 },
  { thread_id: 't3_preview_crm', subreddit: 'r/startups', title: 'What is the least painful way to maintain CRM hygiene?', author: 'pipeline_builder', timestamp: '29m ago', status: 'DISCOVERED', score: 72 },
];
