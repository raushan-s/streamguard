"""Layer 4: Stateful Session Analysis - Main check function."""

import json
import time
import asyncio
from typing import Optional
import httpx
from .schemas import StatefulInput, StatefulOutput, Direction, PatternType
from .stateful_config import Config
from .session import get_session, update_session


async def analyze_with_gpt(history: str) -> dict:
    """
    Analyze conversation history using GPT-4o-mini.

    Args:
        history: Conversation history string

    Returns:
        Dictionary with risk_score, patterns_detected, and explanation
        or error information if analysis fails

    Raises:
        httpx.HTTPError: If HTTP request fails
        json.JSONDecodeError: If response is not valid JSON
    """
    # Load system prompt
    try:
        system_prompt = Config.load_system_prompt()
    except Exception as e:
        return {
            "risk_score": 0.0,
            "patterns_detected": [],
            "explanation": f"Failed to load system prompt: {e}",
            "error": f"System prompt error: {e}"
        }

    # Prepare request
    request_data = {
        "model": Config.GPT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze this conversation:\n\n{history}"}
        ],
        "temperature": Config.GPT_TEMPERATURE,
        "max_tokens": Config.GPT_MAX_TOKENS
    }

    # Make API call with timeout
    async with httpx.AsyncClient(timeout=Config.GPT_TIMEOUT) as client:
        try:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {Config.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=request_data
            )
            response.raise_for_status()
        except httpx.TimeoutException:
            return {
                "risk_score": 0.0,
                "patterns_detected": [],
                "explanation": "GPT analysis timed out",
                "error": "Request timeout"
            }
        except httpx.HTTPStatusError as e:
            return {
                "risk_score": 0.0,
                "patterns_detected": [],
                "explanation": f"GPT API error: {e.response.status_code}",
                "error": f"HTTP error: {e.response.status_code}"
            }
        except httpx.RequestError as e:
            return {
                "risk_score": 0.0,
                "patterns_detected": [],
                "explanation": f"GPT request failed: {e}",
                "error": f"Request error: {e}"
            }

    # Parse response
    try:
        response_data = response.json()
        content = response_data["choices"][0]["message"]["content"]

        # Parse JSON from GPT response
        # GPT might wrap JSON in markdown code blocks
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        result = json.loads(content)

        # Validate required fields
        if "risk_score" not in result:
            raise ValueError("Missing risk_score in GPT response")
        if "patterns_detected" not in result:
            raise ValueError("Missing patterns_detected in GPT response")
        if "explanation" not in result:
            result["explanation"] = "No explanation provided"

        # Convert patterns to PatternType enums
        patterns = []
        for pattern in result["patterns_detected"]:
            try:
                patterns.append(PatternType(pattern))
            except ValueError:
                # Ignore invalid pattern names
                pass
        result["patterns_detected"] = patterns

        return result

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        return {
            "risk_score": 0.0,
            "patterns_detected": [],
            "explanation": f"Failed to parse GPT response: {e}",
            "error": f"Parse error: {e}"
        }
    except Exception as e:
        return {
            "risk_score": 0.0,
            "patterns_detected": [],
            "explanation": f"Unexpected error during GPT analysis: {e}",
            "error": f"Unexpected error: {e}"
        }


async def check_stateful(input_data: StatefulInput) -> StatefulOutput:
    """
    Perform stateful analysis on a message.

    This function handles three cases:
    1. No session_id provided — Return analyzed=False
    2. Insufficient history (< 2 messages) — Update session, return analyzed=False
    3. Full analysis — Analyze with GPT, update session with label

    Args:
        input_data: Input data with text, direction, and optional session_id

    Returns:
        StatefulOutput with analysis results
    """
    start_time = time.time()

    # Case 1: No session_id provided
    if not input_data.session_id:
        return StatefulOutput(
            analyzed=False,
            risk_score=0.0,
            patterns_detected=[],
            explanation="No session_id provided — stateful analysis requires session tracking",
            session_message_count=0,
            latency_ms=(time.time() - start_time) * 1000
        )

    try:
        # Get current session
        session = get_session(input_data.session_id)

        # Case 2: Insufficient history
        if session is None or session["message_count"] < 2:
            # Update session with "unanalyzed" label
            updated_session = update_session(
                input_data.session_id,
                input_data.text,
                input_data.direction,
                input_data.agent_id,
                label="unanalyzed"
            )

            message_count = updated_session["message_count"]

            if message_count < 2:
                explanation = f"Insufficient history for analysis (need 2+ messages, have {message_count})"
            else:
                explanation = "Building conversation history for analysis"

            return StatefulOutput(
                analyzed=False,
                risk_score=0.0,
                patterns_detected=[],
                explanation=explanation,
                session_message_count=message_count,
                latency_ms=(time.time() - start_time) * 1000
            )

        # Case 3: Full analysis with GPT
        # First, add current message to session with "unanalyzed" label
        session = update_session(
            input_data.session_id,
            input_data.text,
            input_data.direction,
            input_data.agent_id,
            label="unanalyzed"
        )

        # Analyze with GPT
        gpt_result = await analyze_with_gpt(session["history"])

        # Determine label based on risk score
        if gpt_result.get("error"):
            # Error occurred — keep "unanalyzed" label
            label = "unanalyzed"
        elif gpt_result["risk_score"] >= Config.RISK_THRESHOLD:
            label = "flagged"
        else:
            label = "benign"

        # Update session with final label
        # We need to replace the last "unanalyzed" label with the final label
        lines = session["history"].split("\n")
        if lines:
            last_line = lines[-1]
            # Replace the label in the last line
            if "[unanalyzed]" in last_line:
                lines[-1] = last_line.replace("[unanalyzed]", f"[{label}]")
                session["history"] = "\n".join(lines)

                # Save updated session
                from .session import get_redis_client
                redis = get_redis_client()
                redis.set(
                    f"session:{input_data.session_id}",
                    json.dumps(session),
                    ex=Config.REDIS_TTL_SECONDS
                )

        # Build output
        error = gpt_result.get("error")
        patterns = gpt_result.get("patterns_detected", [])
        risk_score = gpt_result.get("risk_score", 0.0)
        explanation = gpt_result.get("explanation", "")

        # Validate risk score is in valid range
        risk_score = max(0.0, min(1.0, risk_score))

        return StatefulOutput(
            analyzed=not bool(error),
            risk_score=risk_score,
            patterns_detected=patterns,
            explanation=explanation,
            session_message_count=session["message_count"],
            latency_ms=(time.time() - start_time) * 1000,
            error=error
        )

    except Exception as e:
        # Graceful error handling — never crash the orchestrator
        return StatefulOutput(
            analyzed=False,
            risk_score=0.0,
            patterns_detected=[],
            explanation=f"Stateful analysis failed: {e}",
            session_message_count=0,
            latency_ms=(time.time() - start_time) * 1000,
            error=str(e)
        )


# Synchronous wrapper for compatibility
def check_stateful_sync(input_data: StatefulInput) -> StatefulOutput:
    """
    Synchronous wrapper for check_stateful.

    Args:
        input_data: Input data

    Returns:
        StatefulOutput with analysis results
    """
    try:
        # Run async function in event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an async context, create a new loop
            import asyncio
            return asyncio.run(check_stateful(input_data))
        else:
            return loop.run_until_complete(check_stateful(input_data))
    except RuntimeError:
        # No event loop exists, create new one
        return asyncio.run(check_stateful(input_data))
