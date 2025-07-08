import os
import requests
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

# --- 1. ENV CHECK ---
print("🔍 Checking GROQ_API_KEY in environment...")
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise EnvironmentError("❌ GROQ_API_KEY not found in environment. Check your `.env` file.")

print("✅ GROQ_API_KEY found.")

# --- 2. ENDPOINT CHECK ---
api_url = "https://api.groq.com/openai/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# --- 3. MODEL CHECK ---
model = "mixtral-8x7b-32768"
print(f"🔍 Using model: {model}")

# --- 4. SEND TEST REQUEST ---
print("🚀 Sending test request to Groq API...")
payload = {
    "model": model,
    "messages": [
        {"role": "system", "content": "You are a Bible verse extractor."},
        {"role": "user", "content": "God so loved the world that he gave his one and only son"}
    ],
    "temperature": 0.3
}

try:
    res = requests.post(api_url, headers=headers, json=payload)
    res.raise_for_status()
    print("✅ API responded successfully.")
    print("🧠 Response content:")
    print(res.json()["choices"][0]["message"]["content"])
except requests.exceptions.RequestException as e:
    print("❌ API request failed.")
    print("Details:", e)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    # Also print the raw response if available
    if 'res' in locals() and res:
        print("Raw response text:", res.text) 