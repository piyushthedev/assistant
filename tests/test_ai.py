import ai_service
print("Testing AI Service...")
try:
    response = ai_service.get_response("Hello, who are you?")
    print(f"Response: {response}")
except Exception as e:
    print(f"FAILED: {e}")
