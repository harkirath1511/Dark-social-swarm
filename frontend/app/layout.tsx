import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Dark Social Swarm | Community signal intelligence',
  description: 'Find qualified community conversations, evaluate risk, and keep a human in control of every reply.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-dark-950 text-slate-100 antialiased selection:bg-indigo-500/30 selection:text-indigo-200">
        {children}
      </body>
    </html>
  );
}
