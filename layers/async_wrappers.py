"""
Synchronous wrappers for async layer functions.

These wrappers handle the async functions in Layers 3 and 4 for Lambda compatibility.
They use ThreadPoolExecutor to safely handle Lambda's existing event loops.
"""

import asyncio
import concurrent.futures
from typing import Dict, Any, Coroutine

# Import async functions from layers
from .layer3_moderation import check_openai_moderation
from .layer4_stateful import check_stateful
from .schemas import StatefulInput, StatefulOutput


def run_async_safely(coro: Coroutine) -> Any:
    """
    Run async coroutine safely in Lambda context.

    Handles existing event loops without crashing. Lambda containers may
    reuse event loops between invocations, so we can't use asyncio.run()
    directly.

    Args:
        coro: Async coroutine to execute

    Returns:
        Result of the coroutine execution
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Event loop already running (Lambda container reuse)
            # Use ThreadPoolExecutor to run in separate thread
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result(timeout=10)
        else:
            # No loop or loop not running - use it directly
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No loop exists - create new one
        return asyncio.run(coro)


def check_moderation_sync(text: str) -> Dict[str, Any]:
    """
    Synchronous wrapper for Layer 3 (OpenAI Moderation).

    Args:
        text: Input text to moderate

    Returns:
        Dict with moderation results. Returns safe defaults on error.
    """
    try:
        return run_async_safely(check_openai_moderation(text))
    except Exception as e:
        # Graceful fallback on error
        return {
            "flagged": False,
            "categories": {},
            "error": f"Moderation failed: {str(e)}"
        }


def check_stateful_sync(input_data: StatefulInput) -> StatefulOutput:
    """
    Synchronous wrapper for Layer 4 (Stateful Analysis).

    Args:
        input_data: StatefulInput with text, direction, session_id

    Returns:
        StatefulOutput with analysis results. Returns safe defaults on error.
    """
    try:
        return run_async_safely(check_stateful(input_data))
    except Exception as e:
        # Graceful fallback on error
        return StatefulOutput(
            analyzed=False,
            risk_score=0.0,
            patterns_detected=[],
            explanation=f"Stateful analysis failed: {str(e)}",
            session_message_count=0,
            latency_ms=0.0,
            error=str(e)
        )
