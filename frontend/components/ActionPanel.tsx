'use client';

import React, { useState } from 'react';
import { Check, Copy, Edit3, X, Loader2, Sparkles, Send, MessageSquare } from 'lucide-react';

interface ActionPanelProps {
  opportunityId: string;
  isEditing: boolean;
  onToggleEdit: () => void;
  onApproveAndCopy: () => Promise<void>;
  onApplyEdits: () => Promise<void>;
  onReject: (reason: string) => Promise<void>;
  disabled?: boolean;
}

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
  const [rejectReason, setRejectReason] = useState('Low commercial intent');
  const [customReason, setCustomReason] = useState('');

  const handleAction = async (actionName: string, actionFn: () => Promise<void>) => {
    try {
      setLoadingAction(actionName);
      await actionFn();
    } finally {
      setLoadingAction(null);
    }
  };

  const handleConfirmReject = async () => {
    const finalReason = rejectReason === 'Other' ? customReason || 'Discarded by marketer' : rejectReason;
    setShowRejectModal(false);
    await handleAction('reject', () => onReject(finalReason));
  };

  return (
    <div className="pt-4 border-t border-slate-800/80 mt-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* State Notice */}
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
          <span>LangGraph <code className="text-slate-300 font-mono text-[11px] bg-dark-850 px-1.5 py-0.5 rounded border border-slate-800">interrupt()</code> state</span>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2.5">
          {/* Button 3: Reject / Discard */}
          <button
            type="button"
            disabled={disabled || loadingAction !== null}
            onClick={() => setShowRejectModal(true)}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-red-900/40 bg-red-950/20 text-red-400 hover:bg-red-950/40 hover:text-red-300 transition-colors text-xs font-semibold disabled:opacity-50"
            title="Log rejection reason and discard opportunity"
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

      {/* Reject Reason Modal / Feedback Flyout */}
      {showRejectModal && (
        <div className="mt-4 p-4 rounded-xl bg-dark-950 border border-red-900/40 text-xs">
          <span className="font-bold text-red-400 block mb-1.5">
            Log Rejection Reason (Calibrates Strategist Agent)
          </span>
          <p className="text-slate-400 mb-2">
            Select why this opportunity should not be engaged to tune future scoring weights:
          </p>

          <select
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            className="w-full bg-dark-900 border border-slate-700 rounded-lg p-2 text-slate-200 text-xs mb-2 focus:outline-none focus:ring-1 focus:ring-red-500"
          >
            <option value="Low commercial intent">Low commercial intent / casual discussion</option>
            <option value="High promotional blowback risk">High promotional blowback risk in subreddit</option>
            <option value="Off-topic or irrelevant product fit">Off-topic or irrelevant product fit</option>
            <option value="Deceptive or spam post">Deceptive or spam post</option>
            <option value="Other">Other custom reason</option>
          </select>

          {rejectReason === 'Other' && (
            <input
              type="text"
              value={customReason}
              onChange={(e) => setCustomReason(e.target.value)}
              placeholder="Enter custom rejection reason..."
              className="w-full bg-dark-900 border border-slate-700 rounded-lg p-2 text-slate-200 text-xs mb-2 focus:outline-none focus:ring-1 focus:ring-red-500"
            />
          )}

          <div className="flex items-center justify-end gap-2 mt-2">
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
              className="px-3.5 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white font-semibold shadow-md shadow-red-600/30"
            >
              Confirm Rejection
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
