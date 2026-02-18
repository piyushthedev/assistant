import ai_service
import sys
import time

print("Initializing Broklin...")
# Test 1: Basic Chat
print("\n--- Test 1: Basic Chat ---")
input1 = "Hello, my name is Solu."
print(f"User: {input1}")
response1 = ai_service.get_response(input1)
print(f"Broklin: {response1}")

# Test 2: Memory
print("\n--- Test 2: Memory Check ---")
input2 = "What is my name?"
print(f"User: {input2}")
response2 = ai_service.get_response(input2)
print(f"Broklin: {response2}")

if "Solu" in response2:
    print("\n✅ SUCCESS: Broklin remembered the name!")
else:
    print("\n❌ FAILURE: Broklin forgot the name.")
