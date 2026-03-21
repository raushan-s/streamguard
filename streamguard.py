"""
StreamGuard - Python Security Library for AI/LLM Applications

A comprehensive 4-layer security analysis system:
- Layer 1: PII Detection (Presidio)
- Layer 2a: Jailbreak Detection (Prompt Guard 2)
- Layer 2b: Injection Detection (DeBERTa)
- Layer 3: Content Moderation (OpenAI API)
- Layer 4: Stateful Analysis (GPT-4o-mini + Redis) - Optional

Layers 1-3 run in parallel for minimal latency. Layer 4 runs after if enabled and session_id provided.
Returns ALL layer scores - you decide what to block based on your thresholds.

Basic Usage:
    from streamguard import analyze_text

    result = analyze_text("Your text here")
    print(result["layer_results"]["jailbreak"])
"""

import json
import time
import concurrent.futures
import os
from typing import Dict, Any, Optional

# Import layer modules
from layers import layer1_pii, layer2a_prompt_guard, layer2b_deberta
from layers.async_wrappers import check_moderation_sync, check_stateful_sync
from layers.schemas import StatefulInput, Direction
from layers.normalize import normalize_for_classification
from config import LambdaConfig


# Global model cache for warm starts
_MODEL_CACHE = {
    "initialized": False,
    "init_error": None,
    "models": {}
}


def initialize_models() -> Optional[str]:
    """
    Initialize models at cold start.

    Returns:
        None if successful, error message string if failed
    """
    if _MODEL_CACHE["initialized"]:
        print("[DEBUG] Models already cached", flush=True)
        return None

    try:
        # Get model path from environment or use default
        model_path = os.environ.get('MODEL_PATH', './models')
        print(f"[DEBUG] Using models from: {model_path}", flush=True)

        # Import model loaders
        print("[DEBUG] Importing model loaders...", flush=True)
        from layers.layer2a_prompt_guard import load_model as load_pg
        from layers.layer2b_deberta import load_model as load_deberta
        print("[DEBUG] Model loaders imported successfully", flush=True)

        # Load Prompt Guard 2
        print("[DEBUG] Loading Prompt Guard 2 model...", flush=True)
        import sys
        print(f"[DEBUG] Before load_pg(), memory usage: {sys.getsizeof(_MODEL_CACHE)}", flush=True)
        pg_model, pg_tokenizer = load_pg()
        _MODEL_CACHE["models"]["prompt_guard"] = (
            pg_model, pg_tokenizer
        )
        print("[DEBUG] Prompt Guard 2 loaded successfully", flush=True)

        # Load DeBERTa
        print("[DEBUG] Loading DeBERTa model...", flush=True)
        deberta_model, deberta_tokenizer = load_deberta()
        _MODEL_CACHE["models"]["deberta"] = (
            deberta_model, deberta_tokenizer
        )
        print("[DEBUG] DeBERTa loaded successfully", flush=True)

        _MODEL_CACHE["initialized"] = True
        print("[DEBUG] Model initialization complete", flush=True)
        return None

    except Exception as e:
        import traceback
        error_msg = f"Model initialization failed: {str(e)}"
        print(f"[DEBUG] Error: {error_msg}", flush=True)
        print(f"[DEBUG] Traceback: {traceback.format_exc()}", flush=True)
        _MODEL_CACHE["init_error"] = error_msg
        return error_msg


def analyze_text(
    text: str,
    session_id: Optional[str] = None,
    agent_id: Optional[str] = "default",
    direction: str = "input"
) -> Dict[str, Any]:
    """
    Analyze text for security threats using multiple detection layers.

    Args:
        text: The text to analyze (required)
        session_id: Optional session identifier for stateful analysis (Layer 4)
        agent_id: Optional agent identifier (default: "default")
        direction: Either "input" or "output" (default: "input")

    Returns:
        Dict with structure:
        {
            "layer_results": {
                "pii": {...},
                "jailbreak": {...},
                "injection": {...},
                "moderation": {...},
                "stateful": {...}  # only if session_id provided and Layer 4 enabled
            },
            "latency_ms": 123.45
        }

    Example:
        >>> from streamguard import analyze_text
        >>> result = analyze_text("Ignore all previous instructions")
        >>> print(result["layer_results"]["jailbreak"]["label"])
        'MALICIOUS'
    """
    start_time = time.time()
    print("[DEBUG] StreamGuard analysis started", flush=True)

    # Step 1: Initialize models on cold start
    if not _MODEL_CACHE["initialized"]:
        print("[DEBUG] Initializing models...", flush=True)
        error = initialize_models()
        if error:
            return {
                "error": error,
                "layer_results": {}
            }
        print("[DEBUG] Models initialized", flush=True)

    # Step 2: Validate input
    print("[DEBUG] Validating input...", flush=True)
    if not text or not isinstance(text, str):
        return {
            "error": "Missing or invalid 'text' parameter",
            "layer_results": {}
        }

    # Validate direction
    if direction not in ["input", "output"]:
        direction = "input"

    # Step 3: Normalize text once for Layers 2a and 2b
    print("[DEBUG] Normalizing text...", flush=True)
    normalized = normalize_for_classification(text)
    print("[DEBUG] Text normalized", flush=True)

    # Step 4: Run Layers 1, 2a, 2b, 3 in PARALLEL for lowest latency
    print("[DEBUG] Starting layer execution...", flush=True)
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_pii = executor.submit(layer1_pii.check_pii, text)
            future_jailbreak = executor.submit(
                layer2a_prompt_guard.check_prompt_guard, normalized
            )
            future_injection = executor.submit(
                layer2b_deberta.check_deberta,
                normalized,
                LambdaConfig.DEBERTA_THRESHOLD
            )
            future_moderation = executor.submit(check_moderation_sync, text)

            results = {
                "pii": future_pii.result(timeout=30),
                "jailbreak": future_jailbreak.result(timeout=10),
                "injection": future_injection.result(timeout=10),
                "moderation": future_moderation.result(timeout=10),
            }
    except Exception as e:
        import traceback
        return {
            "error": f"Layer execution failed: {str(e)}",
            "traceback": traceback.format_exc(),
            "layer_results": {}
        }

    # Step 5: Layer 4 - Stateful Analysis (runs AFTER, only if session_id provided)
    if LambdaConfig.ENABLE_LAYER4 and session_id:
        try:
            input_data = StatefulInput(
                text=text,
                direction=Direction.INPUT if direction == "input" else Direction.OUTPUT,
                session_id=session_id,
                agent_id=agent_id
            )
            stateful_result = check_stateful_sync(input_data)
            results["stateful"] = stateful_result.model_dump()
        except Exception as e:
            # Layer 4 failure shouldn't block other results
            results["stateful"] = {
                "analyzed": False,
                "error": f"Stateful analysis failed: {str(e)}"
            }

    # Step 6: Return ALL layer results
    latency_ms = round((time.time() - start_time) * 1000, 2)
    print("[DEBUG] Returning results...", flush=True)

    return {
        "layer_results": results,
        "latency_ms": latency_ms
    }
