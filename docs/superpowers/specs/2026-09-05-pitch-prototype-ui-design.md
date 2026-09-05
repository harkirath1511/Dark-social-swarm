# Pitch Prototype UI Design

## Goal

Turn Dark Social Swarm into a convincing, end-to-end pitch prototype with a cinematic marketing page and a functional human-review workspace.

## Visual direction

The product uses a “Signal Command Center” theme: near-black navy surfaces, cyan signal light, violet depth, and restrained amber warnings. The interface should feel operational and intelligent rather than like a generic admin template. Fine grid textures, scanning lines, an unmistakable rotating globe, layered panels, and compact telemetry reinforce the community-intelligence story.

Framer Motion handles meaningful entrances, page-section reveals, live status pulses, and review-card transitions. Animation uses opacity and transforms, remains interruptible, and resolves to a complete static layout for `prefers-reduced-motion` users.

## Routes and experience

- `/` is the pitch surface: shared navigation, animated hero, visible globe and signal orbit, live product console, trust metrics, workflow, product capabilities, and final review-desk CTA.
- `/review` is the working prototype: persistent command header, backend status, overview metrics, pending opportunity queue, live community stream, simulation actions, and approve/edit/reject controls.
- Browser API traffic uses same-origin `/api/*` paths, proxied by Next.js to FastAPI through `BACKEND_URL`.

## Architecture

The existing `ui/` package remains presentation-only and exports landing-page sections. `frontend/` owns routes, API calls, backend data mapping, and dashboard state. No new dependency is introduced; React, Next.js, D3, Lucide, Tailwind, and the existing `motion` package provide the complete prototype.

## Quality bar

Both routes share one theme, navigation language, focus treatment, spacing rhythm, and status vocabulary. Controls remain at least 44px high, status never relies on color alone, headings remain sequential, the globe is decorative to assistive technology, and layouts must not overflow at 375px. The existing backend workflow tests and production build must remain green.

