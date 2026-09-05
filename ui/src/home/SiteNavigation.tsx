import { ArrowUpRight, Radar } from 'lucide-react';
import { ButtonLink } from '../atoms/ButtonLink';

export function SiteNavigation() {
  return <header className="ds-nav"><a className="ds-brand" href="#top" aria-label="Dark Social Swarm home"><Radar aria-hidden="true" size={20} /><span>dark<span>social</span></span></a><nav aria-label="Primary navigation" className="ds-nav-links"><a href="#workflow">Workflow</a><a href="#signals">Signals</a></nav><ButtonLink href="/review">Open review desk <ArrowUpRight aria-hidden="true" size={16} /></ButtonLink></header>;
}
