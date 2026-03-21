"""
StreamGuard Detection Layers Package

This package contains all 5 detection layers for LLM security analysis.
Layers 1, 2a, and 2b are synchronous and can be imported directly.
Layers 3 and 4 are asynchronous and should be called via async_wrappers.py.
"""

# Export synchronous layers for direct import
from . import layer1_pii
from . import layer2a_prompt_guard
from . import layer2b_deberta

__all__ = [
    "layer1_pii",
    "layer2a_prompt_guard",
    "layer2b_deberta",
]
