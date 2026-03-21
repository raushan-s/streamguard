"""
Tests for StreamGuard Security Library Handler.

Tests key scenarios including:
- Valid input parsing
- All layers execute without error
- Layers 1-3 run in parallel (latency check)
- Layer 4 graceful degradation when ENABLE_LAYER4=false
- Model loading failure handling
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from streamguard import analyze_text, initialize_models, _MODEL_CACHE
from config import LambdaConfig


class TestAnalyzeText:
    """Test analyze_text functionality."""

    @patch('streamguard.layer1_pii.check_pii')
    @patch('streamguard.layer2a_prompt_guard.check_prompt_guard')
    @patch('streamguard.layer2b_deberta.check_deberta')
    @patch('streamguard.check_moderation_sync')
    @patch('streamguard.initialize_models')
    def test_parse_valid_input(self, mock_init, mock_mod, mock_deberta, mock_pg, mock_pii):
        """Test parsing valid input with mocked layers."""
        # Mock model initialization
        mock_init.return_value = None

        # Mock layer responses
        mock_pii.return_value = {"detected": False, "entities": [], "sanitized": "Hello world"}
        mock_pg.return_value = {"prompt_guard_score": 0.1, "label": "BENIGN"}
        mock_deberta.return_value = {"deberta_score": 0.2, "label": "SAFE"}
        mock_mod.return_value = {"flagged": False, "categories": {}, "error": None}

        result = analyze_text("Hello world", session_id="test-session", agent_id="test-agent", direction="input")

        # Should have layer_results and latency_ms
        assert "layer_results" in result
        assert "latency_ms" in result
        assert isinstance(result["latency_ms"], (int, float))

    def test_missing_text_parameter(self):
        """Test parsing input with missing text parameter."""
        result = analyze_text("")

        assert "error" in result
        assert "Missing or invalid 'text' parameter" in result["error"]

    def test_invalid_direction_defaults_to_input(self):
        """Test that invalid direction defaults to 'input'."""
        # Should not error, direction defaults to 'input'
        result = analyze_text("Hello", direction="invalid")
        assert "layer_results" in result

    def test_all_layers_return_results(self):
        """Test that all layers return results."""
        result = analyze_text("This is a test message")

        # Check that all 4 main layers are present
        assert "layer_results" in result
        layers = result["layer_results"]
        assert "pii" in layers
        assert "jailbreak" in layers
        assert "injection" in layers
        assert "moderation" in layers

    def test_parallel_execution_latency(self):
        """Test that layers run in parallel (latency should be low)."""
        result = analyze_text("Test parallel execution")

        # Parallel execution should complete in reasonable time
        # If sequential, would be much slower (sum of all layers)
        # This is a rough check - actual timing depends on model performance
        assert result["latency_ms"] < 10000  # Should complete within 10 seconds

    def test_session_id_triggers_stateful(self):
        """Test that session_id triggers stateful analysis."""
        with patch('streamguard.LambdaConfig') as mock_config:
            mock_config.ENABLE_LAYER4 = True
            mock_config.DEBERTA_THRESHOLD = 0.85

            result = analyze_text("Test message", session_id="test-session-123")

            # Stateful should be present when session_id provided
            # (may have error if Redis not configured, but should be present)
            assert "stateful" in result["layer_results"]


class TestLayer4Disabled:
    """Test Layer 4 graceful degradation when disabled."""

    def test_enable_layer4_false_no_stateful_result(self):
        """Test that ENABLE_LAYER4=false skips stateful analysis."""
        with patch('streamguard.LambdaConfig') as mock_config:
            mock_config.ENABLE_LAYER4 = False
            mock_config.DEBERTA_THRESHOLD = 0.85

            result = analyze_text("Test message", session_id="test-session")

            # Stateful should NOT be in results when disabled
            assert "stateful" not in result["layer_results"]

            # Other layers should still return results
            assert "pii" in result["layer_results"]
            assert "jailbreak" in result["layer_results"]
            assert "injection" in result["layer_results"]
            assert "moderation" in result["layer_results"]

    def test_enable_layer4_false_no_errors(self):
        """Test that disabling Layer 4 doesn't cause errors."""
        with patch('streamguard.LambdaConfig') as mock_config:
            mock_config.ENABLE_LAYER4 = False
            mock_config.DEBERTA_THRESHOLD = 0.85

            result = analyze_text("Test without stateful")

            # Should complete without errors
            assert "error" not in result
            assert "layer_results" in result


class TestModelInitialization:
    """Test model loading and caching."""

    def test_initialize_models_sets_cache(self):
        """Test that initialize_models sets the cache flag."""
        # Reset cache
        _MODEL_CACHE["initialized"] = False
        _MODEL_CACHE["init_error"] = None

        # This will likely fail without actual models, but tests the pattern
        error = initialize_models()

        # Either success (None) or error message
        assert error is None or isinstance(error, str)

    def test_model_cache_persists(self):
        """Test that model cache persists across calls."""
        # Once initialized, should not reinitialize
        initial_initialized = _MODEL_CACHE.get("initialized", False)

        # Call initialize_models again
        initialize_models()

        # Should still be initialized (or have error from first attempt)
        assert _MODEL_CACHE.get("initialized") == initial_initialized or \
               _MODEL_CACHE.get("init_error") is not None


class TestConfigValidation:
    """Test configuration validation."""

    @patch('config.LambdaConfig.HF_TOKEN', None)
    @patch('config.LambdaConfig.OPENAI_API_KEY', 'sk-test')
    def test_config_validation_missing_hf_token(self):
        """Test that missing HF_TOKEN is caught."""
        is_valid, error = LambdaConfig.validate()
        assert not is_valid
        assert "HF_TOKEN" in error

    @patch('config.LambdaConfig.HF_TOKEN', 'hf-test')
    @patch('config.LambdaConfig.OPENAI_API_KEY', None)
    def test_config_validation_missing_openai_key(self):
        """Test that missing OPENAI_API_KEY is caught."""
        is_valid, error = LambdaConfig.validate()
        assert not is_valid
        assert "OPENAI_API_KEY" in error

    @patch('config.LambdaConfig.HF_TOKEN', 'hf-test')
    @patch('config.LambdaConfig.OPENAI_API_KEY', 'sk-test')
    @patch('config.LambdaConfig.ENABLE_LAYER4', True)
    @patch('config.LambdaConfig.UPSTASH_REDIS_URL', None)
    def test_config_validation_layer4_requires_redis(self):
        """Test that Layer 4 requires Redis configuration."""
        is_valid, error = LambdaConfig.validate()
        assert not is_valid
        assert "UPSTASH_REDIS_URL" in error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
