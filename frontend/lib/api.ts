import type { RejectionReason } from '../types';

type ReviewAction = 'approved' | 'edited' | 'rejected';
type FetchOptions = RequestInit & { signal?: AbortSignal };
export type BackendOpportunity = Record<string, any>;

async function request<T>(path: string, options?: FetchOptions): Promise<T> {
  const response = await fetch(`/api${path}`, options);
  if (!response.ok) throw new Error(`API request failed: ${response.status} ${response.statusText}`);
  return response.json() as Promise<T>;
}

export function getReviewQueue(options?: FetchOptions) {
  return request<{ count: number; queue?: unknown[]; opportunities?: unknown[] }>('/review-queue', options);
}

export function getFeed(options?: FetchOptions) {
  return request<{ items?: unknown[] }>('/feed?limit=25', options);
}

export function submitReview(threadId: string, action: ReviewAction, text?: string, rejectionReason?: RejectionReason) {
  return request(`/review/${threadId}/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, edited_text: action === 'edited' ? text : undefined, rejection_reason: action === 'rejected' ? rejectionReason : undefined }),
  });
}

export function ingestCustom(title: string, body: string, subreddit: string) {
  return request<{ opportunity?: BackendOpportunity }>('/ingest/custom', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, body, subreddit }),
  });
}
