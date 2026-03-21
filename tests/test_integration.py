"""
Simple integration test to verify StreamGuard library works.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from streamguard import analyze_text


def test_simple_invoke():
    """Test a simple library invocation."""
    print("\n" + "="*60)
    print("Testing StreamGuard Library with simple input...")
    print("="*60)

    try:
        result = analyze_text("Hello, world!")

        # Check for handler-level errors
        if 'error' in result:
            print(f"\n[FAIL] Library error: {result['error']}")
            return False

        print("\n[PASS] StreamGuard Library executed successfully!")
        print(f"\nLatency: {result.get('latency_ms', 'N/A')}ms")
        print(f"\nLayer Results:")

        # Check each layer for errors
        layers = result.get('layer_results', {})
        for layer, data in layers.items():
            print(f"  - {layer}: {type(data).__name__}")
            # Check if layer has an error field
            if isinstance(data, dict) and data.get('error'):
                print(f"    [ERROR] {data['error']}")

        # Check that we got results
        assert 'layer_results' in result, "Missing layer_results"
        assert 'latency_ms' in result, "Missing latency_ms"

        # Check main layers are present
        assert 'pii' in layers, "Missing PII layer"
        assert 'jailbreak' in layers, "Missing jailbreak layer"
        assert 'injection' in layers, "Missing injection layer"
        assert 'moderation' in layers, "Missing moderation layer"

        # Check for errors in any layer
        for layer_name, layer_data in layers.items():
            if isinstance(layer_data, dict) and layer_data.get('error'):
                print(f"\n[FAIL] {layer_name} has errors: {layer_data['error']}")
                return False

        print("\n[PASS] All checks passed!")
        return True

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_with_session_id():
    """Test StreamGuard library with session_id (Layer 4)."""
    print("\n" + "="*60)
    print("Testing StreamGuard Library with session_id...")
    print("="*60)

    try:
        result = analyze_text(
            text="This is a test message",
            session_id="test-session-123",
            agent_id="test-agent",
            direction="input"
        )

        print("\n[PASS] StreamGuard Library executed successfully!")
        print(f"\nLatency: {result.get('latency_ms', 'N/A')}ms")

        # Check if stateful layer ran
        if 'stateful' in result.get('layer_results', {}):
            print("\n[INFO] Stateful layer executed!")
            stateful = result['layer_results']['stateful']
            print(f"  Analyzed: {stateful.get('analyzed', False)}")

            # Check for errors in stateful layer
            if stateful.get('error'):
                print(f"  [ERROR] Stateful layer error: {stateful['error']}")
                print(f"\n[FAIL] Stateful layer has errors!")
                return False

            # If analyzed=False but no error, it's expected (insufficient history)
            if not stateful.get('analyzed'):
                print(f"  [INFO] Not analyzed (insufficient history - expected for first message)")
            else:
                print(f"  [PASS] Full analysis completed!")
                print(f"  Risk Score: {stateful.get('risk_score', 'N/A')}")
                patterns = stateful.get('patterns_detected', [])
                if patterns:
                    print(f"  Patterns Detected: {patterns}")
                print(f"  Explanation: {stateful.get('explanation', 'N/A')[:100]}...")
        else:
            print("\n[WARN] Stateful layer not in results (may be disabled)")

        return True

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("StreamGuard Library - Integration Tests")
    print("="*60)

    # Run simple test first
    success1 = test_simple_invoke()

    # Run session_id test
    success2 = test_with_session_id()

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Simple Invoke: {'[PASS]' if success1 else '[FAIL]'}")
    print(f"Session ID Test: {'[PASS]' if success2 else '[FAIL]'}")
    print("="*60 + "\n")
