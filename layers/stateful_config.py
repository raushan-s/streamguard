"""Configuration for Layer 4 stateful analysis."""

import os
from pathlib import Path
from typing import Optional


class Config:
    """Configuration with environment variable overrides."""

    # Upstash Redis
    UPSTASH_REDIS_URL: str = os.getenv("UPSTASH_REDIS_URL", "")
    UPSTASH_REDIS_TOKEN: str = os.getenv("UPSTASH_REDIS_TOKEN", "")

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Detection thresholds
    RISK_THRESHOLD: float = float(os.getenv("STATEFUL_RISK_THRESHOLD", "0.7"))
    MAX_HISTORY_TURNS: int = int(os.getenv("STATEFUL_MAX_HISTORY_TURNS", "20"))
    REDIS_TTL_SECONDS: int = int(os.getenv("REDIS_TTL_SECONDS", "86400"))

    # GPT-4o-mini settings
    GPT_MODEL: str = "gpt-4o-mini"
    GPT_TEMPERATURE: float = 0.0
    GPT_MAX_TOKENS: int = 300
    GPT_TIMEOUT: float = 10.0  # 10-second timeout (GPT-4o-mini can take 8-10s under load)

    # System prompt file path (using pathlib for robustness)
    SYSTEM_PROMPT_PATH: Path = Path(__file__).parent / "system_prompt.txt"

    @classmethod
    def validate(cls) -> tuple[bool, Optional[str]]:
        """
        Validate configuration.

        Returns:
            (is_valid, error_message)
        """
        if not cls.UPSTASH_REDIS_URL:
            return False, "UPSTASH_REDIS_URL is required"

        if not cls.UPSTASH_REDIS_TOKEN:
            return False, "UPSTASH_REDIS_TOKEN is required"

        if not cls.OPENAI_API_KEY:
            return False, "OPENAI_API_KEY is required"

        if not cls.SYSTEM_PROMPT_PATH.exists():
            return False, f"System prompt file not found: {cls.SYSTEM_PROMPT_PATH}"

        if cls.RISK_THRESHOLD < 0.0 or cls.RISK_THRESHOLD > 1.0:
            return False, "RISK_THRESHOLD must be between 0.0 and 1.0"

        if cls.MAX_HISTORY_TURNS < 2:
            return False, "MAX_HISTORY_TURNS must be at least 2"

        if cls.REDIS_TTL_SECONDS < 60:
            return False, "REDIS_TTL_SECONDS must be at least 60"

        return True, None

    @classmethod
    def load_system_prompt(cls) -> str:
        """
        Load system prompt from file.

        Returns:
            System prompt content

        Raises:
            FileNotFoundError: If system prompt file doesn't exist
            IOError: If file cannot be read
        """
        return cls.SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
