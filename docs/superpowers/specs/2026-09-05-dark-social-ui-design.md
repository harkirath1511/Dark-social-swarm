# Dark Social Swarm UI Design

## Goal

Create a reusable UI package and a new homepage for Dark Social Swarm that turns the existing review workflow into a polished, dark, social-signal intelligence product.

## Reference interpretation

The supplied `scroll-locked-video-hero` is a visual reference, not a component to copy directly. Its music tracks, synthetic sound, global wheel/touch listeners, remote media URLs, and continuous physics loop do not serve the review workflow and would create accessibility and performance problems in this application.

The implementation will retain the reference's useful traits:

- immersive, full-width dark hero with a real visual asset;
- navy base, cyan signal glow, and restrained amber emphasis;
- a dimensional central panel with pointer-responsive depth on fine pointers only;
- compact controls and layered information surfaces;
- a deliberately simpler, static mobile composition.

## Architecture

`ui/` is a local TypeScript component package named `@dark-social/ui`. It contains visual primitives and homepage sections only; it never calls the backend and has no knowledge of review-queue types. `frontend/` owns routes, data fetching, review actions, and state, and consumes the package as a transpiled local dependency.

The homepage remains in the existing Next.js app. A client-only hero component is limited to pointer depth and small Motion animations. All other sections are server-compatible presentational components. The existing review desk remains available and is not functionally changed in this slice.

## Homepage

1. **Navigation:** product mark, concise navigation labels, and one visible primary action that leads to the review desk.
2. **Hero:** headline describing opportunity discovery from community conversations; supporting copy; primary review CTA; a signal-console visual that replaces the reference's music player/video.
3. **Signal preview:** three compact, fictional opportunity rows with confidence, community, and risk/status labels. These are static marketing examples, not live backend data.
4. **Workflow strip:** discover, qualify, review, and engage steps, each using a Lucide icon and text label.
5. **Trust/accessibility:** semantic landmarks, meaningful CTA labels, visible keyboard focus, text labels in addition to color, and reduced-motion support.

## Visual system

- Default appearance is dark: ink/navy surfaces with elevated panels, subtle grid/aurora background treatment, cyan as the interactive signal color, and amber as an attention color.
- Semantic custom properties define background, panel, text, muted text, border, signal, attention, success, and danger colors. Components must consume these tokens rather than hardcoded one-off colors.
- Body typography uses the project's system sans stack. Scores, identifiers, and timestamps use a monospaced style only where it improves scanning.
- Motion uses `motion` with opacity and transform only. Hero depth is disabled for touch, keyboard, and `prefers-reduced-motion` users. No autoplaying carousel, drag-only interaction, global listeners, audio, or remote video is introduced.
- Layout is mobile-first, has no horizontal scrolling at 375px, uses a compact stacked hero on small screens, and becomes a two-column hero at 1024px and above.

## Package boundary

Create these modules:

- `ui/src/atoms/` for reusable badge and button primitives;
- `ui/src/home/` for navigation, hero, console preview, and workflow sections;
- `ui/src/styles/tokens.css` for shared CSS custom properties;
- `ui/src/index.ts` as the public import surface.

`frontend/next.config.js` transpiles `@dark-social/ui`; its Tailwind content paths include `../ui/src`. `frontend/package.json` references the local package. React, React DOM, Motion, and Lucide remain peer dependencies in `ui/` so the application has one runtime copy of each.

## Verification

- Build the Next.js app successfully after local-package linking.
- Preserve the existing UI-flow test and add lightweight assertions that the homepage exposes its heading, primary review link, and accessible signal-status labels.
- Inspect the page at desktop and mobile widths; use the production build as the final type and dependency boundary check.
