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
} from 'lucide-react';
import { Opportunity } from '../types';
import { ActionPanel } from './ActionPanel';

interface OpportunityCardProps {
  opportunity: Opportunity;
  onActionComplete: (
    threadId: string,
    action: 'approved' | 'edited' | 'rejected',
    text?: string,
    rejectionReason?: string
  ) => Promise<void>;
}

export const OpportunityCard: React.FC<OpportunityCardProps> = ({
  opportunity,
  onActionComplete,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedDraft, setEditedDraft] = useState(opportunity.draft_content);
  const [showFullPreview, setShowFullPreview] = useState(false);
  const [isResolved, setIsResolved] = useState(false);
  const [resolvedStatus, setResolvedStatus] = useState<string | null>(null);
  const [copiedToast, setCopiedToast] = useState(false);

  const score = opportunity.strategist_output.opportunity_score;

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

  const getIntentBadge = (intent: string) => {
    switch (intent.toLowerCase()) {
      case 'high':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'medium':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      default:
        return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  };

  // Button 1: Approve & Copy
  const handleApproveAndCopy = async () => {
    // Copy drafted text to clipboard
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
    setResolvedStatus('EDITED & APPROVED');
  };

  // Button 3: Reject / Discard
  const handleReject = async (reason: string) => {
    await onActionComplete(opportunity.thread_data.thread_id, 'rejected', undefined, reason);
    setIsResolved(true);
    setResolvedStatus(`REJECTED: ${reason.toUpperCase()}`);
  };

  if (isResolved) {
    return (
      <div className="bg-dark-900/60 border border-slate-800/80 rounded-2xl p-6 text-center text-slate-400 transition-all duration-300">
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
    <div className="bg-dark-900 border border-slate-800 hover:border-slate-700 rounded-2xl p-6 transition-all duration-200 shadow-xl shadow-black/40 relative">
      {/* Toast Notification */}
      {copiedToast && (
        <div className="absolute top-4 right-4 z-20 flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-600 text-white text-xs font-semibold shadow-lg animate-bounce">
          <Copy className="w-3.5 h-3.5" />
          <span>Copied to Clipboard!</span>
        </div>
      )}

      {/* 1. Source Context Meta Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2.5">
          <span className="px-2.5 py-1 rounded-md text-xs font-semibold bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            {opportunity.thread_data.subreddit}
          </span>
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <User className="w-3.5 h-3.5 text-slate-500" />
            <span>u/{opportunity.thread_data.author}</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Buying Intent Pill */}
          <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-medium border uppercase tracking-wider ${getIntentBadge(opportunity.analyst_output.buying_intent)}`}>
            {opportunity.analyst_output.buying_intent} Intent
          </span>

          {/* External Link to Thread */}
          <a
            href={opportunity.thread_data.permalink}
            target="_blank"
            rel="noopener noreferrer"
            className="text-slate-400 hover:text-white p-1 rounded hover:bg-dark-850 transition-colors flex items-center gap-1 text-xs"
            title="Open original Reddit thread"
          >
            <span>Reddit</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
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
          <span>{showFullPreview ? 'Hide Conversation Preview' : 'Show Full Conversation Preview'}</span>
        </button>

        {showFullPreview && (
          <div className="p-3.5 rounded-lg bg-dark-950/90 border border-slate-800 text-xs text-slate-300 leading-relaxed max-h-48 overflow-y-auto whitespace-pre-line mt-1">
            {opportunity.thread_data.body || '(No post body content provided by author.)'}
          </div>
        )}
      </div>

      {/* 2. Highlighted Verbatim Evidence Quote */}
      <div className="bg-gradient-to-r from-dark-850 to-dark-850/50 border-l-4 border-amber-500 rounded-r-xl p-4 mb-4 text-xs sm:text-sm text-slate-200 relative shadow-inner">
        <div className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-amber-400 mb-1.5">
          <Quote className="w-3.5 h-3.5" />
          Verbatim Anchor Evidence (Traceability Non-Negotiable)
        </div>
        <p className="italic font-serif leading-relaxed text-slate-100">
          "{opportunity.analyst_output.evidence_quote}"
        </p>
      </div>

      {/* 3. Extracted Problem & Strategist Scoring Meter */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-3 mb-4 text-xs">
        {/* Extracted Problem (7 cols) */}
        <div className="md:col-span-7 p-3.5 bg-dark-950/60 border border-slate-800/80 rounded-xl">
          <span className="font-semibold text-slate-400 block mb-1 uppercase tracking-wider text-[10px]">
            Extracted Core Problem
          </span>
          <p className="text-slate-200 leading-snug">{opportunity.analyst_output.core_problem}</p>
        </div>

        {/* Strategist Visual Progress Meter (5 cols) */}
        <div className="md:col-span-5 p-3.5 bg-dark-950/60 border border-slate-800/80 rounded-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <span className="font-semibold text-slate-400 uppercase tracking-wider text-[10px]">
                Strategist Score
              </span>
              <span className={`font-mono font-bold text-sm ${getScoreTextColor(score)}`}>
                {score} / 100
              </span>
            </div>

            {/* Visual Progress Bar */}
            <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden mb-2">
              <div
                className={`h-full transition-all duration-500 rounded-full ${getScoreBarColor(score)}`}
                style={{ width: `${Math.min(score, 100)}%` }}
              />
            </div>
          </div>

          <p className="text-[11px] text-slate-400 line-clamp-2 leading-tight">
            {opportunity.strategist_output.reasoning}
          </p>
        </div>
      </div>

      {/* 4. Compliance Status Badge */}
      <div className="p-3.5 bg-dark-950/80 border border-slate-800 rounded-xl mb-4 text-xs flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          {opportunity.critic_output.critic_passed ? (
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          )}
          <span className="font-medium text-slate-300">
            Compliance Audit Status:{' '}
            <strong className={opportunity.critic_output.critic_passed ? 'text-emerald-400 font-semibold' : 'text-amber-400 font-semibold'}>
              {opportunity.critic_output.critic_passed ? 'PASSED (Anti-Astroturfing & Zero-Plug)' : `FLAGGED WITH NOTES (${opportunity.critic_output.violation_category})`}
            </strong>
          </span>
        </div>

        {opportunity.critic_output.critic_feedback && (
          <span className="text-[11px] text-slate-400 italic block w-full mt-1 pl-6">
            Note: {opportunity.critic_output.critic_feedback}
          </span>
        )}
      </div>

      {/* 5. Editable Text Area pre-filled with proposed_draft */}
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
          placeholder="Refine proposed response..."
        />
      </div>

      {/* 6. Three Action Buttons Panel */}
      <ActionPanel
        opportunityId={opportunity.thread_data.thread_id}
        isEditing={isEditing}
        onToggleEdit={() => setIsEditing(!isEditing)}
        onApproveAndCopy={handleApproveAndCopy}
        onApplyEdits={handleApplyEdits}
        onReject={handleReject}
      />
    </div>
  );
};
