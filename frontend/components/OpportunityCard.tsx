'use client';

import React, { useState } from 'react';
import {
  ExternalLink,
  Quote,
  ShieldCheck,
  AlertTriangle,
  User,
  MessageSquare,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  Copy,
  Tag,
  Gauge,
  HelpCircle,
  AlertOctagon,
  Sparkles,
  Clock,
} from 'lucide-react';
import { Opportunity, RejectionReason } from '../types';
import { ActionPanel } from './ActionPanel';
import { formatLocalTime } from '../lib/date-utils.mjs';

interface OpportunityCardProps {
  opportunity: Opportunity;
  onActionComplete: (
    threadId: string,
    action: 'approved' | 'edited' | 'rejected',
    text?: string,
    rejectionReason?: RejectionReason
  ) => Promise<void>;
}

export const OpportunityCard: React.FC<OpportunityCardProps> = ({
  opportunity,
  onActionComplete,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedDraft, setEditedDraft] = useState(opportunity.draft_content || '');
  const [showFullPreview, setShowFullPreview] = useState(false);
  const [isResolved, setIsResolved] = useState(false);
  const [resolvedStatus, setResolvedStatus] = useState<string | null>(null);
  const [copiedToast, setCopiedToast] = useState(false);

  const score = opportunity.strategist_output.opportunity_score ?? 75;
  const strat = opportunity.strategist_output;
  const analyst = opportunity.analyst_output;
  const critic = opportunity.critic_output;

  const getScoreBarColor = (val: number) => {
    if (val >= 70) return 'bg-emerald-500';
    if (val >= 40) return 'bg-amber-500';
    return 'bg-red-500';
  };

  const getScoreTextColor = (val: number) => {
    if (val >= 70) return 'text-emerald-400';
    if (val >= 40) return 'text-amber-400';
    return 'text-red-400';
  };

  // Button 1: Approve & Copy
  const handleApproveAndCopy = async () => {
    try {
      if (typeof navigator !== 'undefined' && navigator.clipboard) {
        await navigator.clipboard.writeText(editedDraft);
      }
    } catch (e) {
      console.warn('Clipboard write failed:', e);
    }

    setCopiedToast(true);
    setTimeout(() => setCopiedToast(false), 3000);

    await onActionComplete(opportunity.thread_data.thread_id, 'approved', editedDraft);
    setIsResolved(true);
    setResolvedStatus('APPROVED & COPIED TO CLIPBOARD');
  };

  // Button 2: Apply Edits (Submit custom edits)
  const handleApplyEdits = async () => {
    await onActionComplete(opportunity.thread_data.thread_id, 'edited', editedDraft);
    setIsEditing(false);
    setIsResolved(true);
    setResolvedStatus('EDITED & AUTHORIZED');
  };

  // Button 3: Reject / Discard
  const handleReject = async (reason: RejectionReason) => {
    await onActionComplete(opportunity.thread_data.thread_id, 'rejected', undefined, reason);
    setIsResolved(true);
    setResolvedStatus(`REJECTED: ${reason.replace('_', ' ').toUpperCase()}`);
  };

  if (isResolved) {
    return (
      <div className="dash-card border border-emerald-500/20 rounded-2xl p-6 text-center text-slate-400 transition-all duration-300">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider bg-dark-850 border border-slate-700 text-slate-300 mb-2">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          {resolvedStatus}
        </div>
        <p className="text-sm">
          Thread <span className="font-mono text-xs text-indigo-300">{opportunity.thread_data.thread_id}</span> triaged successfully.
        </p>
      </div>
    );
  }

  return (
    <article className="dash-card dash-opportunity border border-slate-800/80 hover:border-cyan-400/30 rounded-2xl p-5 sm:p-6 transition-all duration-200 relative">
      {/* Toast Notification */}
      {copiedToast && (
        <div className="absolute top-4 right-4 z-20 flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-600 text-white text-xs font-semibold shadow-lg animate-bounce">
          <Copy className="w-3.5 h-3.5" />
          <span>Copied to Clipboard!</span>
        </div>
      )}

      {/* Sensitive Topic Alert Banner */}
      {opportunity.sensitive_topic && (
        <div className="mb-4 p-3 rounded-xl bg-red-950/40 border border-red-800/60 flex items-start gap-2.5 text-xs text-red-200">
          <AlertOctagon className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
          <div>
            <strong className="text-red-300 font-semibold block">Sensitive Topic Gate Triggered (Drafting Bypassed)</strong>
            <span>{opportunity.sensitive_topic_reason || 'Medical, legal, or crisis subject detected. Handled strictly via manual review.'}</span>
          </div>
        </div>
      )}

      {/* 1. Header & Source Meta Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
        <div className="flex flex-wrap items-center gap-2">
          {/* Subreddit / Community Pill */}
          <span className="px-2.5 py-1 rounded-md text-xs font-semibold bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            {opportunity.thread_data.community_id || opportunity.thread_data.subreddit}
          </span>

          {/* Author */}
          <div className="text-xs text-slate-400 flex items-center gap-1">
            <User className="w-3.5 h-3.5 text-slate-500" />
            <span>
              {(() => {
                const a = opportunity.thread_data.author || 'anonymous';
                const isHN = opportunity.thread_data.thread_id.startsWith('hn_') ||
                  opportunity.thread_data.subreddit?.includes('ycombinator');
                if (isHN) return a.startsWith('hn/') ? a : `hn/${a}`;
                if (a.startsWith('u/')) return a;
                return `u/${a}`;
              })()}
            </span>
          </div>

          {/* Local Timestamp */}
          {opportunity.created_at && (
            <span className="text-[11px] text-slate-400 font-mono flex items-center gap-1 bg-slate-850/80 px-2 py-0.5 rounded border border-slate-700/60" title="Ingestion time in your local timezone">
              <Clock className="w-3 h-3 text-indigo-400" />
              {formatLocalTime(opportunity.created_at)}
            </span>
          )}

          {/* Brand Absence / Mention Badge */}
          {analyst.brand_mentioned ? (
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-purple-500/10 border border-purple-500/30 text-purple-400">
              <Tag className="w-3 h-3" />
              Brand Mentioned: {analyst.mentioned_brands?.join(', ') || 'Yes'}
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
              <Tag className="w-3 h-3" />
              Brand Mentioned: None (Unbranded)
            </span>
          )}

          {/* Intent Badge */}
          <span className="px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 uppercase tracking-wider">
            {analyst.buying_intent.replace('_', ' ')}
          </span>

          {/* Sentiment Badge */}
          {analyst.sentiment && (
            <span className="px-2 py-0.5 rounded-md text-[10px] bg-slate-800 text-slate-300 border border-slate-700">
              {analyst.sentiment}
            </span>
          )}
        </div>

        {/* Link to Thread */}
        {(() => {
          const permalink = opportunity.thread_data.permalink || '';
          const isHN =
            opportunity.thread_data.thread_id.startsWith('hn_') ||
            permalink.includes('news.ycombinator.com') ||
            opportunity.thread_data.subreddit?.includes('ycombinator');

          let platformLabel = 'Reddit';
          let targetUrl = permalink;
          let tooltip = 'Open discussion on Reddit';

          if (isHN) {
            platformLabel = 'Hacker News';
            tooltip = 'Open live thread on Hacker News';
            targetUrl = permalink.startsWith('http')
              ? permalink
              : `https://news.ycombinator.com/item?id=${opportunity.thread_data.thread_id.replace('hn_', '')}`;
          } else if (permalink.startsWith('http://') || permalink.startsWith('https://')) {
            platformLabel = 'Reddit';
            targetUrl = permalink;
            tooltip = 'Open original thread on Reddit';
          } else if (permalink.startsWith('/r/')) {
            platformLabel = 'Reddit';
            targetUrl = `https://reddit.com${permalink}`;
            tooltip = 'Open original thread on Reddit';
          } else {
            // Simulated placeholder without a direct link
            const cleanSub = opportunity.thread_data.subreddit?.replace(/^r\//, '') || 'SaaS';
            platformLabel = 'Reddit Search';
            targetUrl = `https://www.reddit.com/r/${cleanSub}/search/?q=${encodeURIComponent(opportunity.thread_data.title)}`;
            tooltip = 'Search matching discussions on Reddit';
          }

          return (
            <a
              href={targetUrl}
              target="_blank"
              rel="noopener noreferrer"
              className={`p-1 rounded transition-colors flex items-center gap-1.5 text-xs font-semibold ${
                isHN
                  ? 'text-orange-400 hover:text-orange-300 hover:bg-orange-950/40 bg-orange-500/10 border border-orange-500/30 px-2.5 py-1'
                  : 'text-slate-400 hover:text-white hover:bg-dark-850 px-2 py-1'
              }`}
              title={tooltip}
            >
              <span>{platformLabel}</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          );
        })()}
      </div>

      {/* Thread Title */}
      <h3 className="text-base sm:text-lg font-bold text-white mb-2 tracking-tight">
        {opportunity.thread_data.title}
      </h3>

      {/* Full Conversation Preview Toggle */}
      <div className="mb-4">
        <button
          type="button"
          onClick={() => setShowFullPreview(!showFullPreview)}
          className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200 transition-colors mb-1"
        >
          {showFullPreview ? <ChevronUp className="w-3.5 h-3.5 text-indigo-400" /> : <ChevronDown className="w-3.5 h-3.5 text-indigo-400" />}
          <span>{showFullPreview ? 'Hide Raw Post Text' : 'Show Raw Post Text'}</span>
        </button>

        {showFullPreview && (
          <div className="p-3.5 rounded-lg bg-dark-950/90 border border-slate-800 text-xs text-slate-300 leading-relaxed max-h-48 overflow-y-auto whitespace-pre-line mt-1">
            {opportunity.thread_data.body || '(No self-text body content.)'}
          </div>
        )}
      </div>

      {/* 2. Highlighted Verbatim Evidence (Multi-Quote Support) */}
      <div className="bg-gradient-to-r from-dark-850 to-dark-850/50 border-l-4 border-amber-500 rounded-r-xl p-4 mb-4 text-xs sm:text-sm text-slate-200 relative shadow-inner">
        <div className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-amber-400 mb-2">
          <Quote className="w-3.5 h-3.5" />
          Verbatim Anchor Evidence ({analyst.evidence && analyst.evidence.length > 1 ? `${analyst.evidence.length} Quotes` : 'Anchor Quote'})
        </div>
        {analyst.evidence && analyst.evidence.length > 1 ? (
          <ul className="list-disc list-inside space-y-1 text-slate-100 italic font-serif">
            {analyst.evidence.map((quote, idx) => (
              <li key={idx}>"{quote}"</li>
            ))}
          </ul>
        ) : (
          <p className="italic font-serif leading-relaxed text-slate-100">
            "{analyst.evidence_quote}"
          </p>
        )}
      </div>

      {/* 3. Problem, Pain Point & Community Context Panel */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-3 mb-4 text-xs">
        {/* Extracted Problem & Pain Point (7 cols) */}
        <div className="md:col-span-7 p-3.5 bg-dark-950/70 border border-slate-800/80 rounded-xl space-y-2">
          <div>
            <span className="font-semibold text-slate-400 block mb-0.5 uppercase tracking-wider text-[10px]">
              Extracted Core Problem
            </span>
            <p className="text-slate-200 leading-snug">{analyst.core_problem}</p>
          </div>

          {analyst.pain_point && (
            <div>
              <span className="font-semibold text-slate-400 block mb-0.5 uppercase tracking-wider text-[10px]">
                Underlying Operational Friction
              </span>
              <p className="text-slate-300 leading-snug">{analyst.pain_point}</p>
            </div>
          )}

          {analyst.community_context && (
            <div className="pt-1.5 border-t border-slate-800/60">
              <span className="font-semibold text-indigo-300 block mb-0.5 uppercase tracking-wider text-[10px]">
                Community Norms & Scrutiny
              </span>
              <p className="text-slate-400 text-[11px] leading-snug">{analyst.community_context}</p>
            </div>
          )}
        </div>

        {/* 6D Composite Opportunity Score & Rationale (5 cols) */}
        <div className="md:col-span-5 p-3.5 bg-dark-950/70 border border-slate-800/80 rounded-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <span className="font-semibold text-slate-400 uppercase tracking-wider text-[10px] flex items-center gap-1">
                <Gauge className="w-3.5 h-3.5 text-indigo-400" />
                Opportunity Score
              </span>
              <span className={`font-mono font-bold text-base ${getScoreTextColor(score)}`}>
                {score} / 100
              </span>
            </div>

            {/* Visual Progress Bar */}
            <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden mb-2">
              <div
                className={`h-full transition-all duration-500 rounded-full ${getScoreBarColor(score)}`}
                style={{ width: `${Math.min(score, 100)}%` }}
              />
            </div>

            {/* Confidence pill */}
            <div className="flex items-center justify-between text-[11px] text-slate-400 mb-2">
              <span>Analyst Conf: <strong>{Math.round((analyst.analyst_confidence ?? 0.85) * 100)}%</strong></span>
              <span>Strategist Conf: <strong>{Math.round((strat.strategist_confidence ?? 0.85) * 100)}%</strong></span>
            </div>
          </div>

          <p className="text-[11px] text-slate-400 line-clamp-3 leading-tight pt-2 border-t border-slate-800/60">
            {strat.reasoning}
          </p>
        </div>
      </div>

      {/* 4. 6-Dimensional Breakdown Badges */}
      <div className="p-3 bg-dark-950/50 border border-slate-800/70 rounded-xl mb-4 text-xs">
        <span className="font-semibold text-slate-400 block mb-2 uppercase tracking-wider text-[10px]">
          6D Diagnostic Rubric
        </span>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-center">
          <div className="p-2 rounded-lg bg-dark-900 border border-slate-800">
            <span className="text-[10px] text-slate-400 block">Relevance</span>
            <span className="font-mono font-bold text-sm text-indigo-400">{strat.relevance_score ?? 90}/100</span>
          </div>
          <div className="p-2 rounded-lg bg-dark-900 border border-slate-800">
            <span className="text-[10px] text-slate-400 block">Intent Strength</span>
            <span className="font-mono font-bold text-sm text-cyan-400">{strat.intent_strength_score ?? 85}/100</span>
          </div>
          <div className="p-2 rounded-lg bg-dark-900 border border-slate-800">
            <span className="text-[10px] text-slate-400 block">Community Fit</span>
            <span className="font-mono font-bold text-sm text-emerald-400">{strat.community_fit_score ?? 80}/100</span>
          </div>
          <div className="p-2 rounded-lg bg-dark-900 border border-slate-800">
            <span className="text-[10px] text-slate-400 block">Credibility</span>
            <span className="font-mono font-bold text-sm text-amber-400">{strat.credibility_score ?? 85}/100</span>
          </div>
          <div className="p-2 rounded-lg bg-dark-900 border border-slate-800">
            <span className="text-[10px] text-slate-400 block">Backlash Risk</span>
            <span className="font-mono font-bold text-sm text-red-400">{strat.engagement_risk_score ?? 20}/100</span>
          </div>
        </div>
      </div>

      {/* 5. Compliance Status Badge */}
      <div className="p-3.5 bg-dark-950/80 border border-slate-800 rounded-xl mb-4 text-xs flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          {critic.critic_passed ? (
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          )}
          <span className="font-medium text-slate-300">
            Compliance Audit Status:{' '}
            <strong className={critic.critic_passed ? 'text-emerald-400 font-semibold' : 'text-amber-400 font-semibold'}>
              {critic.critic_passed ? '✓ PASSED (Anti-Astroturfing & Zero-Plug Enforced)' : `FLAGGED: ${critic.violation_category?.toUpperCase() || 'NOTES'}`}
            </strong>
          </span>
        </div>

        {critic.critic_feedback && (
          <span className="text-[11px] text-slate-400 italic block w-full mt-1 pl-6">
            Adversarial Audit Note: {critic.critic_feedback}
          </span>
        )}
      </div>

      {/* 6. Editable Text Area pre-filled with proposed_draft */}
      <div className="mt-4">
        <div className="flex items-center justify-between mb-2 text-xs font-semibold text-slate-300">
          <div className="flex items-center gap-1.5">
            <MessageSquare className="w-3.5 h-3.5 text-indigo-400" />
            <span>AI Value-First Draft (Relay Persona)</span>
          </div>
          <span className="text-slate-500 font-normal">{editedDraft.length} characters</span>
        </div>

        <textarea
          value={editedDraft}
          onChange={(e) => setEditedDraft(e.target.value)}
          rows={5}
          className="w-full bg-dark-950 border border-slate-800 hover:border-slate-700 focus:border-indigo-500 rounded-xl p-3.5 text-xs sm:text-sm text-slate-100 font-sans focus:outline-none focus:ring-2 focus:ring-indigo-500/50 resize-y leading-relaxed transition-all"
          placeholder={opportunity.sensitive_topic ? 'Drafting bypassed due to sensitive topic. Marketer may compose manual response...' : 'Refine proposed response...'}
        />
      </div>

      {/* 7. Action Buttons Panel */}
      <ActionPanel
        opportunityId={opportunity.thread_data.thread_id}
        isEditing={isEditing}
        onToggleEdit={() => setIsEditing(!isEditing)}
        onApproveAndCopy={handleApproveAndCopy}
        onApplyEdits={handleApplyEdits}
        onReject={handleReject}
      />
    </article>
  );
};
