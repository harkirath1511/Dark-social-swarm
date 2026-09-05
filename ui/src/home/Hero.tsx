'use client';

import { ArrowRight, ScanSearch } from 'lucide-react';
import { motion, useReducedMotion } from 'motion/react';
import { ButtonLink } from '../atoms/ButtonLink';
import { SignalConsole } from './SignalConsole';
import { RotatingGlobe } from './RotatingGlobe';

export function Hero() {
  const reduceMotion = useReducedMotion();
  const rise = reduceMotion ? false : { opacity: 0, y: 24 };
  return <section className="ds-hero" id="top"><motion.div className="ds-hero-copy" initial={rise} animate={{ opacity: 1, y: 0 }} transition={{ duration: .65, ease: [0.22, 1, 0.36, 1] }}><p className="ds-eyebrow"><ScanSearch aria-hidden="true" size={15} />AI-native community intelligence</p><h1>See intent <span>before</span> it becomes a lead.</h1><p className="ds-lede">Dark Social Swarm monitors high-signal communities, qualifies the evidence, and prepares useful responses—while humans stay in control.</p><div className="ds-actions"><ButtonLink href="/review">Open live review queue <ArrowRight aria-hidden="true" size={17} /></ButtonLink><a className="ds-text-link" href="#network">Explore the network <span aria-hidden="true">↓</span></a></div><dl className="ds-stats"><div><dt>24/7</dt><dd>community monitoring</dd></div><div><dt>6D</dt><dd>opportunity scoring</dd></div><div><dt>100%</dt><dd>human authorized</dd></div></dl></motion.div><motion.div className="ds-hero-visual" id="network" initial={reduceMotion ? false : { opacity: 0, scale: .94 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: .8, delay: .12 }}><div className="ds-orbit ds-orbit-one" aria-hidden="true" /><div className="ds-orbit ds-orbit-two" aria-hidden="true" /><RotatingGlobe /><div className="ds-network-label"><span>Community signal network</span><strong>14 sources connected</strong></div><SignalConsole /></motion.div></section>;
}
