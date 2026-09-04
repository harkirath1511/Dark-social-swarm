"""
SQLite Lead & Opportunity Lifecycle Storage.
Configured with Write-Ahead Logging (WAL) for concurrent async operations.
Tracks opportunities across: DISCOVERED -> PROCESSING -> AWAITING_APPROVAL -> APPROVED / EDITED / REJECTED / DISCARDED.
"""

import aiosqlite
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from app.core.config import settings


CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS opportunities (
    platform TEXT NOT NULL DEFAULT 'reddit',
    thread_id TEXT PRIMARY KEY,
    subreddit TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT,
    author TEXT,
    permalink TEXT,
    created_utc REAL,
    status TEXT NOT NULL DEFAULT 'DISCOVERED',
    extracted_problem TEXT DEFAULT NULL,
    user_intent TEXT DEFAULT NULL,
    evidence_quote TEXT DEFAULT NULL,
    opportunity_score INTEGER DEFAULT NULL,
    engagement_decision TEXT DEFAULT NULL,
    strategic_reasoning TEXT DEFAULT NULL,
    proposed_draft TEXT DEFAULT NULL,
    draft_iteration INTEGER DEFAULT 0,
    critic_passed INTEGER DEFAULT NULL,
    violation_category TEXT DEFAULT NULL,
    critic_feedback TEXT DEFAULT NULL,
    human_status TEXT DEFAULT NULL,
    final_response_text TEXT DEFAULT NULL,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            ("extracted_problem", "ALTER TABLE opportunities ADD COLUMN extracted_problem TEXT DEFAULT NULL;"),
            ("user_intent", "ALTER TABLE opportunities ADD COLUMN user_intent TEXT DEFAULT NULL;"),
            ("engagement_decision", "ALTER TABLE opportunities ADD COLUMN engagement_decision TEXT DEFAULT NULL;"),
            ("proposed_draft", "ALTER TABLE opportunities ADD COLUMN proposed_draft TEXT DEFAULT NULL;"),
            ("draft_iteration", "ALTER TABLE opportunities ADD COLUMN draft_iteration INTEGER DEFAULT 0;"),
            ("human_status", "ALTER TABLE opportunities ADD COLUMN human_status TEXT DEFAULT NULL;"),
            ("final_response_text", "ALTER TABLE opportunities ADD COLUMN final_response_text TEXT DEFAULT NULL;"),
            ("violation_category", "ALTER TABLE opportunities ADD COLUMN violation_category TEXT DEFAULT NULL;"),
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
) -> Dict[str, Any]:
    """Persist newly discovered post into SQLite with status DISCOVERED."""
    query = """
    INSERT INTO opportunities (
        platform, thread_id, subreddit, title, body, author, permalink, created_utc, status, discovered_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'DISCOVERED', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    ON CONFLICT(thread_id) DO UPDATE SET
        updated_at = CURRENT_TIMESTAMP
    RETURNING *;
    """
    async with get_db() as db:
        cursor = await db.execute(
            query, (platform, thread_id, subreddit, title, body, author, permalink, created_utc)
        )
        row = await cursor.fetchone()
        await db.commit()
        return dict(row) if row else {}


async def update_opportunity_status(thread_id: str, status: str) -> None:
    """Update lifecycle status of an opportunity."""
    query = """
    UPDATE opportunities
    SET status = ?, updated_at = CURRENT_TIMESTAMP
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
) -> None:
    """Store findings from Analyst Node (Scout persona)."""
    query = """
    UPDATE opportunities
    SET extracted_problem = ?, user_intent = ?, evidence_quote = ?, status = 'PROCESSING', updated_at = CURRENT_TIMESTAMP
    WHERE thread_id = ?;
    """
    async with get_db() as db:
        await db.execute(query, (extracted_problem, user_intent, evidence_quote, thread_id))
        await db.commit()


async def update_strategist_decision(
    thread_id: str,
    opportunity_score: int,
    engagement_decision: str,
    strategic_reasoning: str,
    status: str,
) -> None:
    """Store findings from Strategist Node."""
    query = """
    UPDATE opportunities
    SET opportunity_score = ?, engagement_decision = ?, strategic_reasoning = ?, status = ?, updated_at = CURRENT_TIMESTAMP
    WHERE thread_id = ?;
    """
    async with get_db() as db:
        await db.execute(query, (opportunity_score, engagement_decision, strategic_reasoning, status, thread_id))
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
    SET proposed_draft = ?, draft_iteration = ?, critic_passed = ?, violation_category = ?, critic_feedback = ?, status = ?, updated_at = CURRENT_TIMESTAMP
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
) -> Dict[str, Any]:
    """Records human review decision: approved, edited, or rejected."""
    lifecycle_status = human_status.upper()
    query = """
    UPDATE opportunities
    SET human_status = ?, final_response_text = ?, status = ?, updated_at = CURRENT_TIMESTAMP
    WHERE thread_id = ?
    RETURNING *;
    """
    async with get_db() as db:
        cursor = await db.execute(query, (human_status, final_response_text, lifecycle_status, thread_id))
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
