# Live Agent Stream Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show real swarm-agent execution live in the review dashboard, merge the newest backend changes safely, and ship the validated prototype to `main`.

**Architecture:** Move the WebSocket connection manager into a neutral API module so graph nodes and routes share one broadcaster without circular imports. Wrap every LangGraph node with an instrumentation function that emits safe lifecycle envelopes, then consume those envelopes in a Motion-powered client panel with accessible text states, reconnect handling, and a bounded timeline.

**Tech Stack:** FastAPI, LangGraph, pytest, Next.js, React, TypeScript, Motion, WebSocket

**Spec:** `docs/superpowers/specs/2026-09-05-pitch-prototype-ui-design.md`

## Global Constraints

- Preserve every existing REST endpoint and graph routing decision.
- Emit only presentation-safe metadata; never stream prompts, credentials, or environment values.
- Represent state with text and icons in addition to color, and respect reduced-motion preferences.
- Run Next.js development and production build processes sequentially to avoid `.next` cache corruption.

---

### Task 1: Merge the latest backend

**Files:**
- Modify: files changed by `origin/main`, if any

**Interfaces:**
- Consumes: local pitch-prototype checkpoint and `origin/main`
- Produces: a conflict-free `main` containing both histories

- [ ] **Step 1: Checkpoint the current prototype**

Run `git add` on the reviewed UI files and commit them with signing disabled.

- [ ] **Step 2: Fetch and inspect upstream**

Run `git fetch origin main`, then inspect `HEAD..origin/main` and the three-dot diff.

- [ ] **Step 3: Merge and resolve conflicts**

Run `git merge origin/main`; preserve upstream backend behavior and the local themed frontend where conflicts overlap.

- [ ] **Step 4: Verify the merge tree**

Run `git diff --check` and confirm `git status` contains no unmerged paths.

### Task 2: Backend lifecycle telemetry

**Files:**
- Create: `backend/app/api/stream.py`
- Create: `backend/app/swarm/telemetry.py`
- Create: `backend/tests/test_swarm_telemetry.py`
- Modify: `backend/app/api/routes.py`
- Modify: `backend/app/swarm/graph.py`

**Interfaces:**
- Consumes: async LangGraph node callables and `SwarmState`
- Produces: `instrument_node(agent_name, node, broadcaster=ws_manager)` and WebSocket envelopes with `type`, `timestamp`, and `data`

- [ ] **Step 1: Write lifecycle contract tests**

Add tests proving a successful node emits `AGENT_STARTED` followed by `AGENT_COMPLETED`, includes the agent/thread/iteration metadata, returns the node update unchanged, and excludes raw body text. Add a failure test proving `AGENT_FAILED` is emitted before the original exception is re-raised.

- [ ] **Step 2: Run tests and verify RED**

Run `python3 -m pytest backend/tests/test_swarm_telemetry.py -q`; expect import failure because `app.swarm.telemetry` does not exist.

- [ ] **Step 3: Implement the broadcaster and wrapper**

Create the shared connection manager and the minimal async wrapper needed by the tests. Build event summaries only from safe fields such as title, community, score, decision, critic result, and sensitive status.

- [ ] **Step 4: Run tests and verify GREEN**

Run `python3 -m pytest backend/tests/test_swarm_telemetry.py -q`; expect all lifecycle tests to pass.

- [ ] **Step 5: Instrument graph nodes**

Register wrapped analyst, strategist, sensitive gate, drafter, critic, and human-review nodes while leaving all edges and conditional routers unchanged. Import the shared broadcaster in routes so existing opportunity events continue to reach the same clients.

- [ ] **Step 6: Run backend regression tests**

Run `python3 -m pytest backend/tests -q`; expect the full suite to pass.

### Task 3: Live pipeline dashboard

**Files:**
- Create: `frontend/components/AgentLivePanel.tsx`
- Create: `frontend/lib/agent-stream.ts`
- Create: `frontend/tests/test_agent_stream.mjs`
- Modify: `frontend/app/review/page.tsx`
- Modify: `frontend/app/globals.css`
- Modify: `frontend/package.json`

**Interfaces:**
- Consumes: backend WebSocket lifecycle envelopes
- Produces: `getAgentStreamUrl(locationLike, configuredUrl?)`, parsed lifecycle events, and `<AgentLivePanel />`

- [ ] **Step 1: Write URL and event-state tests**

Add literal assertions for configured WebSocket URLs, localhost development fallback, secure same-origin fallback, ordered bounded event history, and start/completion/failure state transitions.

- [ ] **Step 2: Run tests and verify RED**

Run `npm run test:agent-stream`; expect failure because the stream helper does not exist.

- [ ] **Step 3: Implement the stream model**

Create pure helpers for endpoint selection and lifecycle state reduction, retaining at most 40 events so the UI cannot grow without bound.

- [ ] **Step 4: Run tests and verify GREEN**

Run `npm run test:agent-stream`; expect all helper tests to pass.

- [ ] **Step 5: Build the live panel**

Connect with native WebSocket, retry after disconnect, render all six agents with icon and text status, animate active/completed transitions with Motion, announce connection changes, and render a scrollable timestamped event timeline.

- [ ] **Step 6: Integrate and style**

Place the panel below dashboard metrics and before the review queue. Add responsive styles consistent with the established cyan/violet command-center theme and reduced-motion behavior.

### Task 4: Final verification and delivery

**Files:**
- Modify: only files required by failures found during verification

**Interfaces:**
- Consumes: merged backend and completed frontend
- Produces: tested commit pushed to `origin/main`

- [ ] **Step 1: Run repository verification**

Run backend tests, `npm test`, `npm run build`, and `git diff --check` sequentially.

- [ ] **Step 2: Exercise the real flow**

Start backend and frontend, open `/review`, submit a custom discussion, and verify that agent lifecycle events appear while the request runs.

- [ ] **Step 3: Commit the feature**

Stage the exact implementation and test files and commit with signing disabled.

- [ ] **Step 4: Push**

Confirm `origin/main` has not advanced since the merge, then run `git push origin main`.
