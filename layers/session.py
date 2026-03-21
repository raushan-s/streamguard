"""Redis session management for Layer 4 stateful analysis."""

import json
import time
from typing import Optional, Dict, Any
from upstash_redis import Redis
from .stateful_config import Config
from .schemas import Direction


def get_redis_client() -> Redis:
    """
    Get Upstash Redis client.

    Returns:
        Configured Redis client

    Raises:
        ValueError: If Redis configuration is invalid
    """
    if not Config.UPSTASH_REDIS_URL or not Config.UPSTASH_REDIS_TOKEN:
        raise ValueError("Redis URL and token are required")

    return Redis(
        url=Config.UPSTASH_REDIS_URL,
        token=Config.UPSTASH_REDIS_TOKEN
    )


def format_history_entry(
    text: str,
    direction: Direction,
    agent_id: str,
    label: str = "unanalyzed"
) -> str:
    """
    Format a conversation history entry.

    Args:
        text: Message text
        direction: Message direction (INPUT/OUTPUT)
        agent_id: Agent identifier
        label: Analysis label (flagged, benign, unanalyzed)

    Returns:
        Formatted history entry string

    Example:
        >>> format_history_entry("Hello", Direction.INPUT, "default", "benign")
        "INPUT[default][benign]: Hello"
    """
    # Clean and escape text to prevent format injection
    clean_text = text.replace('\n', ' ').strip()
    # Limit length to prevent storage bloat
    if len(clean_text) > 500:
        clean_text = clean_text[:500] + "..."
    return f"{direction.value.upper()}[{agent_id}][{label}]: {clean_text}"


def parse_history_entry(entry: str) -> Dict[str, str]:
    """
    Parse a conversation history entry.

    Args:
        entry: Formatted history entry string

    Returns:
        Dictionary with direction, agent_id, label, and text

    Example:
        >>> parse_history_entry("INPUT[default][benign]: Hello")
        {"direction": "input", "agent_id": "default", "label": "benign", "text": "Hello"}
    """
    try:
        # Parse format: DIRECTION[agent_id][label]: text
        # Example: INPUT[default][benign]: Hello world
        import re

        # Use regex to match the entire pattern
        pattern = r'^([A-Z]+)\[([^\]]+)\]\[([^\]]+)\]:\s*(.*)$'
        match = re.match(pattern, entry)

        if not match:
            return {"direction": "unknown", "agent_id": "unknown", "label": "unknown", "text": entry}

        direction, agent_id, label, text = match.groups()

        return {
            "direction": direction.lower(),
            "agent_id": agent_id,
            "label": label,
            "text": text.strip()
        }
    except Exception:
        # Return safe default on parse error
        return {"direction": "unknown", "agent_id": "unknown", "label": "unknown", "text": entry}


def create_session(session_id: str) -> Dict[str, Any]:
    """
    Create a new session.

    Args:
        session_id: Session identifier

    Returns:
        Created session object
    """
    return {
        "history": "",
        "message_count": 0,
        "last_updated": time.time(),
        "agent_ids": [],
        "flagged_count": 0
    }


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a session from Redis.

    Args:
        session_id: Session identifier

    Returns:
        Session object or None if not found

    Raises:
        Exception: Redis connection or parsing errors
    """
    redis = get_redis_client()
    data = redis.get(f"session:{session_id}")

    if not data:
        return None

    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid session data in Redis: {e}")


def update_session(
    session_id: str,
    text: str,
    direction: Direction,
    agent_id: str,
    label: str = "unanalyzed"
) -> Dict[str, Any]:
    """
    Update a session with a new message.

    Args:
        session_id: Session identifier
        text: Message text
        direction: Message direction (INPUT/OUTPUT)
        agent_id: Agent identifier
        label: Analysis label (flagged, benign, unanalyzed)

    Returns:
        Updated session object

    Raises:
        Exception: Redis connection or update errors
    """
    redis = get_redis_client()

    # Get existing session or create new one
    session = get_session(session_id)
    if session is None:
        session = create_session(session_id)

    # Format new history entry
    entry = format_history_entry(text, direction, agent_id, label)

    # Append to history
    if session["history"]:
        session["history"] += "\n" + entry
    else:
        session["history"] = entry

    # Update metadata
    session["message_count"] += 1
    session["last_updated"] = time.time()

    # Track agent_id
    if agent_id not in session["agent_ids"]:
        session["agent_ids"].append(agent_id)

    # Track flagged count
    if label == "flagged":
        session["flagged_count"] += 1

    # Limit history size if needed
    if session["message_count"] > Config.MAX_HISTORY_TURNS:
        # Remove oldest entries
        lines = session["history"].split("\n")
        excess = session["message_count"] - Config.MAX_HISTORY_TURNS
        # Remove excess lines from the beginning
        lines = lines[excess:]
        session["history"] = "\n".join(lines)
        session["message_count"] = Config.MAX_HISTORY_TURNS

    # Save to Redis with TTL
    redis.set(
        f"session:{session_id}",
        json.dumps(session),
        ex=Config.REDIS_TTL_SECONDS
    )

    return session


def delete_session(session_id: str) -> bool:
    """
    Delete a session from Redis.

    Args:
        session_id: Session identifier

    Returns:
        True if session was deleted, False otherwise
    """
    try:
        redis = get_redis_client()
        redis.delete(f"session:{session_id}")
        return True
    except Exception:
        return False
