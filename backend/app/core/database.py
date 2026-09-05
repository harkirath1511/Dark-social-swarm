"""
SQLite Lead & Opportunity Lifecycle Storage.
Configured with Write-Ahead Logging (WAL) for concurrent async operations.
Tracks opportunities across: DISCOVERED -> PROCESSING -> AWAITING_APPROVAL -> APPROVED / EDITED / REJECTED / DISCARDED.
Includes Delta Upgrade columns for multi-quote evidence, 6D scoring, brand flags, and structured rejection.
"""

import json
import aiosqlite
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from app.core.config import settings


CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS opportunities (
    platform TEXT NOT NULL DEFAULT 'reddit',
    thread_id TEXT PRIMARY KEY,
    community_id TEXT DEFAULT NULL,
    subreddit TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT,
    author TEXT,
    permalink TEXT,
    created_utc REAL,
    status TEXT NOT NULL DEFAULT 'DISCOVERED',
    discovery_score REAL DEFAULT 0.0,
    discovery_passed INTEGER DEFAULT 1,
    extracted_problem TEXT DEFAULT NULL,
    pain_point TEXT DEFAULT NULL,
    conversation_context TEXT DEFAULT NULL,
    community_context TEXT DEFAULT NULL,
    user_goal TEXT DEFAULT NULL,
    user_intent TEXT DEFAULT NULL,
    sentiment TEXT DEFAULT NULL,
    entities TEXT DEFAULT '[]',
    brand_mentioned INTEGER DEFAULT 0,
    competitor_mentioned INTEGER DEFAULT 0,
    mentioned_brands TEXT DEFAULT '[]',
    mentioned_competitors TEXT DEFAULT '[]',
    evidence_quote TEXT DEFAULT NULL,
    evidence TEXT DEFAULT '[]',
    analyst_confidence REAL DEFAULT 0.8,
    relevance_score INTEGER DEFAULT 0,
    intent_strength_score INTEGER DEFAULT 0,
    community_fit_score INTEGER DEFAULT 0,
    credibility_score INTEGER DEFAULT 0,
    engagement_risk_score INTEGER DEFAULT 0,
    opportunity_score INTEGER DEFAULT NULL,
    strategist_confidence REAL DEFAULT 0.8,
    engagement_decision TEXT DEFAULT NULL,
    strategic_reasoning TEXT DEFAULT NULL,
    sensitive_topic INTEGER DEFAULT 0,
    sensitive_topic_reason TEXT DEFAULT NULL,
    proposed_draft TEXT DEFAULT NULL,
    draft_iteration INTEGER DEFAULT 0,
    critic_passed INTEGER DEFAULT NULL,
    violation_category TEXT DEFAULT NULL,
    critic_feedback TEXT DEFAULT NULL,
    human_status TEXT DEFAULT NULL,
    rejection_reason TEXT DEFAULT NULL,
    final_response_text TEXT DEFAULT NULL,
    discovered_at TIMESTAMP DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TIMESTAMP DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_opportunities_status ON opportunities(status);
CREATE INDEX IF NOT EXISTS idx_opportunities_created ON opportunities(created_utc);
CREATE INDEX IF NOT EXISTS idx_opportunities_score ON opportunities(opportunity_score);
"""


@asynccontextmanager
async def get_db():
    """Async context manager connection with WAL mode enabled."""
    async with aiosqlite.connect(settings.SQLITE_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA journal_mode = WAL;")
        await db.execute("PRAGMA synchronous = NORMAL;")
        yield db


async def init_db() -> None:
    """Initialize database schema and ensure WAL mode is active."""
    async with get_db() as db:
        await db.executescript(CREATE_TABLES_SQL)
        # Lightweight schema migration for existing sqlite databases
        cursor = await db.execute("PRAGMA table_info(opportunities);")
        columns = [row["name"] for row in await cursor.fetchall()]
        migrations = [
            ("platform", "ALTER TABLE opportunities ADD COLUMN platform TEXT NOT NULL DEFAULT 'reddit';"),
            ("community_id", "ALTER TABLE opportunities ADD COLUMN community_id TEXT DEFAULT NULL;"),
            ("discovery_score", "ALTER TABLE opportunities ADD COLUMN discovery_score REAL DEFAULT 0.0;"),
            ("discovery_passed", "ALTER TABLE opportunities ADD COLUMN discovery_passed INTEGER DEFAULT 1;"),
            ("extracted_problem", "ALTER TABLE opportunities ADD COLUMN extracted_problem TEXT DEFAULT NULL;"),
            ("pain_point", "ALTER TABLE opportunities ADD COLUMN pain_point TEXT DEFAULT NULL;"),
            ("conversation_context", "ALTER TABLE opportunities ADD COLUMN conversation_context TEXT DEFAULT NULL;"),
            ("community_context", "ALTER TABLE opportunities ADD COLUMN community_context TEXT DEFAULT NULL;"),
            ("user_goal", "ALTER TABLE opportunities ADD COLUMN user_goal TEXT DEFAULT NULL;"),
            ("user_intent", "ALTER TABLE opportunities ADD COLUMN user_intent TEXT DEFAULT NULL;"),
            ("sentiment", "ALTER TABLE opportunities ADD COLUMN sentiment TEXT DEFAULT NULL;"),
            ("entities", "ALTER TABLE opportunities ADD COLUMN entities TEXT DEFAULT '[]';"),
            ("brand_mentioned", "ALTER TABLE opportunities ADD COLUMN brand_mentioned INTEGER DEFAULT 0;"),
            ("competitor_mentioned", "ALTER TABLE opportunities ADD COLUMN competitor_mentioned INTEGER DEFAULT 0;"),
            ("mentioned_brands", "ALTER TABLE opportunities ADD COLUMN mentioned_brands TEXT DEFAULT '[]';"),
            ("mentioned_competitors", "ALTER TABLE opportunities ADD COLUMN mentioned_competitors TEXT DEFAULT '[]';"),
            ("evidence_quote", "ALTER TABLE opportunities ADD COLUMN evidence_quote TEXT DEFAULT NULL;"),
            ("evidence", "ALTER TABLE opportunities ADD COLUMN evidence TEXT DEFAULT '[]';"),
            ("analyst_confidence", "ALTER TABLE opportunities ADD COLUMN analyst_confidence REAL DEFAULT 0.8;"),
            ("relevance_score", "ALTER TABLE opportunities ADD COLUMN relevance_score INTEGER DEFAULT 0;"),
            ("intent_strength_score", "ALTER TABLE opportunities ADD COLUMN intent_strength_score INTEGER DEFAULT 0;"),
            ("community_fit_score", "ALTER TABLE opportunities ADD COLUMN community_fit_score INTEGER DEFAULT 0;"),
            ("credibility_score", "ALTER TABLE opportunities ADD COLUMN credibility_score INTEGER DEFAULT 0;"),
            ("engagement_risk_score", "ALTER TABLE opportunities ADD COLUMN engagement_risk_score INTEGER DEFAULT 0;"),
            ("strategist_confidence", "ALTER TABLE opportunities ADD COLUMN strategist_confidence REAL DEFAULT 0.8;"),
            ("engagement_decision", "ALTER TABLE opportunities ADD COLUMN engagement_decision TEXT DEFAULT NULL;"),
            ("strategic_reasoning", "ALTER TABLE opportunities ADD COLUMN strategic_reasoning TEXT DEFAULT NULL;"),
            ("sensitive_topic", "ALTER TABLE opportunities ADD COLUMN sensitive_topic INTEGER DEFAULT 0;"),
            ("sensitive_topic_reason", "ALTER TABLE opportunities ADD COLUMN sensitive_topic_reason TEXT DEFAULT NULL;"),
            ("proposed_draft", "ALTER TABLE opportunities ADD COLUMN proposed_draft TEXT DEFAULT NULL;"),
            ("draft_iteration", "ALTER TABLE opportunities ADD COLUMN draft_iteration INTEGER DEFAULT 0;"),
            ("critic_passed", "ALTER TABLE opportunities ADD COLUMN critic_passed INTEGER DEFAULT NULL;"),
            ("violation_category", "ALTER TABLE opportunities ADD COLUMN violation_category TEXT DEFAULT NULL;"),
            ("critic_feedback", "ALTER TABLE opportunities ADD COLUMN critic_feedback TEXT DEFAULT NULL;"),
            ("human_status", "ALTER TABLE opportunities ADD COLUMN human_status TEXT DEFAULT NULL;"),
            ("rejection_reason", "ALTER TABLE opportunities ADD COLUMN rejection_reason TEXT DEFAULT NULL;"),
            ("final_response_text", "ALTER TABLE opportunities ADD COLUMN final_response_text TEXT DEFAULT NULL;"),
        ]
        for col_name, alter_stmt in migrations:
            if col_name not in columns:
                await db.execute(alter_stmt)
        await db.commit()


async def save_raw_post(
    thread_id: str,
    subreddit: str,
    title: str,
    body: str,
    author: str,
    permalink: str,
    created_utc: float,
    platform: str = "reddit",
    community_id: Optional[str] = None,
    discovery_score: float = 0.0,
    discovery_passed: bool = True,
) -> Dict[str, Any]:
    """Persist newly discovered post into SQLite with status DISCOVERED."""
    comm_id = community_id or subreddit
    query = """
    INSERT INTO opportunities (
        platform, thread_id, community_id, subreddit, title, body, author, permalink, created_utc,
        discovery_score, discovery_passed, status, discovered_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'DISCOVERED', strftime('%Y-%m-%dT%H:%M:%SZ', 'now'), strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
    ON CONFLICT(thread_id) DO UPDATE SET
        status = 'DISCOVERED',
        updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
    RETURNING *;
    """
    async with get_db() as db:
        cursor = await db.execute(
            query, (
                platform, thread_id, comm_id, subreddit, title, body, author, permalink, created_utc,
                discovery_score, 1 if discovery_passed else 0
            )
        )
        row = await cursor.fetchone()
        await db.commit()
        return dict(row) if row else {}


async def update_opportunity_status(thread_id: str, status: str) -> None:
    """Update lifecycle status of an opportunity."""
    query = """
    UPDATE opportunities
    SET status = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
    WHERE thread_id = ?;
    """
    async with get_db() as db:
        await db.execute(query, (status, thread_id))
        await db.commit()


async def update_analyst_signals(
    thread_id: str,
    extracted_problem: str,
    user_intent: str,
    evidence_quote: str,
    pain_point: Optional[str] = None,
    conversation_context: Optional[str] = None,
    community_context: Optional[str] = None,
    user_goal: Optional[str] = None,
    sentiment: Optional[str] = None,
    entities: Optional[List[str]] = None,
    brand_mentioned: bool = False,
    competitor_mentioned: bool = False,
    mentioned_brands: Optional[List[str]] = None,
    mentioned_competitors: Optional[List[str]] = None,
    evidence: Optional[List[str]] = None,
    analyst_confidence: float = 0.85,
) -> None:
    """Store rich intelligence findings from Analyst Node."""
    entities_json = json.dumps(entities or [])
    brands_json = json.dumps(mentioned_brands or [])
    competitors_json = json.dumps(mentioned_competitors or [])
    evidence_json = json.dumps(evidence or [evidence_quote])

    query = """
    UPDATE opportunities
    SET extracted_problem = ?, user_intent = ?, evidence_quote = ?,
        pain_point = ?, conversation_context = ?, community_context = ?,
        user_goal = ?, sentiment = ?, entities = ?,
        brand_mentioned = ?, competitor_mentioned = ?,
        mentioned_brands = ?, mentioned_competitors = ?,
        evidence = ?, analyst_confidence = ?,
        status = 'PROCESSING', updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
    WHERE thread_id = ?;
    """
    async with get_db() as db:
        await db.execute(
            query,
            (
                extracted_problem, user_intent, evidence_quote,
                pain_point, conversation_context, community_context,
                user_goal, sentiment, entities_json,
                1 if brand_mentioned else 0, 1 if competitor_mentioned else 0,
                brands_json, competitors_json,
                evidence_json, analyst_confidence,
                thread_id
            ),
        )
        await db.commit()


async def update_strategist_decision(
    thread_id: str,
    opportunity_score: int,
    engagement_decision: str,
    strategic_reasoning: str,
    status: str,
    relevance_score: int = 0,
    intent_strength_score: int = 0,
    community_fit_score: int = 0,
    credibility_score: int = 0,
    engagement_risk_score: int = 0,
    strategist_confidence: float = 0.85,
) -> None:
    """Store 6D evaluation findings from Strategist Node."""
    query = """
    UPDATE opportunities
    SET opportunity_score = ?, engagement_decision = ?, strategic_reasoning = ?,
        relevance_score = ?, intent_strength_score = ?, community_fit_score = ?,
        credibility_score = ?, engagement_risk_score = ?, strategist_confidence = ?,
        status = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
    WHERE thread_id = ?;
    """
    async with get_db() as db:
        await db.execute(
            query,
            (
                opportunity_score, engagement_decision, strategic_reasoning,
                relevance_score, intent_strength_score, community_fit_score,
                credibility_score, engagement_risk_score, strategist_confidence,
                status, thread_id
            ),
        )
        await db.commit()


async def update_sensitive_topic(
    thread_id: str,
    sensitive_topic: bool,
    sensitive_topic_reason: Optional[str] = None,
    status: str = "AWAITING_APPROVAL",
) -> None:
    """Flag opportunity as sensitive topic bypassing automated drafting."""
    query = """
    UPDATE opportunities
    SET sensitive_topic = ?, sensitive_topic_reason = ?, status = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
    WHERE thread_id = ?;
    """
    async with get_db() as db:
        await db.execute(query, (1 if sensitive_topic else 0, sensitive_topic_reason, status, thread_id))
        await db.commit()


async def update_draft_and_critic(
    thread_id: str,
    proposed_draft: str,
    draft_iteration: int,
    critic_passed: bool,
    violation_category: Optional[str] = None,
    critic_feedback: Optional[str] = None,
    status: str = "AWAITING_APPROVAL",
) -> None:
    """Store generated draft and critic validation results."""
    query = """
    UPDATE opportunities
    SET proposed_draft = ?, draft_iteration = ?, critic_passed = ?, violation_category = ?, critic_feedback = ?, status = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
    WHERE thread_id = ?;
    """
    async with get_db() as db:
        await db.execute(
            query,
            (
                proposed_draft,
                draft_iteration,
                1 if critic_passed else 0,
                violation_category,
                critic_feedback,
                status,
                thread_id,
            ),
        )
        await db.commit()


async def record_human_triage(
    thread_id: str,
    human_status: str,
    final_response_text: Optional[str] = None,
    rejection_reason: Optional[str] = None,
) -> Dict[str, Any]:
    """Records human review decision: approved, edited, or rejected with structured calibration reason."""
    lifecycle_status = human_status.upper()
    query = """
    INSERT INTO opportunities (
        thread_id, platform, community_id, subreddit, title, status, human_status, final_response_text, rejection_reason, updated_at
    ) VALUES (?, 'reddit', 'r/general', 'r/general', 'Community Discussion', ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
    ON CONFLICT(thread_id) DO UPDATE SET
        human_status = excluded.human_status,
        final_response_text = excluded.final_response_text,
        rejection_reason = excluded.rejection_reason,
        status = excluded.status,
        updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
    RETURNING *;
    """
    async with get_db() as db:
        cursor = await db.execute(query, (thread_id, lifecycle_status, human_status, final_response_text, rejection_reason))
        row = await cursor.fetchone()
        await db.commit()
        return dict(row) if row else {}


async def get_opportunity(thread_id: str) -> Optional[Dict[str, Any]]:
    """Fetch single opportunity by thread ID."""
    query = "SELECT * FROM opportunities WHERE thread_id = ?;"
    async with get_db() as db:
        cursor = await db.execute(query, (thread_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_pending_opportunities() -> List[Dict[str, Any]]:
    """Retrieve opportunities waiting at the Human Review Node."""
    query = """
    SELECT * FROM opportunities 
    WHERE status = 'AWAITING_APPROVAL' 
    ORDER BY opportunity_score DESC, updated_at DESC;
    """
    async with get_db() as db:
        cursor = await db.execute(query)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def count_opportunities() -> int:
    """Return total count of all ingested posts."""
    query = "SELECT COUNT(*) as count FROM opportunities;"
    async with get_db() as db:
        cursor = await db.execute(query)
        row = await cursor.fetchone()
        return row["count"] if row else 0


async def get_all_opportunities(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """List opportunities ordered by most recent update with pagination."""
    query = "SELECT * FROM opportunities ORDER BY updated_at DESC LIMIT ? OFFSET ?;"
    async with get_db() as db:
        cursor = await db.execute(query, (limit, offset))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
