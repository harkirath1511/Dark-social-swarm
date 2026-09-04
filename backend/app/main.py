"""
Dark Social Swarm - FastAPI Main Application & Background Daemon Lifecycle.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db, get_opportunity
from app.api.routes import router, ws_manager
from app.api.dependencies import get_graph
from app.ingestion.listener import RedditListener
from app.ingestion.normalizer import RedditPostEvent
from app.swarm.state import SwarmState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("dark_social_swarm.main")

# Ingestion Queue
ingestion_queue: asyncio.Queue[RedditPostEvent] = asyncio.Queue()
reddit_daemon = RedditListener(ingestion_queue)


async def queue_consumer_worker():
    """
    Background worker that pulls normalized posts from the ingestion queue
    and triggers the LangGraph Multi-Agent Swarm for each candidate.
    """
    logger.info("Background Swarm Queue Consumer started.")
    graph = get_graph()

    while True:
        try:
            event: RedditPostEvent = await ingestion_queue.get()
            logger.info(f"Processing candidate post {event.thread_id} through Swarm...")

            initial_state: SwarmState = {
                "platform": "reddit",
                "thread_id": event.thread_id,
                "subreddit": event.subreddit,
                "title": event.title,
                "body": event.body,
                "author": event.author,
                "permalink": event.permalink,
            }

            config = {"configurable": {"thread_id": event.thread_id}}

            # Run graph until interrupt or END
            try:
                await graph.ainvoke(initial_state, config=config)
            except Exception as e:
                logger.error(f"Error processing thread {event.thread_id} in graph: {e}")

            # Fetch updated lead from DB and broadcast via WebSocket
            updated = await get_opportunity(event.thread_id)
            if updated:
                await ws_manager.broadcast({
                    "type": "POST_PROCESSED",
                    "data": updated,
                })

            ingestion_queue.task_done()

        except asyncio.CancelledError:
            logger.info("Queue consumer worker cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in queue consumer: {e}")
            await asyncio.sleep(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and shutdown procedures."""
    logger.info("Starting Dark Social Swarm server...")
    # 1. Initialize SQLite Database with WAL mode
    await init_db()
    logger.info("Database initialized with WAL mode.")

    # 2. Start Ingestion Stream Daemon & Queue Worker
    reddit_daemon.start()
    consumer_task = asyncio.create_task(queue_consumer_worker())

    yield

    # Shutdown
    logger.info("Shutting down Dark Social Swarm server...")
    consumer_task.cancel()
    await reddit_daemon.stop()


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-driven conversation intelligence and opportunity triage system with strict human-in-the-loop controls.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Router
app.include_router(router)


@app.get("/")
async def root():
    return {
        "message": "Welcome to Dark Social Swarm API",
        "docs_url": "/docs",
        "endpoints": {
            "pending": "/api/opportunities/pending",
            "resume": "/api/opportunities/{thread_id}/resume",
            "simulate": "/api/ingest/simulate",
            "websocket": "/api/ws/stream",
        },
    }
