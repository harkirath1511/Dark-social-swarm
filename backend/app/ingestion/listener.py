"""
Reddit Ingestion Stream Daemon.
Adapted from ivucicev/redsignal:
- Streams submissions from target subreddits using PRAW
- Stripped of legacy single-prompt LLM filter
- Directly feeds normalized posts into an asyncio.Queue
- Includes fallback synthetic stream for local testing without API keys
"""

import asyncio
import logging
import time
from typing import Optional, AsyncGenerator
import praw

from app.core.config import settings
from app.ingestion.normalizer import RedditPostEvent, normalize_submission, is_valid_candidate
from app.core.database import save_raw_post

logger = logging.getLogger("dark_social_swarm.ingestion")

# Sample realistic dark-social mock posts for deterministic dev/testing
SYNTHETIC_POSTS = [
    {
        "id": "1h9k2z8",
        "subreddit": "r/SaaS",
        "title": "I've tried three tools for turning long videos into clips. Which one actually works?",
        "selftext": "Most automated tools cut off sentences right in the middle or pick arbitrary highlights that don't make sense without context. Does anyone have a workflow or tool that actually respects semantic boundaries?",
        "author": "creator_dan99",
        "permalink": "/r/SaaS/comments/1h9k2z8",
        "created_utc": time.time() - 300,
    },
    {
        "id": "1h9m7q1",
        "subreddit": "r/startups",
        "title": "Our sales team hates updating HubSpot. Are people actually using AI SDRs or lightweight CRMs?",
        "selftext": "Manual CRM hygiene is killing our rep productivity. We lose tracking on half our dark social touchpoints and Slack DMs. What is the leanest way teams are tracking deals without requiring 20 form fields per call?",
        "author": "saas_founder_alex",
        "permalink": "/r/startups/comments/1h9m7q1",
        "created_utc": time.time() - 600,
    },
    {
        "id": "1h9x3p4",
        "subreddit": "r/Entrepreneur",
        "title": "How do you monitor organic discussions without looking like a spam bot?",
        "selftext": "Every time we try social listening, the alerts are 90% spam or our team writes answers that get downvoted for self-promotion. How are successful founders actually participating in niche communities?",
        "author": "bootstrapped_mike",
        "permalink": "/r/Entrepreneur/comments/1h9x3p4",
        "created_utc": time.time() - 1200,
    },
    {
        "id": "1h9low2",
        "subreddit": "r/smallbusiness",
        "title": "Check out our brand new SEO discount code 50% OFF",
        "selftext": "Click this link now for 50% off guaranteed backlink building at spamlink.com",
        "author": "seo_spammer_101",
        "permalink": "/r/smallbusiness/comments/1h9low2",
        "created_utc": time.time() - 1800,
    },
]


class RedditListener:
    """Daemon that streams submissions from Reddit and pushes to asyncio queue."""

    def __init__(self, queue: asyncio.Queue[RedditPostEvent]):
        self.queue = queue
        self._running = False
        self._task: Optional[asyncio.Task] = None

    def _init_praw(self) -> Optional[praw.Reddit]:
        """Initialize PRAW client if credentials exist."""
        if not settings.has_reddit_creds:
            logger.info("Reddit credentials missing or placeholder. Running in synthetic mock stream mode.")
            return None

        try:
            reddit = praw.Reddit(
                client_id=settings.REDDIT_CLIENT_ID,
                client_secret=settings.REDDIT_CLIENT_SECRET,
                user_agent=settings.REDDIT_USER_AGENT,
                read_only=True,
            )
            # Test authentication
            _ = reddit.user.me()
            logger.info("PRAW Reddit authenticated successfully in read-only mode.")
            return reddit
        except Exception as e:
            logger.warning(f"Failed to initialize live PRAW client: {e}. Falling back to synthetic mode.")
            return None

    async def _mock_stream(self) -> AsyncGenerator[RedditPostEvent, None]:
        """Yields realistic test opportunities for local dev & evaluation."""
        logger.info("Starting synthetic dark-social ingestion stream...")
        # First push the initial batch
        for raw in SYNTHETIC_POSTS:
            event = normalize_submission(raw)
            if is_valid_candidate(event):
                yield event
            await asyncio.sleep(0.5)

        # Then periodically wait to simulate a live listening stream
        while self._running:
            await asyncio.sleep(60)

    async def _live_stream(self, reddit: praw.Reddit) -> AsyncGenerator[RedditPostEvent, None]:
        """Streams live submissions across configured subreddits."""
        subreddit_str = "+".join(settings.subreddit_list)
        logger.info(f"Connecting to live Reddit stream for r/{subreddit_str}...")
        subreddits = reddit.subreddit(subreddit_str)

        # Run PRAW blocking generator in a thread pool executor
        loop = asyncio.get_running_loop()

        def get_submission_stream():
            return subreddits.stream.submissions(pause_after=5, skip_existing=True)

        stream = await loop.run_in_executor(None, get_submission_stream)

        while self._running:
            try:
                submission = await loop.run_in_executor(None, lambda: next(stream, None))
                if submission is None:
                    await asyncio.sleep(2)
                    continue

                event = normalize_submission(submission)
                if is_valid_candidate(event):
                    yield event

            except Exception as e:
                logger.error(f"Error reading from PRAW stream: {e}. Backing off 5s...")
                await asyncio.sleep(5)
                stream = await loop.run_in_executor(None, get_submission_stream)

    async def _run_loop(self):
        """Core worker loop."""
        reddit = self._init_praw()
        generator = self._live_stream(reddit) if reddit else self._mock_stream()

        async for event in generator:
            if not self._running:
                break
            
            # Persist raw post to SQLite
            await save_raw_post(
                thread_id=event.thread_id,
                subreddit=event.subreddit,
                title=event.title,
                body=event.body,
                author=event.author,
                permalink=event.permalink,
                created_utc=event.created_utc,
            )
            
            # Push into async processing queue
            await self.queue.put(event)
            logger.info(f"Ingested [{event.subreddit}] '{event.title[:45]}...' (ID: {event.thread_id})")

    def start(self) -> asyncio.Task:
        """Starts ingestion listener daemon as a background task."""
        if self._running:
            logger.warning("Listener is already running.")
            return self._task

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Reddit Ingestion Daemon started.")
        return self._task

    async def stop(self):
        """Stops ingestion daemon."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Reddit Ingestion Daemon stopped.")
