import { ArrowUpRight, Radar } from 'lucide-react';
import { ButtonLink } from '../atoms/ButtonLink';

export function SiteNavigation() {
  return <header className="ds-nav"><a className="ds-brand" href="#top" aria-label="Dark Social Swarm home"><span className="ds-brand-mark"><Radar aria-hidden="true" size={20} /></span><span>dark<span>social</span></span></a><nav aria-label="Primary navigation" className="ds-nav-links"><a href="#network">Network</a><a href="#capabilities">Platform</a><a href="#workflow">Workflow</a></nav><div className="ds-nav-status"><i aria-hidden="true" />System live</div><ButtonLink href="/review">Enter command center <ArrowUpRight aria-hidden="true" size={16} /></ButtonLink></header>;
}
