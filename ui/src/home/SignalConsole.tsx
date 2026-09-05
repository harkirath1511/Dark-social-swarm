'use client';

import { useEffect, useState } from 'react';
import { motion, useReducedMotion } from 'motion/react';
import { ArrowUpRight, CircleAlert, Radar, ShieldCheck } from 'lucide-react';
import { SignalBadge } from '../atoms/SignalBadge';

const signals = [
  { community: 'r/productivity', title: 'A team is losing time to scattered customer feedback', score: 92, tone: 'ready' as const, label: 'Ready to review' },
  { community: 'r/SaaS', title: 'Founder asks how to find buyers before they ask for demos', score: 86, tone: 'ready' as const, label: 'High intent' },
  { community: 'r/startups', title: 'A switching signal needs context before engagement', score: 68, tone: 'watch' as const, label: 'Needs context' },
];

export function SignalConsole() {
  const reduceMotion = useReducedMotion();
  const [isFinePointer, setIsFinePointer] = useState(false);
  const [rotation, setRotation] = useState({ x: 0, y: 0 });
  useEffect(() => { const media = window.matchMedia('(pointer: fine)'); const update = () => setIsFinePointer(media.matches); update(); media.addEventListener('change', update); return () => media.removeEventListener('change', update); }, []);
  const onMove = (event: React.PointerEvent<HTMLElement>) => { if (!isFinePointer || reduceMotion) return; const rect = event.currentTarget.getBoundingClientRect(); setRotation({ x: ((event.clientY - rect.top) / rect.height - .5) * -4, y: ((event.clientX - rect.left) / rect.width - .5) * 5 }); };
  return <motion.section className="ds-console" id="signals" aria-label="Example signal review console" onPointerMove={onMove} onPointerLeave={() => setRotation({ x: 0, y: 0 })} animate={{ rotateX: reduceMotion ? 0 : rotation.x, rotateY: reduceMotion ? 0 : rotation.y }} transition={{ type: 'spring', stiffness: 180, damping: 22 }}><div className="ds-console-glow" aria-hidden="true" /><div className="ds-console-head"><div><span className="ds-eyebrow"><Radar aria-hidden="true" size={13} />signal queue</span><strong>Community opportunities</strong></div><span className="ds-live"><i aria-hidden="true" />live scan</span></div><p className="sr-only" role="status" aria-atomic="true">3 signals ready for human review</p><div className="ds-signal-list">{signals.map((signal, index) => <motion.article className="ds-signal-row" initial={reduceMotion ? false : { opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: reduceMotion ? 0 : index * .07 }} key={signal.title}><div className="ds-score">{signal.score}</div><div className="ds-signal-copy"><span>{signal.community}</span><h3>{signal.title}</h3></div><SignalBadge tone={signal.tone} label={signal.label} /></motion.article>)}</div><div className="ds-console-footer"><span><ShieldCheck aria-hidden="true" size={15} />Human approval required</span><button type="button" aria-label="Preview signal queue"><ArrowUpRight aria-hidden="true" size={16} /></button></div><div className="ds-console-risk"><CircleAlert aria-hidden="true" size={14} />Risk checks run before every recommendation.</div></motion.section>;
}
