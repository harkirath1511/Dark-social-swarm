# Pitch Prototype UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a pitch-ready landing page and operational review dashboard using the merged backend contract.

**Architecture:** The presentation-only `ui/` package owns the landing experience and theme tokens. The Next.js `frontend/` owns routing, same-origin API access, state, and the review dashboard.

**Tech Stack:** Next.js 14, React 18, TypeScript, Tailwind CSS, Motion, D3, Lucide React.

**Spec:** `docs/superpowers/specs/2026-09-05-pitch-prototype-ui-design.md`

## Global Constraints

- Add no new frontend dependencies.
- Keep `/` and `/review` as the two public product routes.
- Send browser API calls through `/api/*` and the Next.js backend rewrite.
- Respect `prefers-reduced-motion` and keep controls at least 44px high.
- Preserve approve, edit, reject, refresh, feed, and custom-ingest behavior.

---

### Task 1: Lock the pitch route contract

**Files:**
- Modify: `frontend/tests/test_homepage.mjs`
- Modify: `frontend/tests/test_api_proxy.mjs`

**Interfaces:**
- Consumes: server-rendered `/` HTML and `next.config.js`.
- Produces: assertions for the command-center sections, visible map semantics, `/review` CTA, and `/api` rewrite.

- [ ] Add assertions for `Community signal network`, `How the swarm works`, `Built for human judgment`, and `href="/review"`.
- [ ] Run `npm run test:homepage` and confirm it fails on the missing new sections.
- [ ] Keep the API proxy test asserting `/api/:path*` targets `http://localhost:8000/api/:path*`.

### Task 2: Rebuild the landing experience

**Files:**
- Modify: `ui/src/home/DarkSocialHome.tsx`
- Modify: `ui/src/home/SiteNavigation.tsx`
- Modify: `ui/src/home/Hero.tsx`
- Modify: `ui/src/home/RotatingGlobe.tsx`
- Modify: `ui/src/home/SignalConsole.tsx`
- Modify: `ui/src/home/Workflow.tsx`
- Create: `ui/src/home/Capabilities.tsx`
- Create: `ui/src/home/FinalCta.tsx`
- Modify: `ui/src/index.ts`
- Modify: `ui/src/styles/tokens.css`

**Interfaces:**
- Consumes: presentation-only static content and `href="/review"`.
- Produces: `DarkSocialHome` with hero, network console, workflow, capabilities, and CTA sections.

- [ ] Compose the new sections and export them through `ui/src/index.ts`.
- [ ] Implement transform/opacity Motion sequences and reduced-motion fallbacks.
- [ ] Give the globe an explicit responsive stage so its sphere, dots, and grid remain visible.
- [ ] Run `npm run test:homepage` and confirm the landing contract passes.

### Task 3: Theme the operational review route

**Files:**
- Modify: `frontend/app/review/page.tsx`
- Modify: `frontend/components/Navbar.tsx`
- Modify: `frontend/components/OpportunityCard.tsx`
- Modify: `frontend/components/LiveStreamFeed.tsx`
- Modify: `frontend/components/ActionPanel.tsx`
- Modify: `frontend/app/globals.css`
- Create: `frontend/components/DashboardMetric.tsx`

**Interfaces:**
- Consumes: `getReviewQueue`, `getFeed`, `submitReview`, and `ingestCustom` from `frontend/lib/api.ts`.
- Produces: a responsive dashboard with live metrics, queue controls, readable opportunities, and animated state transitions.

- [ ] Add the shared command-center shell and metric row.
- [ ] Apply consistent surfaces, focus styles, status treatments, and responsive spacing to the queue and feed.
- [ ] Animate dashboard entrance and opportunity resolution without changing API behavior.
- [ ] Run `node tests/test_ui_flow.mjs` and confirm all review actions pass.

### Task 4: Verify the pitch prototype

**Files:**
- Test: `frontend/tests/test_homepage.mjs`
- Test: `frontend/tests/test_api_proxy.mjs`
- Test: `frontend/tests/test_ui_flow.mjs`

**Interfaces:**
- Consumes: completed `/`, `/review`, and API proxy.
- Produces: passing tests, production build, and visual verification.

- [ ] Run `npm test` and require zero failures.
- [ ] Run `npm run build` and require exit code 0.
- [ ] Inspect `/` and `/review` in a browser, including a 375px layout and reduced-motion behavior.
- [ ] Run `git diff --check` and require no whitespace errors.

