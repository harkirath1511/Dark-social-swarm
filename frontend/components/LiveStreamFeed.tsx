'use client';

import React, { useState } from 'react';
import { Radio, PlusCircle, Filter, CheckCircle2, Clock, XCircle, ArrowUpRight, Loader2 } from 'lucide-react';
import { IngestedPost } from '../types';

interface LiveStreamFeedProps {
  posts: IngestedPost[];
  onSimulateIngest: (title: string, body: string, subreddit: string) => Promise<void>;
}

export const LiveStreamFeed: React.FC<LiveStreamFeedProps> = ({
  posts,
  onSimulateIngest,
}) => {
  const [filter, setFilter] = useState<string>('ALL');
  const [isSimulating, setIsSimulating] = useState(false);

  const handleSimulateQuick = async (type: 'clip' | 'crm' | 'spam') => {
    try {
      setIsSimulating(true);
      if (type === 'clip') {
        await onSimulateIngest(
          "I've tried three tools for turning long videos into clips. Which one actually works?",
          "Most automated tools cut off sentences right in the middle or pick arbitrary highlights that don't make sense without context. Does anyone have a workflow or tool that actually respects semantic boundaries?",
          "r/SaaS"
        );
      } else if (type === 'crm') {
        await onSimulateIngest(
          "Our sales team hates updating HubSpot. Are people actually using lightweight CRMs?",
          "Manual CRM hygiene is killing our rep productivity. We lose tracking on half our dark social touchpoints and Slack DMs. What is the leanest way teams are tracking deals without requiring 20 form fields per call?",
          "r/startups"
        );
      } else {
        await onSimulateIngest(
          "Best SEO service 50% discount coupon code",
          "Click our promotional link now to get cheap backlink packages at spamlink.com",
          "r/marketing"
        );
      }
    } finally {
      setIsSimulating(false);
    }
  };

  const handleFetchLiveHN = async () => {
    try {
      setIsSimulating(true);
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      await fetch(`${API_URL}/api/ingest/hn?limit=2`, { method: 'POST' });
    } catch (e) {
      console.error("Failed to fetch live HN:", e);
    } finally {
      setIsSimulating(false);
    }
  };

  const filteredPosts = posts.filter((p) => {
    if (filter === 'ALL') return true;
    return p.status === filter;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'AWAITING_APPROVAL':
        return <span className="inline-flex items-center gap-1 text-[10px] text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20"><Clock className="w-3 h-3" /> Paused</span>;
      case 'APPROVED':
        return <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20"><CheckCircle2 className="w-3 h-3" /> Approved</span>;
      case 'DISCARDED':
        return <span className="inline-flex items-center gap-1 text-[10px] text-slate-500 bg-slate-800 px-2 py-0.5 rounded border border-slate-700"><XCircle className="w-3 h-3" /> Dropped</span>;
      default:
        return <span className="inline-flex items-center gap-1 text-[10px] text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20"><Radio className="w-3 h-3 animate-pulse" /> Ingested</span>;
    }
  };

  return (
    <div className="bg-dark-900 border border-slate-800 rounded-xl p-5 shadow-xl shadow-black/30">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-4">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          <h2 className="text-sm font-bold tracking-tight text-white uppercase">Community Stream Feed</h2>
        </div>
        <span className="text-xs text-slate-400 font-mono">{posts.length} ingested</span>
      </div>

      {/* Quick Simulation Injector */}
      <div className="bg-dark-950/80 border border-slate-800/80 rounded-lg p-3 mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider">Test Pipeline Simulation</span>
          {isSimulating && <Loader2 className="w-3.5 h-3.5 text-indigo-400 animate-spin" />}
        </div>
        <div className="flex flex-wrap gap-1.5">
          <button
            type="button"
            disabled={isSimulating}
            onClick={() => handleSimulateQuick('clip')}
            className="text-[11px] px-2.5 py-1 rounded bg-dark-850 hover:bg-dark-800 border border-slate-700 text-indigo-300 transition-colors disabled:opacity-50"
          >
            + Video Tool Inquiry
          </button>
          <button
            type="button"
            disabled={isSimulating}
            onClick={() => handleSimulateQuick('crm')}
            className="text-[11px] px-2.5 py-1 rounded bg-dark-850 hover:bg-dark-800 border border-slate-700 text-cyan-300 transition-colors disabled:opacity-50"
          >
            + CRM Friction Inquiry
          </button>
          <button
            type="button"
            disabled={isSimulating}
            onClick={() => handleSimulateQuick('spam')}
            className="text-[11px] px-2.5 py-1 rounded bg-dark-850 hover:bg-dark-800 border border-slate-700 text-red-300 transition-colors disabled:opacity-50"
          >
            + Spam Promo (Drop)
          </button>
          <button
            type="button"
            disabled={isSimulating}
            onClick={handleFetchLiveHN}
            className="text-[11px] px-2.5 py-1 rounded bg-orange-950/50 hover:bg-orange-900/60 border border-orange-500/50 text-orange-300 font-medium transition-colors disabled:opacity-50 flex items-center gap-1.5"
            title="Fetch real Ask HN discussions from news.ycombinator.com (100% real live links)"
          >
            <Radio className="w-3 h-3 text-orange-400 animate-pulse" />
            + Live Ask HN (Real Data)
          </button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-1 mb-3 text-xs">
        {(['ALL', 'AWAITING_APPROVAL', 'APPROVED', 'DISCARDED'] as const).map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setFilter(tab)}
            className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors ${
              filter === tab
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-dark-850'
            }`}
          >
            {tab === 'AWAITING_APPROVAL' ? 'Pending' : tab}
          </button>
        ))}
      </div>

      {/* Ingested List */}
      <div className="space-y-2.5 max-h-[520px] overflow-y-auto pr-1">
        {filteredPosts.length === 0 ? (
          <div className="text-center py-8 text-xs text-slate-500">
            No posts matching filter.
          </div>
        ) : (
          filteredPosts.map((post) => {
            const isHN = post.thread_id.startsWith('hn_') || post.subreddit?.includes('ycombinator');
            const url = post.permalink && (post.permalink.startsWith('http://') || post.permalink.startsWith('https://'))
              ? post.permalink
              : isHN
              ? `https://news.ycombinator.com/item?id=${post.thread_id.replace('hn_', '')}`
              : post.permalink?.startsWith('/r/')
              ? `https://reddit.com${post.permalink}`
              : `https://www.reddit.com/r/${post.subreddit?.replace(/^r\//, '') || 'SaaS'}/search/?q=${encodeURIComponent(post.title)}`;

            return (
              <div
                key={post.thread_id}
                className="p-3 bg-dark-950/60 hover:bg-dark-950 border border-slate-800/80 hover:border-slate-700 rounded-lg transition-all text-xs group"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className={`font-semibold text-[11px] ${isHN ? 'text-orange-400' : 'text-indigo-400'}`}>
                    {post.subreddit}
                  </span>
                  <div className="flex items-center gap-2">
                    {post.score !== undefined && (
                      <span className="font-mono text-[10px] text-slate-400">Score: {post.score}</span>
                    )}
                    {getStatusBadge(post.status)}
                  </div>
                </div>
                <a
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-slate-200 font-medium line-clamp-2 leading-snug mb-1.5 hover:text-indigo-300 transition-colors flex items-start justify-between gap-1"
                  title={isHN ? 'Open on Hacker News' : 'Open on Reddit'}
                >
                  <span>{post.title}</span>
                  <ArrowUpRight className="w-3 h-3 text-slate-500 group-hover:text-indigo-400 shrink-0 mt-0.5" />
                </a>
                <div className="flex items-center justify-between text-[10px] text-slate-500">
                  <span>
                    {isHN
                      ? (post.author?.startsWith('hn/') ? post.author : `hn/${post.author}`)
                      : (post.author?.startsWith('u/') ? post.author : `u/${post.author}`)}
                  </span>
                  <span>{post.timestamp}</span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
