import { ArrowRight, ScanSearch } from 'lucide-react';
import { ButtonLink } from '../atoms/ButtonLink';
import { SignalConsole } from './SignalConsole';
import { RotatingGlobe } from './RotatingGlobe';

export function Hero() {
  return <section className="ds-hero" id="top"><div className="ds-hero-copy"><p className="ds-eyebrow"><ScanSearch aria-hidden="true" size={15} />community intelligence, without the noise</p><h1>Find the conversations that <em>move your market.</em></h1><p className="ds-lede">Dark Social Swarm listens for real buying signals, qualifies the evidence, and routes every response through human review.</p><div className="ds-actions"><ButtonLink href="/review">Review live signals <ArrowRight aria-hidden="true" size={17} /></ButtonLink><a className="ds-text-link" href="#workflow">See how it works</a></div><dl className="ds-stats"><div><dt>92%</dt><dd>signal confidence</dd></div><div><dt>&lt; 3 min</dt><dd>to human review</dd></div><div><dt>0</dt><dd>autoposted replies</dd></div></dl></div><div className="ds-hero-visual"><RotatingGlobe /><SignalConsole /></div></section>;
}
