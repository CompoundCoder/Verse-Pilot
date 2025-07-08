from app.core.ai.detectors.base_detector import BaseDetector
import requests
import json
import os
import logging
import time
from dotenv import load_dotenv

# Load .env file if present, making environment variables available
load_dotenv()

# Read API key from environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class OnlineGroqDetector(BaseDetector):
    """
    Handles verse detection by making API calls to the Groq cloud platform.
    It includes retry logic and robust response validation.
    """
    API_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, retries=2, timeout=10):
        """
        Initializes the detector, checks for API key, and sets up a session.
        """
        self.api_key = GROQ_API_KEY
        self.model = os.getenv("GROQ_MODEL_ID", "llama3-8b-8192") # Fallback default
        self.retries = retries
        self.timeout = timeout
        self.session = requests.Session()
        
        if not self.api_key:
            self.available = False
            logging.warning("[OnlineGroqDetector] Not available: GROQ_API_KEY is missing from .env file.")
        else:
            self.available = True
            self.session.headers.update({
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            })
            logging.info(f"[OnlineGroqDetector] Initialized successfully with model '{self.model}'.")

    def is_available(self):
        """Returns True if the detector is configured and ready to use."""
        return self.available

    def _validate_response(self, response_text):
        """Parses and validates that the response is a JSON object with the required keys."""
        try:
            data = json.loads(response_text)
            if isinstance(data, dict) and "book" in data and "chapter" in data:
                # Fallback to verse 1 if the 'verse' key is missing from the response.
                data.setdefault("verse", 1)
                logging.info(f"[OnlineGroqDetector] ✅ Valid JSON response received: {data}")
                return data
            else:
                logging.warning(f"[OnlineGroqDetector] ⚠️ Invalid JSON structure: {response_text}")
                return None
        except json.JSONDecodeError:
            logging.error(f"[OnlineGroqDetector] ❌ Failed to decode JSON: {response_text}")
            return None

    def detect(self, transcript_text: str):
        """
        Sends the transcript to the Groq API and attempts to get a structured verse.
        
        Args:
            transcript_text (str): The user's spoken text.

        Returns:
            dict or None: A dictionary with 'book', 'chapter', 'verse' if successful, otherwise None.
        """
        if not self.is_available():
            # This should not be called if not available, but as a safeguard:
            logging.error("[OnlineGroqDetector] Detect called but service is not available.")
            return None

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a Bible verse extraction assistant.\n\n"
                        "Your job is to extract a single verse reference from natural English sentences. "
                        "Respond ONLY with a valid JSON object like this:\n\n"
                        '{ "book": "Matthew", "chapter": 5, "verse": 14 }\n\n'
                        "You MUST only respond with this JSON object. Do NOT include any explanation, "
                        "preamble, or extra fields.\n\n"
                        "Support informal variations like:\n"
                        "- 'we're in Matthew 5 verse 14'\n"
                        "- 'let's go to John 3 16'\n"
                        "- 'Exodus chapter 4 verse 3'\n"
                        "- 'now turn to Luke 1:35'\n\n"
                        "If there is no clear verse reference, respond with null."
                    )
                },
                {
                    "role": "user",
                    "content": transcript_text
                }
            ],
            "temperature": 0.0,
            "response_format": {"type": "json_object"}, # Request structured JSON output
        }
        
        logging.info(f"[OnlineGroqDetector] 🧠 Sending prompt for transcript: \"{transcript_text}\"")
        print(f"🌐 [Groq] Sending to model: {self.model}")
        print(f"🧠 [Prompt Payload] {json.dumps(payload, indent=2)}")

        for attempt in range(self.retries):
            try:
                response = self.session.post(
                    self.API_URL,
                    json=payload,
                    timeout=self.timeout
                )
                print(f"📡 [Groq Response Raw] {response.status_code} {response.text}")
                response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)

                try:
                    # The API returns the JSON as a string inside the 'content' field
                    content_str = response.json().get("choices", [{}])[0].get("message", {}).get("content")
                    if not content_str:
                        logging.warning("[OnlineGroqDetector] ⚠️ API returned an empty message content.")
                        continue # Try again
                    
                    print(f"[DEBUG] Raw content string: {content_str}")
                    parsed = json.loads(content_str)
                    if isinstance(parsed, dict) and "book" in parsed:
                        print(f"✅ [Groq Parsed Response] {parsed}")
                        return parsed
                    
                    logging.warning(f"[OnlineGroqDetector] Parsed data is not a valid verse object: {parsed}")
                    return None # Don't retry if we got a valid-but-wrong response
                except (json.JSONDecodeError, KeyError, IndexError) as e:
                    logging.warning(f"[OnlineGroqDetector] Failed to parse response content on attempt {attempt + 1}: {e}")
                    # Let it retry if parsing fails

            except requests.exceptions.HTTPError as e:
                logging.error(f"[OnlineGroqDetector] HTTP Error on attempt {attempt + 1}/{self.retries}: {e.response.status_code} - {e.response.text}")
            except requests.exceptions.RequestException as e:
                logging.error(f"[OnlineGroqDetector] Request failed on attempt {attempt + 1}/{self.retries}: {e}")

            if attempt < self.retries - 1:
                sleep_time = 2 ** attempt  # Exponential backoff: 1s, 2s
                logging.info(f"[OnlineGroqDetector] Retrying in {sleep_time} second(s)...")
                time.sleep(sleep_time)

        logging.error(f"[OnlineGroqDetector] ❌ All {self.retries} attempts failed for transcript: \"{transcript_text}\"")
        return None 