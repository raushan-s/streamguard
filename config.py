"""
Consolidated configuration for StreamGuard security library.

Validates all environment variables at cold start and provides
a single source of truth for all layer configurations.
"""

import os
from pathlib import Path
from typing import Optional

# Try to import upstash-redis, but don't fail if it's not installed
try:
    import upstash_redis
    UPSTASH_AVAILABLE = True
except ImportError:
    UPSTASH_AVAILABLE = False


class LambdaConfig:
    """
    Unified configuration for all detection layers.

    All layers must import config from this root config.py via LambdaConfig,
    NOT from layers/stateful_config.py.

    Note: Layer 4 (Stateful Analysis) is optional and requires upstash-redis.
    """

    # Model paths
    MODEL_PATH: Path = Path(os.getenv("MODEL_PATH", "./models/"))
    HF_HOME: Path = MODEL_PATH / "hf_cache"

    # HuggingFace (Layers 2a, 2b)
    HF_TOKEN: Optional[str] = os.getenv("HF_TOKEN")
    PROMPT_GUARD_THRESHOLD: float = float(os.getenv("PROMPT_GUARD_THRESHOLD", "0.5"))
    DEBERTA_THRESHOLD: float = float(os.getenv("DEBERTA_THRESHOLD", "0.85"))

    # OpenAI (Layers 3, 4)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    MODERATION_TIMEOUT: float = float(os.getenv("MODERATION_TIMEOUT", "3.0"))

    # Redis (Layer 4)
    UPSTASH_REDIS_URL: Optional[str] = os.getenv("UPSTASH_REDIS_URL")
    UPSTASH_REDIS_TOKEN: Optional[str] = os.getenv("UPSTASH_REDIS_TOKEN")
    STATEFUL_RISK_THRESHOLD: float = float(os.getenv("STATEFUL_RISK_THRESHOLD", "0.7"))
    STATEFUL_MAX_HISTORY: int = int(os.getenv("STATEFUL_MAX_HISTORY", "20"))
    REDIS_TTL_SECONDS: int = int(os.getenv("REDIS_TTL_SECONDS", "86400"))

    # Feature flags
    ENABLE_LAYER4: bool = os.getenv("ENABLE_LAYER4", "false").lower() == "true"

    @classmethod
    def validate(cls) -> tuple[bool, Optional[str]]:
        """
        Validate configuration at cold start.

        Returns:
            (is_valid, error_message) - tuple of validation status and error message
        """
        errors = []

        # Required for Layers 2a, 2b (HuggingFace models)
        if not cls.HF_TOKEN:
            errors.append("HF_TOKEN is required for jailbreak/injection detection")

        # Required for Layer 3
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required for content moderation")

        # Required for Layer 4 (if enabled)
        if cls.ENABLE_LAYER4:
            # Check if upstash-redis is installed
            if not UPSTASH_AVAILABLE:
                errors.append("upstash-redis package is not installed. Install it with: pip install upstash-redis")
            # Check if credentials are provided
            if not cls.UPSTASH_REDIS_URL:
                errors.append("UPSTASH_REDIS_URL is required when Layer 4 is enabled")
            if not cls.UPSTASH_REDIS_TOKEN:
                errors.append("UPSTASH_REDIS_TOKEN is required when Layer 4 is enabled")

        # Validate thresholds
        if not 0.0 <= cls.PROMPT_GUARD_THRESHOLD <= 1.0:
            errors.append("PROMPT_GUARD_THRESHOLD must be between 0.0 and 1.0")

        if not 0.0 <= cls.DEBERTA_THRESHOLD <= 1.0:
            errors.append("DEBERTA_THRESHOLD must be between 0.0 and 1.0")

        if not 0.0 <= cls.STATEFUL_RISK_THRESHOLD <= 1.0:
            errors.append("STATEFUL_RISK_THRESHOLD must be between 0.0 and 1.0")

        if errors:
            return False, "; ".join(errors)

        return True, None

    @classmethod
    def get_config_dict(cls) -> dict:
        """
        Get configuration as dictionary for logging.

        Returns:
            Dict with non-sensitive configuration values
        """
        return {
            "model_path": str(cls.MODEL_PATH),
            "prompt_guard_threshold": cls.PROMPT_GUARD_THRESHOLD,
            "deberta_threshold": cls.DEBERTA_THRESHOLD,
            "moderation_timeout": cls.MODERATION_TIMEOUT,
            "stateful_enabled": cls.ENABLE_LAYER4,
            "stateful_threshold": cls.STATEFUL_RISK_THRESHOLD if cls.ENABLE_LAYER4 else None,
        }
