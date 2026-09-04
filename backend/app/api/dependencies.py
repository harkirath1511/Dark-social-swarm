"""
FastAPI Dependencies for Dark Social Swarm.
Provides database connections and shared LangGraph execution instances.
"""

from typing import AsyncGenerator
import aiosqlite
from langgraph.checkpoint.memory import MemorySaver

from app.core.config import settings
from app.core.database import get_db
from app.swarm.graph import compile_swarm_graph

# Shared in-memory checkpointer for LangGraph execution state
checkpointer = MemorySaver()
swarm_graph = compile_swarm_graph(checkpointer=checkpointer)


async def get_db_session() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Dependency that yields an active SQLite database session with WAL mode."""
    async with get_db() as db:
        yield db


def get_graph():
    """Returns compiled LangGraph app with active checkpointer."""
    return swarm_graph
