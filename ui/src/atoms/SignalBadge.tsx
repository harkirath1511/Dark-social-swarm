export function SignalBadge({ label, tone }: { label: string; tone: 'ready' | 'watch' | 'risk' }) {
  return <span className={`ds-badge ds-badge-${tone}`}>{label}</span>;
}
