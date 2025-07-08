import os
import requests
import uuid
import json
from datetime import datetime
from typing import Optional, List
from dotenv import load_dotenv
from app.core.verse_buffer import VerseCandidate
from app.core.bible.constants import BOOK_TO_NUM_CHAPTERS
import logging

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


def prompt_template(transcript: str, context: str = "", last_book: Optional[str] = None, last_chapter: Optional[int] = None) -> str:
    return f"""
You are a Bible verse identifier and validator.

Read the transcript and identify any clearly referenced verses. Return only verse(s) that are either:
- Directly mentioned (e.g., "Matthew chapter 2 verse 3")
- Partially referenced (e.g., "verse 5") AND context or state fills in the missing part

Context:
"{context.strip()}"
Previous confirmed verse:
"{last_book} {last_chapter}" if last_book else "Not available"

Only return verse(s) if the transcript mentions or implies one clearly.

Respond with one of the following:
- A list of JSON objects, each like:
  {{
    "book": "Matthew",
    "chapter": 2,
    "verse": 3,
    "certainty": 0.88,
    "explanation": "Transcript said 'verse 3' and context was Matthew 2"
  }}
- Or a single JSON object: {{ "review_required": true }}

DO NOT hallucinate. If no verse is mentioned, return review_required.

Transcript:
"{transcript.strip()}"
""".strip()

def is_known_book(book: str) -> bool:
    """Checks if a book exists in the canonical list."""
    return book in BOOK_TO_NUM_CHAPTERS

def is_valid_reference(book: str, chapter: int) -> bool:
    """Checks if a book and chapter exist in the canonical list."""
    # This assumes is_known_book was already checked.
    if chapter > BOOK_TO_NUM_CHAPTERS.get(book, 999):
        return False
    return True

def validate_with_gemini(transcript: str, context: str = "", last_book: str = "", last_chapter: int = 0) -> List[VerseCandidate]:
    if not GEMINI_API_KEY:
        print("[SlowValidator] Error: GEMINI_API_KEY not found in .env file.")
        return []

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY,
    }

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt_template(transcript, context, last_book, last_chapter)}]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
        }
    }

    response = requests.post(GEMINI_URL, headers=headers, json=payload)

    if response.status_code != 200:
        print(f"[SlowValidator] Error: {response.status_code} – {response.text}")
        return []

    try:
        res_json = response.json()
        text = res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print("[SlowValidator] Failed to parse Gemini response.")
        print("Raw response text:", response.text)
        print("Exception:", e)
        return []

    try:
        raw_data = res_json["candidates"][0]["content"]["parts"][0]["text"]
        if isinstance(raw_data, str):
            # Gemini sometimes returns JSON wrapped in triple backticks, like:
            # ```json ... ```
            cleaned = raw_data.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.removeprefix("```json").strip()
            if cleaned.endswith("```"):
                cleaned = cleaned.removesuffix("```").strip()

            try:
                raw_data = json.loads(cleaned)
            except json.JSONDecodeError as e:
                print("[SlowValidator] ⚠️ Could not decode cleaned JSON string")
                print("Raw (uncleaned):", raw_data)
                print("Exception:", e)
                return []

        if "review_required" in str(raw_data).lower():
            return []

        # Ensure we are working with a list
        if isinstance(raw_data, dict):
            raw_data = [raw_data]

        candidates = []
        for item in raw_data:
            book = item.get("book", "").title()
            chapter = int(item.get("chapter", 0))
            verse = int(item.get("verse", 0))

            # Skip if essential parts are missing
            if not all([book, chapter, verse]):
                continue

            # STEP 1: Hard check for canonical book names.
            if not is_known_book(book):
                logging.warning(f"Blocked hallucinated book: {book}")
                continue # Discard silently.

            # STEP 2: Book is known, now validate chapter.
            is_valid = is_valid_reference(book, chapter)
            validation_status = "valid"
            if not is_valid:
                validation_status = "invalid_chapter"
                logging.debug(f"[SlowValidator] Invalid chapter for {book}: {chapter}. Awaiting user confirmation.")

            certainty = float(item.get("certainty", 0.5))
            explanation = item.get("explanation", "No explanation provided")

            candidate = VerseCandidate(
                book=book,
                chapter=chapter,
                verse=verse,
                transcript_snippet=transcript,
                confidence_score=certainty,
                source="slow",
                status="pending",
                validation_status=validation_status,
                is_partial=False if certainty >= 0.8 else True,
                review_required=certainty < 0.8,
                explanation=explanation,
            )
            candidates.append(candidate)

        return candidates

    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as e:
        print(f"[SlowValidator] Failed to parse Gemini response text content: {e}")
        print(f"Content that failed to parse: {raw_data}")
        return [] 