import re
import logging
import subprocess
import json
from typing import Optional, Tuple, List, Dict
import ollama

# --- Configuration ---
# Specifies the Ollama model to be used for AI-based parsing.
# 'mistral' is chosen for its strong instruction-following capabilities.
OLLAMA_MODEL = "mistral"
# Sets a timeout for the Ollama process to prevent the application from
# hanging indefinitely if the local AI model is unresponsive.
OLLAMA_TIMEOUT = 15 # seconds

# --- Setup logging ---
log = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a Bible verse extraction engine. Your ONLY job is to return Bible references "
    "in the form of proper JSON objects. Do NOT return lists of strings. "
    "Only output a JSON list like this:\n"
    '[{"book": "Genesis", "chapter": 1, "verse": 1}]\n'
    "Always include keys: book (string), chapter (int), and verse (int or null).\n"
    "Do NOT reference previous context. You are stateless."
)

def _parse_with_regex(text: str) -> Optional[Tuple[str, int, int]]:
    """
    Fallback function to extract a Bible verse reference using regular expressions.

    This function serves as a reliable backup if the AI parser fails. It's
    less flexible than the AI but provides a deterministic way to find
    common verse formats.
    """
    # This regex is designed to capture common Bible reference patterns, including
    # books with numbered prefixes (e.g., "1 John").
    # \b - word boundary, to avoid matching parts of words.
    # (1\s?[A-Za-z]+|...) - Captures book names like "John" or "1 Corinthians".
    # \s+ - Matches the space between book and chapter.
    # (\d{1,3}) - Captures the chapter number.
    # (?:[:\s,]+(\d{1,3}))? - Optionally captures the verse number after a separator.
    pattern = r"\b(1\s?[A-Za-z]+|2\s?[A-Za-z]+|3\s?[A-Za-z]+|[A-Za-z]+)\s+(\d{1,3})(?:[:\s,]+(\d{1,3}))?\b"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        book = match.group(1).strip().title()
        chapter = int(match.group(2))
        # If no verse is explicitly mentioned, it defaults to verse 1,
        # which is a common way to refer to the start of a chapter.
        verse = int(match.group(3)) if match.group(3) else 1
        return book, chapter, verse
    return None

def parse_verse_from_text(text: str) -> List[Dict]:
    try:
        log.info(f"Asking LLM to parse: '{text}'")
        response_data = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': text},
            ],
            options={'temperature': 0.0}
        )
        
        response = response_data['message']['content']

        # Save full response to a local log file for debugging
        with open("versepilot_ai_log.txt", "a") as f:
            f.write(f"---\nTRANSCRIBED: {text}\nRAW_RESPONSE: {response}\n")

        # Use regex to extract all full JSON object blocks
        matches = re.findall(r'\{.*?\}', response)
        if not matches:
            log.warning(f"No valid JSON objects found in Ollama response: {response}")
            return []

        # Wrap them in brackets and parse
        json_string = f"[{','.join(matches)}]"
        parsed_data = json.loads(json_string)
        
        if not isinstance(parsed_data, list):
            log.warning(f"Parsed JSON is not a list, but {type(parsed_data)}")
            return []

        log.info(f"Successfully parsed {len(parsed_data)} verse(s) from LLM response.")
        return parsed_data

    except ollama.ResponseError as e:
        log.error(f"Ollama API error: {e.error}")
        if "model not found" in e.error:
            log.error(f"The '{OLLAMA_MODEL}' model is not available. Please run 'ollama pull {OLLAMA_MODEL}'")
        return []
    except Exception as e:
        log.error(f"Error parsing verse JSON: {e}", exc_info=True)
        return []


if __name__ == '__main__':
    # This block allows for standalone testing of the parser module.
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    print("--- Testing AI-Powered Verse Parser ---")
    
    # Ensure Ollama is running before testing: `ollama run deepseek-coder`
    tests = [
        "Could you please turn to the book of John, chapter 3, verse 16?",
        "Let's read from romans 8 28 together",
        "My favorite is 1st Corinthians 13 verse 4.",
        "Now for Genesis 1:1 and exodus 1 2.",
        "The speaker said, and I quote: 'the verse is John 3:16'",
        "Sure, here you go! {'book': 'Romans', 'chapter': 8, 'verse': 28}. Let me know if you need another.",
        "The speaker is just talking normally without a reference.",
        "Please show me Matthew chapter 6 verses 9 through 13.", # Note: current LLM prompt doesn't handle ranges well
    ]
    
    for t in tests:
        result = parse_verse_from_text(t)
        print(f"'{t}' -> {result if result else 'Not Found'}")
        print("-" * 20)
