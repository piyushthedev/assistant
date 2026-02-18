import sys
import os

# Add root directory to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import ai_service
from config import Config

print("Testing AI Service...")
try:
    # Test text response
    print("Testing text response...")
    response = ai_service.get_response("Hello, who are you?")
    print(f"AI Response: {response}")
    
    if response:
        print("✅ Text response test passed.")
    else:
        print("❌ Text response test failed (Empty response).")

except Exception as e:
    print(f"❌ AI Service test failed: {e}")

print("\nTesting Config...")
try:
    if Config.WAKE_WORD == "broklin":
        print("✅ Config load passed (WAKE_WORD=broklin).")
    else:
        print(f"❌ Config load failed (WAKE_WORD={Config.WAKE_WORD}).")
except Exception as e:
    print(f"❌ Config test failed: {e}")
