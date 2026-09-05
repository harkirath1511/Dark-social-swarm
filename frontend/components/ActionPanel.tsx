'use client';

import React, { useState } from 'react';
import { Check, Copy, Edit3, X, Loader2, Sparkles, Send, ShieldAlert } from 'lucide-react';
import { RejectionReason } from '../types';

interface ActionPanelProps {
  opportunityId: string;
  isEditing: boolean;
  onToggleEdit: () => void;
  onApproveAndCopy: () => Promise<void>;
  onApplyEdits: () => Promise<void>;
  onReject: (reason: RejectionReason) => Promise<void>;
  disabled?: boolean;
}

const REJECTION_REASONS: { value: RejectionReason; label: string; description: string }[] = [
  {
    value: 'wrong_community',
    label: 'Wrong Community',
    description: 'Norm violation, extreme anti-promo culture, or unsuitable subreddit.',
  },
  {
    value: 'too_promotional',
    label: 'Too Promotional',
    description: 'Context would interpret any response as unsolicited advertising.',
  },
  {
    value: 'low_intent',
    label: 'Low Intent',
    description: 'Casual opinion, rant, or theoretical chatter with zero solution urgency.',
  },
  {
    value: 'unsafe_topic',
    label: 'Unsafe Topic',
    description: 'Sensitive personal, legal, medical, crisis, or toxic discussion.',
  },
  {
    value: 'not_relevant',
    label: 'Not Relevant',
    description: 'Problem lies outside our solution domain or technical capabilities.',
  },
  {
    value: 'poor_evidence',
    label: 'Poor Evidence',
    description: 'Vague post without verifiable struggle or observable context quotes.',
  },
];

export const ActionPanel: React.FC<ActionPanelProps> = ({
  opportunityId,
  isEditing,
  onToggleEdit,
  onApproveAndCopy,
  onApplyEdits,
  onReject,
  disabled = false,
}) => {
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [selectedReason, setSelectedReason] = useState<RejectionReason>('low_intent');

  const handleAction = async (actionName: string, actionFn: () => Promise<void>) => {
    try {
      setLoadingAction(actionName);
      await actionFn();
    } finally {
      setLoadingAction(null);
    }
  };

  const handleConfirmReject = async () => {
    setShowRejectModal(false);
    await handleAction('reject', () => onReject(selectedReason));
  };

  return (
    <div className="pt-5 border-t border-slate-800/80 mt-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* State Notice */}
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
          <span>
            LangGraph <code className="text-slate-300 font-mono text-[11px] bg-dark-850 px-1.5 py-0.5 rounded border border-slate-800">interrupt()</code> review gate
          </span>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Button 3: Reject / Discard */}
          <button
            type="button"
            disabled={disabled || loadingAction !== null}
            onClick={() => setShowRejectModal(true)}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-red-900/40 bg-red-950/20 text-red-400 hover:bg-red-950/40 hover:text-red-300 transition-colors text-xs font-semibold disabled:opacity-50"
            title="Select structured calibration reason and discard"
          >
            {loadingAction === 'reject' ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <X className="w-3.5 h-3.5" />
            )}
            Reject / Discard
          </button>

          {/* Button 2: Apply Edits Toggle */}
          <button
            type="button"
            disabled={disabled || loadingAction !== null}
            onClick={onToggleEdit}
            className={`inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg border text-xs font-semibold transition-colors disabled:opacity-50 ${
              isEditing
                ? 'border-indigo-500 bg-indigo-950/40 text-indigo-300'
                : 'border-slate-700 bg-dark-850 text-slate-300 hover:bg-dark-800 hover:text-white'
            }`}
          >
            <Edit3 className="w-3.5 h-3.5 text-indigo-400" />
            {isEditing ? 'Cancel Editing' : 'Apply Edits'}
          </button>

          {/* Button 1 / Primary: Approve & Copy (or Save & Submit Edits) */}
          {isEditing ? (
            <button
              type="button"
              disabled={disabled || loadingAction !== null}
              onClick={() => handleAction('save_edits', onApplyEdits)}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs shadow-lg shadow-indigo-600/30 transition-all disabled:opacity-50"
            >
              {loadingAction === 'save_edits' ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Send className="w-3.5 h-3.5" />
              )}
              Save Edits & Authorize
            </button>
          ) : (
            <button
              type="button"
              disabled={disabled || loadingAction !== null}
              onClick={() => handleAction('approve_copy', onApproveAndCopy)}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs shadow-lg shadow-emerald-600/30 transition-all disabled:opacity-50"
            >
              {loadingAction === 'approve_copy' ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Copy className="w-3.5 h-3.5" />
              )}
              Approve & Copy
            </button>
          )}
        </div>
      </div>

      {/* Reject Reason Modal / Structured Feedback Flyout */}
      {showRejectModal && (
        <div className="mt-4 p-4 rounded-xl bg-dark-950 border border-red-900/50 text-xs animate-in fade-in duration-200">
          <div className="flex items-center gap-2 text-red-400 font-bold mb-1">
            <ShieldAlert className="w-4 h-4" />
            <span>Structured Triage Rejection (Calibrates Strategist Node)</span>
          </div>
          <p className="text-slate-400 mb-3 leading-relaxed">
            Select the structured reason for rejecting this opportunity. This telemetry tunes the Strategist agent's 6D scoring weights:
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-3">
            {REJECTION_REASONS.map((r) => (
              <label
                key={r.value}
                className={`p-2.5 rounded-lg border cursor-pointer transition-all flex flex-col justify-start ${
                  selectedReason === r.value
                    ? 'border-red-500 bg-red-950/40 text-white'
                    : 'border-slate-800 bg-dark-900 text-slate-400 hover:border-slate-700 hover:text-slate-300'
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <input
                    type="radio"
                    name={`reject-${opportunityId}`}
                    value={r.value}
                    checked={selectedReason === r.value}
                    onChange={() => setSelectedReason(r.value)}
                    className="accent-red-500 w-3.5 h-3.5"
                  />
                  <span className="font-semibold text-xs">{r.label}</span>
                </div>
                <span className="text-[10px] text-slate-400 pl-5.5 leading-snug">{r.description}</span>
              </label>
            ))}
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setShowRejectModal(false)}
              className="px-3 py-1.5 rounded-lg border border-slate-700 bg-dark-850 text-slate-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleConfirmReject}
              className="px-4 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white font-semibold text-xs shadow-md shadow-red-600/30 transition-all"
            >
              Confirm Structured Rejection
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
