"""
Simple local test for StreamGuard security library
"""
import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from streamguard import analyze_text

def test_simple():
    """Simple test to see what the library returns"""
    print("\n" + "="*60)
    print("Testing StreamGuard Library Locally")
    print("="*60)

    # Test using the new simplified API
    text = "Hello, this is a test message"
    session_id = "test-session-123"
    agent_id = "test-agent"
    direction = "input"

    print(f"\nInput text: {text}")
    print(f"Session ID: {session_id}")
    print(f"Agent ID: {agent_id}")
    print(f"Direction: {direction}")
    print("\nCalling analyze_text...")

    result = analyze_text(text, session_id, agent_id, direction)

    print("\n" + "="*60)
    print("RESULT:")
    print("="*60)
    print(json.dumps(result, indent=2))

    return result

if __name__ == "__main__":
    try:
        result = test_simple()
        print("\n[SUCCESS] Test completed successfully!")
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
