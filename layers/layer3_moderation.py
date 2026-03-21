"""
StreamGuard V3 - Layer 3: Content Moderation
============================================
Async OpenAI Moderation API integration with timeout protection.

This layer detects harmful content across 11 categories using OpenAI's Moderation API.
It operates as a non-blocking async service with graceful fallback on timeout.

Categories:
- harassment, harassment/threatening
- hate, hate/threatening
- violence, violence/graphic
- self-harm, self-harm/intent, self-harm/instructions
- sexual, sexual/minors, sexual/violence
- illicit, illicit/violent
"""

import os
from typing import Dict, Any
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODERATION_URL = "https://api.openai.com/v1/moderations"
REQUEST_TIMEOUT = 3.0  # 3-second timeout to prevent blocking pipeline


async def check_openai_moderation(text: str) -> Dict[str, Any]:
    """
    Check text content using OpenAI's Moderation API asynchronously.

    This function makes a non-blocking HTTP call to OpenAI's Moderation API
    to detect potentially harmful content across 11 categories. It includes
    timeout protection to prevent blocking the security pipeline.

    Args:
        text: The input text to moderate. Should NOT be normalized/preprocessed.

    Returns:
        Dict with structure:
        {
            "flagged": bool,  # True if any category threshold exceeded
            "categories": {   # All 11 category scores (0.0-1.0)
                "harassment": float,
                "harassment_threatening": float,
                "hate": float,
                "hate_threatening": float,
                "violence": float,
                "violence_graphic": float,
                "self_harm": float,
                "self_harm_intent": float,
                "self_harm_instructions": float,
                "sexual": float,
                "sexual_minors": float,
                "sexual_violence": float,
                "illicit": float,
                "illicit_violent": float,
            },
            "error": str | None  # "timeout", "api_error", "invalid_input", or None
        }

    Examples:
        >>> result = await check_openai_moderation("Hello world")
        >>> print(result["flagged"])
        False

        >>> result = await check_openai_moderation("I hate everyone")
        >>> print(result["flagged"])
        True
        >>> print(result["categories"]["harassment"])
        0.9
    """
    # Validate input
    if not isinstance(text, str):
        return {
            "flagged": False,
            "categories": {},
            "error": "invalid_input"
        }

    if not text.strip():
        return {
            "flagged": False,
            "categories": {},
            "error": "invalid_input"
        }

    # Check if API key is configured
    if not OPENAI_API_KEY:
        return {
            "flagged": False,
            "categories": {},
            "error": "api_error"
        }

    # Prepare request
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "omni-moderation-latest",
        "input": text  # Use original text, DO NOT normalize
    }

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                OPENAI_MODERATION_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            # Parse response
            data = response.json()
            result = data["results"][0]

            # Extract all category scores (handle missing categories)
            category_scores = result["category_scores"]
            categories = {
                "harassment": category_scores.get("harassment", 0.0),
                "harassment_threatening": category_scores.get("harassment/threatening", 0.0),
                "hate": category_scores.get("hate", 0.0),
                "hate_threatening": category_scores.get("hate/threatening", 0.0),
                "violence": category_scores.get("violence", 0.0),
                "violence_graphic": category_scores.get("violence/graphic", 0.0),
                "self_harm": category_scores.get("self-harm", 0.0),
                "self_harm_intent": category_scores.get("self-harm/intent", 0.0),
                "self_harm_instructions": category_scores.get("self-harm/instructions", 0.0),
                "sexual": category_scores.get("sexual", 0.0),
                "sexual_minors": category_scores.get("sexual/minors", 0.0),
                "sexual_violence": category_scores.get("sexual/violence", 0.0),
                "illicit": category_scores.get("illicit", 0.0),
                "illicit_violent": category_scores.get("illicit/violent", 0.0),
            }

            return {
                "flagged": result["flagged"],
                "categories": categories,
                "error": None
            }

    except httpx.TimeoutException:
        # Timeout fallback - return safe default
        return {
            "flagged": False,
            "categories": {},
            "error": "timeout"
        }
    except httpx.HTTPStatusError:
        # API error fallback
        return {
            "flagged": False,
            "categories": {},
            "error": "api_error"
        }
    except Exception:
        # Generic error fallback
        return {
            "flagged": False,
            "categories": {},
            "error": "api_error"
        }
