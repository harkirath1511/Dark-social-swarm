import { Hero } from './Hero';
import { SiteNavigation } from './SiteNavigation';
import { Workflow } from './Workflow';
import { Capabilities } from './Capabilities';
import { FinalCta } from './FinalCta';

export function DarkSocialHome() {
  return <main className="ds-page"><SiteNavigation /><Hero /><Capabilities /><Workflow /><FinalCta /></main>;
}
