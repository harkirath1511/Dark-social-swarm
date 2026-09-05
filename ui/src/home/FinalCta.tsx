'use client';

import { ArrowRight, Radio, ShieldCheck } from 'lucide-react';
import { motion, useReducedMotion } from 'motion/react';
import { ButtonLink } from '../atoms/ButtonLink';

export function FinalCta() {
  const reduceMotion = useReducedMotion();
  return <section className="ds-final-wrap"><motion.div className="ds-final" initial={reduceMotion ? false : { opacity: 0, y: 26 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}><div><p className="ds-eyebrow"><Radio aria-hidden="true" size={15} />Ready for review</p><h2>Turn hidden conversations into your next move.</h2><p>Open the live workspace and see the full discover → qualify → draft → approve loop.</p></div><ButtonLink href="/review">Launch command center <ArrowRight aria-hidden="true" size={17} /></ButtonLink><div className="ds-final-proof"><ShieldCheck aria-hidden="true" size={16} />Human approval enforced</div></motion.div><footer className="ds-footer"><span>Dark Social Swarm</span><span>Community intelligence · Human control</span><span>Prototype v0.1</span></footer></section>;
}
