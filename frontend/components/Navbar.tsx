'use client';

import React from 'react';
import { ShieldCheck, Cpu, Radio, Sparkles } from 'lucide-react';

interface NavbarProps {
  pendingCount: number;
  approvedCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({ pendingCount, approvedCount }) => {
  return (
    <header className="border-b border-slate-800/80 bg-dark-900/90 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand & Subtitle */}
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-600 to-cyan-500 p-[1px] shadow-lg shadow-indigo-500/20">
            <div className="w-full h-full bg-dark-900 rounded-[11px] flex items-center justify-center">
              <Sparkles className="h-5 w-5 text-indigo-400 animate-pulse" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-tight text-white">Dark Social Swarm</span>
              <span className="text-[10px] uppercase tracking-wider font-semibold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                HITL Desk
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">
              Problem-First Conversation Intelligence & Triage
            </p>
          </div>
        </div>

        {/* System Status Indicators */}
        <div className="flex items-center gap-3">
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-dark-850 border border-slate-800 text-xs">
            <Radio className="h-3.5 w-3.5 text-emerald-400 animate-pulse" />
            <span className="text-slate-300">PRAW Ingestion: <strong className="text-emerald-400 font-medium">Streaming</strong></span>
          </div>

          <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-dark-850 border border-slate-800 text-xs">
            <Cpu className="h-3.5 w-3.5 text-indigo-400" />
            <span className="text-slate-300">LangGraph Checkpointer: <strong className="text-indigo-400 font-medium">interrupt() active</strong></span>
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-indigo-950/40 border border-indigo-800/40 text-xs text-indigo-200">
            <ShieldCheck className="h-3.5 w-3.5 text-indigo-400" />
            <span>Pending Review: <strong className="font-bold text-white ml-1">{pendingCount}</strong></span>
          </div>
        </div>
      </div>
    </header>
  );
};
