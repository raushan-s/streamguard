"""Pydantic schemas for Layer 4 stateful analysis."""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class Direction(str, Enum):
    """Message direction in conversation."""
    INPUT = "input"
    OUTPUT = "output"


class PatternType(str, Enum):
    """Attack patterns detected by stateful analysis."""
    PROGRESSIVE_EXTRACTION = "progressive_extraction"
    REPETITIOUS_PROBING = "repetitious_probing"
    CROSS_AGENT_POLLUTION = "cross_agent_pollution"
    CONTEXT_MANIPULATION = "context_manipulation"
    ROLE_CONFUSION = "role_confusion"
    BENIGN = "benign"


class StatefulInput(BaseModel):
    """Input for stateful analysis."""
    text: str = Field(..., min_length=1, max_length=10000, description="Message text (1-10,000 characters)")
    direction: Direction = Field(..., description="Message direction (INPUT or OUTPUT)")
    session_id: Optional[str] = Field(None, description="Session identifier (None = stateless mode)")
    agent_id: str = Field(default="default", description="Agent identifier")
    metadata: Optional[Dict] = Field(default=None, description="Additional metadata for future extensibility")

    @field_validator('text')
    @classmethod
    def validate_text_length(cls, v: str) -> str:
        """Validate text length is within bounds."""
        if not v or not v.strip():
            raise ValueError("text cannot be empty or whitespace only")
        if len(v) > 10000:
            raise ValueError("text cannot exceed 10,000 characters")
        return v.strip()


class StatefulOutput(BaseModel):
    """Output from stateful analysis."""
    analyzed: bool = Field(..., description="True if full analysis was performed")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk score (0.0-1.0)")
    patterns_detected: List[PatternType] = Field(default_factory=list, description="Patterns detected")
    explanation: str = Field(default="", description="Explanation of analysis result")
    session_message_count: int = Field(default=0, ge=0, description="Number of messages in session")
    latency_ms: float = Field(default=0.0, ge=0.0, description="Total operation time in milliseconds")
    error: Optional[str] = Field(None, description="Error message if analysis failed")
