# Dark Social UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reusable local UI package and immersive, accessible Dark Social Swarm homepage while retaining the current review desk at `/review`.

**Architecture:** `ui/` exports presentational React components and semantic CSS tokens. `frontend/` links the package through a local dependency, asks Next.js to transpile it, hosts the homepage at `/`, and moves its existing client-side review desk to `/review` unchanged in behavior.

**Tech Stack:** Next.js 14, React 18, TypeScript, Tailwind CSS 3, Motion, Lucide React, Node integration tests.

**Spec:** `docs/superpowers/specs/2026-09-05-dark-social-ui-design.md`

## Global Constraints

- `ui/` must expose `@dark-social/ui` without API calls or backend domain types.
- The package must declare React, React DOM, Motion, and Lucide React as peer dependencies.
- The homepage uses dark semantic CSS tokens, Lucide icons, labels in addition to color, visible focus indicators, and reduced-motion-safe transform/opacity animation only.
- The responsive layout must stack at 375px and form two hero columns from 1024px.
- The current review workflow remains reachable at `/review`.

---

### Task 1: Add a failing homepage integration test

**Files:**
- Create: `frontend/tests/test_homepage.mjs`
- Modify: `frontend/package.json`

**Interfaces:**
- Produces: `npm run test:homepage`, a test that starts `next dev`, fetches `/`, and asserts the page includes the product heading, the `/review` CTA, and a human-readable signal status.

- [ ] **Step 1: Write the failing test**

```js
assert.match(html, /Find the conversations that move your market/i)
assert.match(html, /href="\/review"/)
assert.match(html, /3 signals ready for human review/i)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm run test:homepage`

Expected: FAIL because the current root page is the review desk and does not render the proposed homepage text.

- [ ] **Step 3: Add the script entry**

```json
"test:homepage": "node tests/test_homepage.mjs"
```

- [ ] **Step 4: Re-run the test to verify the expected red failure**

Run: `npm run test:homepage`

Expected: FAIL on a missing homepage assertion, not a server startup error.

### Task 2: Create the local UI package and link it to Next.js

**Files:**
- Create: `ui/package.json`
- Create: `ui/src/index.ts`
- Create: `ui/src/styles/tokens.css`
- Modify: `frontend/package.json`
- Modify: `frontend/next.config.js`
- Modify: `frontend/tailwind.config.js`
- Modify: `frontend/app/globals.css`

**Interfaces:**
- Produces: `@dark-social/ui` and the public stylesheet subpath `@dark-social/ui/styles/tokens.css`.
- Consumes: the existing `motion` and `lucide-react` dependencies from `frontend`.

- [ ] **Step 1: Create the package contract**

```json
{
  "name": "@dark-social/ui",
  "private": true,
  "version": "0.1.0",
  "exports": { ".": "./src/index.ts", "./styles/tokens.css": "./src/styles/tokens.css" },
  "peerDependencies": { "lucide-react": "^0.453.0", "motion": "^13.2.0", "react": "^18.3.1", "react-dom": "^18.3.1" }
}
```

- [ ] **Step 2: Configure the consuming app**

```js
const nextConfig = { reactStrictMode: true, transpilePackages: ['@dark-social/ui'] }
```

Add `@dark-social/ui: "file:../ui"` to `frontend` dependencies and `../ui/src/**/*.{ts,tsx}` to Tailwind content. Import the package tokens before app-specific global rules.

- [ ] **Step 3: Install and type-check the package boundary**

Run: `npm install && npm run build`

Expected: build progresses beyond package resolution; later homepage content work may still be incomplete.

### Task 3: Implement reusable visual primitives and homepage sections

**Files:**
- Create: `ui/src/atoms/ButtonLink.tsx`
- Create: `ui/src/atoms/SignalBadge.tsx`
- Create: `ui/src/home/SiteNavigation.tsx`
- Create: `ui/src/home/SignalConsole.tsx`
- Create: `ui/src/home/Hero.tsx`
- Create: `ui/src/home/Workflow.tsx`
- Modify: `ui/src/index.ts`

**Interfaces:**
- Produces: `DarkSocialHome`, exported from `@dark-social/ui`.
- Consumes: `href="/review"` as the product route and no backend data.

- [ ] **Step 1: Implement button and badge primitives**

```tsx
export function ButtonLink({ href, children }: { href: string; children: React.ReactNode }) {
  return <a className="ds-button ds-button-primary" href={href}>{children}</a>
}
```

```tsx
export function SignalBadge({ label, tone }: { label: string; tone: 'ready' | 'watch' | 'risk' }) {
  return <span className={`ds-badge ds-badge-${tone}`}>{label}</span>
}
```

- [ ] **Step 2: Implement the static signal console**

Render three fictional rows with visible community, score, intent text, and a single `role="status" aria-atomic="true"` message reading `3 signals ready for human review`.

- [ ] **Step 3: Implement the hero and workflow sections**

Use `motion/react` for one opacity/translate entrance sequence. Keep the pointer-depth transform in a client leaf component, activate only for `pointer: fine`, and render the final static transform under reduced motion. Use Lucide `Radar`, `ShieldCheck`, `Search`, `Sparkles`, and `Send` icons with visible labels.

- [ ] **Step 4: Export one composed homepage**

```tsx
export function DarkSocialHome() {
  return <main><SiteNavigation /><Hero /><Workflow /></main>
}
```

### Task 4: Preserve the review desk and make the homepage the root route

**Files:**
- Create: `frontend/app/review/page.tsx`
- Modify: `frontend/app/page.tsx`
- Modify: `frontend/app/layout.tsx`

**Interfaces:**
- Consumes: `DarkSocialHome` from `@dark-social/ui`.
- Produces: `/` for the marketing homepage and `/review` for the former review desk.

- [ ] **Step 1: Move the existing root review-desk component intact**

Copy the existing client component into `app/review/page.tsx`; preserve all API calls, state mappings, and action handlers.

- [ ] **Step 2: Replace the root route with the package homepage**

```tsx
import { DarkSocialHome } from '@dark-social/ui'

export default function HomePage() {
  return <DarkSocialHome />
}
```

- [ ] **Step 3: Set homepage metadata and main-region styling**

Update title and description to the social-signal product value proposition without changing the shared document language or dark theme default.

- [ ] **Step 4: Run the homepage test to verify green**

Run: `npm run test:homepage`

Expected: PASS with the heading, review link, and signal status in server-rendered HTML.

### Task 5: Verify the UI and existing workflow safeguards

**Files:**
- Test: `frontend/tests/test_homepage.mjs`
- Test: `frontend/tests/test_ui_flow.mjs`

- [ ] **Step 1: Run focused homepage verification**

Run: `npm run test:homepage`

Expected: PASS.

- [ ] **Step 2: Run existing review API-flow verification**

Run: `node tests/test_ui_flow.mjs`

Expected: all GET and action POST checks pass.

- [ ] **Step 3: Build the production app**

Run: `npm run build`

Expected: Next.js production build exits 0.

- [ ] **Step 4: Inspect responsive states**

Run the app and inspect `/` at 375px and 1440px. Confirm no horizontal overflow, visible keyboard focus, a static/reduced-motion-safe hero, and a reachable `/review` link.
