# Dark Social Swarm

> **AI-Driven Conversation Intelligence & Opportunity Triage System**  
> *Shifting social listening from keyword-match spam to problem-first community assistance.*

---

## The Paradigm Shift

Traditional social listening relies on:
```
Brand / Competitor Mentions -> Keyword Match -> Alert -> Spam Outreach
```
This fails in "Dark Social" and organic community discussions where prospective users express problems, frustration, or buying intent without ever naming a specific brand or tool.

**Dark Social Swarm** shifts the pipeline to:
```
Problem -> Context -> Intent -> Opportunity Evaluation -> Compliance Review -> Human Approval
```

### System Non-Negotiables
1. **Never auto-publish:** AI must never post directly to Reddit. Every output must conclude in a Human-in-the-Loop review state.
2. **Value-First Engagement:** Drafted responses must directly answer the user's question or solve their pain point. No unsolicited brand plugs, no astroturfing, and no robotic sales copy.
3. **Traceability:** Every opportunity must anchor on a verbatim quote extracted directly from the original conversation.

---

## Multi-Agent Architecture

```
                   [Public Community Ingestion]
                                │
                                ▼
                         [Analyst Agent]
           (Extracts problem, intent, & evidence quote)
                                │
                                ▼
                        [Strategist Agent]
          (Calculates Opportunity Score & Fit / Risk)
                                │
            ┌───────────────────┴───────────────────┐
  [Score < 40 or "do_not_engage"]        [Score >= 40 & "engage"]
            │                                       │
            ▼                                       ▼
         [DROP]                              [Drafting Agent]
                                        (Context-first response)
                                                    │
                                                    ▼
                                         [Compliance Critic]
                                       (Validates policy/claims)
                                                    │
                                ┌───────────────────┴───────────────────┐
                             [FAILED]                                [PASSED]
                      (Re-draft loop, max 2)                            │
                                │                                       ▼
                                └──────────────────────────────► [Human Review Node]
                                                              (LangGraph interrupt())
                                                                        │
                                                                        ▼
                                                              [Marketer Dashboard]
                                                            (Approve / Edit / Reject)
```

---

## Quickstart Guide

### 1. Backend (FastAPI + LangGraph Swarm)

```powershell
# Navigate to backend and activate virtual environment
cd backend
..\.venv\Scripts\Activate.ps1

# (Optional) Provide API credentials in backend/.env
# Copy template if you haven't already:
cp .env.example .env

# Run FastAPI server with Uvicorn
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

* API Docs available at: [http://localhost:8000/docs](http://localhost:8000/docs)
* Health check: [http://localhost:8000/api/health](http://localhost:8000/api/health)
* Pending opportunities: [http://localhost:8000/api/opportunities/pending](http://localhost:8000/api/opportunities/pending)

### 2. Frontend (Next.js Marketer Review Desk)

```powershell
# In a new terminal, navigate to frontend
cd frontend

# Run development server
npm run dev
```

* Open [http://localhost:3000](http://localhost:3000) to access the Marketer Review Desk.

---

## Running the Automated Test Suite

To run all 19 automated unit and integration tests across the multi-agent pipeline:

```powershell
.venv\Scripts\pytest.exe backend\tests\ -v
```

---

## Repository Structure

```
dark-social-swarm/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes.py            # FastAPI REST & WebSocket endpoints
│   │   │   └── dependencies.py      # Dependency injection & checkpointer
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic environment configuration
│   │   │   └── database.py          # SQLite WAL-mode opportunity lifecycle storage
│   │   ├── ingestion/
│   │   │   ├── listener.py          # PRAW Reddit ingestion stream daemon & fallback queue
│   │   │   └── normalizer.py        # Cleans and packages posts into standard events
│   │   ├── swarm/
│   │   │   ├── state.py             # SwarmState TypedDict & Pydantic models
│   │   │   ├── graph.py             # LangGraph StateGraph assembly & conditional routing
│   │   │   ├── agents/
│   │   │   │   ├── analyst.py       # Analyst Node (Scout persona)
│   │   │   │   ├── strategist.py    # Strategist Node (Opportunity Scoring)
│   │   │   │   ├── drafter.py       # Drafting Node (Relay persona)
│   │   │   │   ├── critic.py        # Compliance Critic Node (Guardrails validation)
│   │   │   │   └── human_review.py  # Interruption node with interrupt()
│   │   │   └── prompts/             # Modular system & task prompts
│   │   └── main.py                  # ASGI server startup & background task runner
│   ├── tests/
│   │   ├── test_phase1.py           # State and schema unit tests
│   │   ├── test_phase2_ingestion_storage.py  # Queue and SQLite WAL tests
│   │   ├── test_graph_flow.py       # StateGraph conditional routing & interrupt() tests
│   │   ├── test_api_routes.py       # FastAPI REST & resume tests
│   │   └── test_swarm_state_serialization.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/                        # Next.js / Tailwind Marketer Review Desk
│   ├── components/
│   │   ├── OpportunityCard.tsx      # Displays quote, score, intent, draft, & critic status
│   │   ├── ActionPanel.tsx          # Approve, Edit, Reject resume dispatchers
│   │   ├── LiveStreamFeed.tsx       # Incoming ingested post stream & simulation triggers
│   │   └── Navbar.tsx               # System status pills & queue counter
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                 # Main Review Desk Dashboard
│   │   └── globals.css
│   └── package.json
└── README.md
```
