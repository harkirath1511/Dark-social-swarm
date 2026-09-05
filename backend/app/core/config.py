"""
Core application configuration using Pydantic Settings.
Loads environment variables from .env files with sane defaults for local development.
"""

from typing import List
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(BASE_DIR / ".env", BASE_DIR.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application
    APP_NAME: str = "Dark Social Swarm"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # LLM Settings
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API Key")
    ANTHROPIC_API_KEY: str = Field(default="", description="Anthropic API Key")
    GROQ_API_KEY: str = Field(default="", description="Groq API Key (Free high-speed Llama-3)")
    DEFAULT_LLM_MODEL: str = "gpt-4o-mini"
    REASONING_LLM_MODEL: str = "gpt-4o"
    GROQ_MODEL: str = "openai/gpt-oss-20b"
    LLM_PROVIDER: str = "auto"  # "auto", "groq", "openai", "anthropic"

    # Reddit Ingestion (PRAW)
    REDDIT_CLIENT_ID: str = Field(default="", description="PRAW Reddit Client ID")
    REDDIT_CLIENT_SECRET: str = Field(default="", description="PRAW Reddit Client Secret")
    REDDIT_USER_AGENT: str = "DarkSocialSwarm/0.1.0 by developer"
    REDDIT_SUBREDDITS: str = "SaaS,startups,Entrepreneur,smallbusiness,marketing"
    MOCK_INGESTION_MODE: bool = True  # Automatically enabled if credentials missing

    # Swarm Decision Thresholds
    OPPORTUNITY_SCORE_THRESHOLD: int = 40
    MAX_CRITIC_RETRIES: int = 2

    # Storage & Persistence
    SQLITE_DB_PATH: str = str(BASE_DIR / "dark_social_swarm.db")
    CHECKPOINTER_DB_PATH: str = str(BASE_DIR / "swarm_checkpointer.db")

    @property
    def subreddit_list(self) -> List[str]:
        return [s.strip() for s in self.REDDIT_SUBREDDITS.split(",") if s.strip()]

    @property
    def has_reddit_creds(self) -> bool:
        return bool(
            self.REDDIT_CLIENT_ID
            and self.REDDIT_CLIENT_SECRET
            and self.REDDIT_CLIENT_ID != "your_reddit_client_id"
        )


settings = Settings()
