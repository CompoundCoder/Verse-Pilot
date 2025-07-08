import logging
import json
import os
from app.core.ai.detectors.base_detector import BaseDetector

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

class LocalDeepSeekDetector(BaseDetector):
    def __init__(self):
        logging.info("LocalDeepSeekDetector is currently disabled.")

    def detect(self, transcript: str) -> dict:
        raise NotImplementedError("LocalDeepSeekDetector is disabled in this build.")

    @property
    def is_available(self) -> bool:
        """This detector is temporarily disabled."""
        return False

    def _build_prompt(self, transcript: str) -> str:
        # This prompt structure is common for instruction-following models.
        return f"""### Instruction
You are an expert Bible verse detector inside a live transcription application. Your only job is to analyze the provided transcript and determine the Bible verse being referenced.

Respond ONLY with a JSON object in the format:
{{"book": "...", "chapter": "...", "verse": "..."}}

If no verse is detected, respond with:
{{"book": null, "chapter": null, "verse": null}}

Transcript:
"{transcript}"

### Response
"""

    def _parse_response(self, raw_text: str) -> dict:
        try:
            # Clean up potential markdown code blocks
            clean_text = raw_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_text)
            
            # Validate structure
            if isinstance(data, dict) and all(k in data for k in ["book", "chapter", "verse"]):
                # Return empty if book is null, signifying no verse found.
                if data["book"] is None:
                    return {}
                
                return {
                    "book": str(data["book"]).strip(),
                    "chapter": int(data["chapter"]),
                    "verse": int(data["verse"]),
                }
            else:
                logging.warning(f"Local AI returned JSON with incorrect structure: {clean_text}")

        except json.JSONDecodeError:
            logging.warning(f"Local AI returned a non-JSON response: '{raw_text}'")
        except (ValueError, TypeError) as e:
            logging.warning(f"Error parsing data from local AI response '{raw_text}': {e}")
        
        return {} # Fallback for any parsing failure 