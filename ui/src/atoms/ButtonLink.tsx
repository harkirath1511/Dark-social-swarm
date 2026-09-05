import { ReactNode } from 'react';

export function ButtonLink({ href, children }: { href: string; children: ReactNode }) {
  return <a className="ds-button ds-button-primary" href={href}>{children}</a>;
}
