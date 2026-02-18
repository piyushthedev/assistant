import google.generativeai as genai
import os

# API Key provided by user
GENAI_API_KEY = "AIzaSyAuBUzpaapW8zvymcTRWBhC_6P1ytzK8VA"

print(f"Configuring Gemini with key: {GENAI_API_KEY[:5]}...")

try:
    genai.configure(api_key=GENAI_API_KEY)
    print("Listing available models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
            
    models_to_try = [
        'gemini-flash-latest',
        'gemini-pro-latest',
        'gemini-2.0-flash-lite',
        'gemini-1.5-flash',
        'gemini-1.5-pro'
    ]
    
    for model_name in models_to_try:
        print(f"\nAttempting with '{model_name}'...")
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Hello")
            print(f"SUCCESS with {model_name}!")
            print("Response:", response.text)
            break # Stop after first success
        except Exception as e:
            print(f"FAILED {model_name}: {e}")

except Exception as e:
    print("\nERROR:")
    print(e)
