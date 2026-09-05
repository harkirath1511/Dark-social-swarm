import type { LucideIcon } from 'lucide-react';

interface DashboardMetricProps {
  icon: LucideIcon;
  label: string;
  value: string | number;
  detail: string;
  tone?: 'cyan' | 'violet' | 'green' | 'amber';
}

export function DashboardMetric({ icon: Icon, label, value, detail, tone = 'cyan' }: DashboardMetricProps) {
  return <article className={`dash-metric dash-metric-${tone}`}><div className="dash-metric-icon"><Icon aria-hidden="true" className="h-4 w-4" /></div><div><p>{label}</p><strong>{value}</strong><span>{detail}</span></div></article>;
}
