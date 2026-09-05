"""
Reddit Post Event Normalizer.
Sanitizes and normalizes raw PRAW or webhook submissions into structured events.
"""

import re
from typing import Any, Dict
from pydantic import BaseModel, Field


class RedditPostEvent(BaseModel):
    """Normalized schema for ingested Reddit posts."""
    thread_id: str = Field(..., description="Unique Reddit post ID (e.g., 't3_1h9k2z8' or '1h9k2z8')")
    subreddit: str = Field(..., description="Subreddit name including r/ prefix")
    title: str = Field(..., description="Post submission title")
    body: str = Field(default="", description="Cleaned post self-text body")
    author: str = Field(default="[deleted]", description="Reddit username of author")
    permalink: str = Field(..., description="Full canonical URL to the Reddit thread")
    created_utc: float = Field(..., description="UNIX timestamp of post creation")

    @property
    def full_text(self) -> str:
        """Combined title and body for LLM context processing."""
        if self.body.strip():
            return f"Title: {self.title}\n\nBody:\n{self.body.strip()}"
        return f"Title: {self.title}"


def clean_text(text: str) -> str:
    """Strip extraneous whitespace, control characters, and normalize line breaks."""
    if not text:
        return ""
    # Replace non-breaking spaces and irregular whitespace
    text = text.replace("\u200b", "").replace("\r\n", "\n")
    # Normalize consecutive blank lines to double newline
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_submission(raw_post: Any) -> RedditPostEvent:
    """
    Normalizes either a PRAW Submission object or a dictionary event.
    """
    if isinstance(raw_post, dict):
        thread_id = str(raw_post.get("thread_id") or raw_post.get("id", ""))
        if not thread_id.startswith("t3_") and not thread_id.startswith("hn_") and thread_id:
            thread_id = f"t3_{thread_id}"
        
        subreddit = raw_post.get("subreddit", "")
        if not subreddit.startswith("r/") and not ("ycombinator" in subreddit or subreddit == "Ask HN"):
            subreddit = f"r/{subreddit}"

        permalink = raw_post.get("permalink", "")
        if permalink and not permalink.startswith("http"):
            permalink = f"https://reddit.com{permalink}"

        return RedditPostEvent(
            thread_id=thread_id,
            subreddit=subreddit,
            title=clean_text(raw_post.get("title", "")),
            body=clean_text(raw_post.get("body", raw_post.get("selftext", ""))),
            author=str(raw_post.get("author", "[deleted]")),
            permalink=permalink,
            created_utc=float(raw_post.get("created_utc", 0)),
        )

    # Assume PRAW Submission object
    raw_id = getattr(raw_post, "id", "")
    thread_id = f"t3_{raw_id}" if not raw_id.startswith("t3_") else raw_id
    
    sub_name = getattr(raw_post.subreddit, "display_name", str(raw_post.subreddit))
    subreddit = f"r/{sub_name}" if not sub_name.startswith("r/") else sub_name

    permalink = getattr(raw_post, "permalink", "")
    if permalink and not permalink.startswith("http"):
        permalink = f"https://reddit.com{permalink}"

    author_obj = getattr(raw_post, "author", None)
    author = getattr(author_obj, "name", "[deleted]") if author_obj else "[deleted]"

    return RedditPostEvent(
        thread_id=thread_id,
        subreddit=subreddit,
        title=clean_text(getattr(raw_post, "title", "")),
        body=clean_text(getattr(raw_post, "selftext", "")),
        author=author,
        permalink=permalink,
        created_utc=float(getattr(raw_post, "created_utc", 0)),
    )


def is_valid_candidate(post: RedditPostEvent) -> bool:
    """
    Discard invalid, removed, deleted, or empty spam posts before triggering agents.
    """
    if not post.title or len(post.title.strip()) < 5:
        return False
    if post.author in ("[deleted]", "[removed]"):
        return False
    if post.body in ("[deleted]", "[removed]"):
        return False
    return True
