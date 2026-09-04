"""
FastAPI REST & WebSocket Endpoints for Dark Social Swarm.
Adapted from KirtiJha/langgraph-interrupt-workflow-template:
- GET /api/feed: Paginated list of all ingested posts and their processing statuses
- GET /api/review-queue: List of threads currently paused in human_review interrupt state
- POST /api/review/{thread_id}/submit: Submits marketer decision and resumes graph execution
- POST /api/ingest/simulate: Runs a thread through the Swarm multi-agent graph
"""

import logging
from typing import List, Dict, Any, Optional, Literal
from fastapi import APIRouter, HTTPException, Depends, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from langgraph.types import Command

from app.core.database import (
    get_pending_opportunities,
    get_all_opportunities,
    count_opportunities,
    get_opportunity,
    save_raw_post,
    record_human_triage,
)
from app.swarm.state import SwarmState
from app.api.dependencies import get_graph

logger = logging.getLogger("dark_social_swarm.api")
router = APIRouter(prefix="/api")


# In-memory connected WebSocket clients
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)


ws_manager = ConnectionManager()


# -------------------------------------------------------------
# Request Schemas
# -------------------------------------------------------------

class ReviewSubmitRequest(BaseModel):
    action: Literal["approved", "edited", "rejected"] = Field(
        ...,
        description="Marketer review action"
    )
    edited_text: Optional[str] = Field(
        default=None,
        description="Edited draft response text when action is 'edited'"
    )


class SimulateIngestRequest(BaseModel):
    title: str = Field(..., description="Post title")
    body: str = Field(default="", description="Post self-text body")
    subreddit: str = Field(default="r/SaaS", description="Subreddit")
    author: str = Field(default="community_member", description="Author username")


# -------------------------------------------------------------
# Core Endpoints
# -------------------------------------------------------------

@router.get("/health")
async def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "system": "Dark Social Swarm",
        "pipeline": "Analyst -> Strategist -> Drafter -> Critic -> HumanReview",
    }


@router.get("/feed")
async def get_feed(
    limit: int = Query(default=50, ge=1, le=100, description="Page limit"),
    offset: int = Query(default=0, ge=0, description="Page offset"),
):
    """
    Paginated list of all ingested posts and their processing statuses.
    """
    total = await count_opportunities()
    items = await get_all_opportunities(limit=limit, offset=offset)
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items,
    }


@router.get("/review-queue")
async def get_review_queue():
    """
    List of threads currently paused in the human_review interrupt state.
    """
    queue = await get_pending_opportunities()
    return {
        "count": len(queue),
        "queue": queue,
    }


@router.post("/review/{thread_id}/submit")
async def submit_review(
    thread_id: str,
    payload: ReviewSubmitRequest,
    graph=Depends(get_graph),
):
    """
    Accepts marketer decision ({ action: 'approved' | 'edited' | 'rejected', edited_text: '...' })
    and invokes Command(resume=...) on the active LangGraph checkpointer to complete the cycle.
    """
    logger.info(f"Submitting review for thread {thread_id}: action={payload.action}")

    existing = await get_opportunity(thread_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found.")

    config = {"configurable": {"thread_id": thread_id}}
    final_text = payload.edited_text or existing.get("proposed_draft", "")

    try:
        # Check if the graph is currently paused at human_review for this thread
        state_snapshot = await graph.aget_state(config)

        if not state_snapshot.next and existing.get("status") in ("APPROVED", "EDITED", "REJECTED"):
            return {
                "status": "already_resolved",
                "thread_id": thread_id,
                "opportunity": existing,
            }

        # Issue resume command to LangGraph
        resume_cmd = Command(resume={
            "action": payload.action,
            "final_response_text": final_text,
        })

        resumed_output = await graph.ainvoke(resume_cmd, config=config)

        # Retrieve updated record
        updated = await get_opportunity(thread_id)

        # Broadcast update to connected WebSockets
        if updated:
            await ws_manager.broadcast({
                "type": "OPPORTUNITY_RESOLVED",
                "data": updated,
            })

        return {
            "status": "resumed",
            "thread_id": thread_id,
            "human_status": payload.action,
            "final_response_text": final_text,
            "opportunity": updated,
        }

    except Exception as e:
        logger.error(f"Error resuming graph for {thread_id}: {e}")
        # Database fallback to guarantee state durability
        updated = await record_human_triage(
            thread_id=thread_id,
            human_status=payload.action,
            final_response_text=final_text,
        )
        return {
            "status": "resumed_fallback",
            "thread_id": thread_id,
            "human_status": payload.action,
            "final_response_text": final_text,
            "opportunity": updated,
        }


# -------------------------------------------------------------
# Backward-Compatible Aliases & Additional Utilities
# -------------------------------------------------------------

@router.get("/opportunities/pending")
async def list_pending_opportunities():
    """Alias for /api/review-queue."""
    opportunities = await get_pending_opportunities()
    return {
        "count": len(opportunities),
        "opportunities": opportunities,
    }


@router.get("/opportunities")
async def list_all_opportunities(limit: int = 50):
    """Alias for /api/feed."""
    opportunities = await get_all_opportunities(limit=limit)
    return {
        "count": len(opportunities),
        "opportunities": opportunities,
    }


@router.post("/opportunities/{thread_id}/resume")
async def resume_opportunity_alias(
    thread_id: str,
    payload: ReviewSubmitRequest,
    graph=Depends(get_graph),
):
    """Alias for /api/review/{thread_id}/submit."""
    return await submit_review(thread_id=thread_id, payload=payload, graph=graph)


@router.post("/ingest/simulate")
async def simulate_ingest_thread(
    req: SimulateIngestRequest,
    graph=Depends(get_graph),
):
    """
    Simulates ingesting a raw community discussion and executing it through the swarm.
    If the opportunity qualifies, execution pauses at human_review_node.
    """
    import uuid, time
    thread_id = f"t3_sim_{uuid.uuid4().hex[:8]}"
    sub = req.subreddit if req.subreddit.startswith("r/") else f"r/{req.subreddit}"

    # 1. Save raw post in SQLite
    saved = await save_raw_post(
        thread_id=thread_id,
        subreddit=sub,
        title=req.title,
        body=req.body,
        author=req.author,
        permalink=f"https://reddit.com/{sub}/comments/{thread_id}",
        created_utc=time.time(),
    )

    # 2. Run through Multi-Agent LangGraph Swarm
    initial_state: SwarmState = {
        "platform": "reddit",
        "thread_id": thread_id,
        "subreddit": sub,
        "title": req.title,
        "body": req.body,
        "author": req.author,
        "permalink": f"https://reddit.com/{sub}/comments/{thread_id}",
    }

    config = {"configurable": {"thread_id": thread_id}}

    try:
        # Run graph until interrupt or END
        await graph.ainvoke(initial_state, config=config)
    except Exception as e:
        logger.error(f"Error during graph execution for {thread_id}: {e}")

    # 3. Retrieve final or paused record
    processed = await get_opportunity(thread_id)

    # Broadcast to WebSockets
    if processed:
        await ws_manager.broadcast({
            "type": "NEW_OPPORTUNITY_INGESTED",
            "data": processed,
        })

    return {
        "thread_id": thread_id,
        "opportunity": processed,
    }


@router.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """WebSocket endpoint broadcasting real-time ingestion & triage updates."""
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
