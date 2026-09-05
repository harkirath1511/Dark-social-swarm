'use client';

import { motion, useReducedMotion } from 'motion/react';
import { Activity, BrainCircuit, MessageSquareText, ShieldCheck } from 'lucide-react';

const capabilities = [
  { icon: Activity, label: 'Discover', title: 'Always-on signal capture', text: 'Continuously watch the conversations where buyers describe real operational pain.', stat: '24/7', tone: 'cyan' },
  { icon: BrainCircuit, label: 'Qualify', title: 'Six-dimensional scoring', text: 'Rank relevance, intent, community fit, credibility, risk, and confidence together.', stat: '6D', tone: 'violet' },
  { icon: MessageSquareText, label: 'Draft', title: 'Context-aware responses', text: 'Create useful, evidence-grounded drafts that match each community’s norms.', stat: '<3m', tone: 'amber' },
  { icon: ShieldCheck, label: 'Control', title: 'Human authorization gate', text: 'Nothing publishes automatically. Every response reaches a marketer first.', stat: '0 auto', tone: 'green' },
];

export function Capabilities() {
  const reduceMotion = useReducedMotion();
  return <section className="ds-capabilities" id="capabilities" aria-labelledby="capabilities-heading"><div className="ds-section-kicker"><p className="ds-eyebrow">One intelligence layer</p><h2 id="capabilities-heading">Built for human judgment.<br /><span>Powered by an agent swarm.</span></h2><p>Move from scattered community chatter to an actionable, auditable review queue.</p></div><div className="ds-capability-grid">{capabilities.map(({ icon: Icon, label, title, text, stat, tone }, index) => <motion.article className={`ds-capability ds-tone-${tone}`} key={title} initial={reduceMotion ? false : { opacity: 0, y: 22 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: '-80px' }} transition={{ delay: index * .06, duration: .42 }}><div className="ds-capability-top"><span><Icon aria-hidden="true" size={18} />{label}</span><strong>{stat}</strong></div><h3>{title}</h3><p>{text}</p><div className="ds-capability-line" aria-hidden="true"><i /></div></motion.article>)}</div></section>;
}
