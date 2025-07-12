print("Testing ADK imports...")

try:
    from google.adk.agents import LlmAgent
    print("✓ LlmAgent imported successfully")
except ImportError as e:
    print(f"✗ Could not import LlmAgent: {e}")

try:
    from google.adk.sessions import InMemorySessionService
    print("✓ InMemorySessionService imported successfully")
except ImportError as e:
    print(f"✗ Could not import InMemorySessionService: {e}")

try:
    from google.adk.runners import Runner
    print("✓ Runner imported successfully")
except ImportError as e:
    print(f"✗ Could not import Runner: {e}")

try:
    from google.adk.tools import google_search
    print("✓ google_search imported successfully")
except ImportError as e:
    print(f"✗ Could not import google_search: {e}")

print("\nTest complete!")