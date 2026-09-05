'use client';

import React from 'react';
import { Activity, ArrowLeft, Radio, Radar, ShieldCheck } from 'lucide-react';

interface NavbarProps { pendingCount: number; approvedCount: number; }

export const Navbar: React.FC<NavbarProps> = ({ pendingCount, approvedCount }) => (
  <header className="dash-nav"><div className="dash-nav-inner"><div className="flex items-center gap-3 min-w-0"><a href="/" className="dash-logo" aria-label="Back to Dark Social Swarm home"><Radar className="h-5 w-5" aria-hidden="true" /></a><div className="min-w-0"><div className="flex items-center gap-2"><span className="font-bold tracking-tight text-white truncate">Dark Social Swarm</span><span className="dash-pill hidden sm:inline-flex">Command center</span></div><p className="hidden md:block text-[11px] text-slate-500 font-mono">Human-in-the-loop operations workspace</p></div></div><nav aria-label="Review workspace" className="flex items-center gap-2 sm:gap-3"><a href="/" className="dash-nav-link"><ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" /><span className="hidden sm:inline">Overview</span></a><div className="dash-health hidden lg:flex"><Radio className="h-3.5 w-3.5" aria-hidden="true" /><span>Ingestion live</span></div><div className="dash-health hidden xl:flex"><Activity className="h-3.5 w-3.5" aria-hidden="true" /><span>{approvedCount} approved</span></div><div className="dash-pending"><ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" /><span>{pendingCount}<span className="hidden sm:inline"> pending</span></span></div></nav></div></header>
);
