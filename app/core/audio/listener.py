import logging
import queue
import threading
import os
import time
import collections
import numpy as np
import json
import requests

import sounddevice as sd
from vosk import Model, KaldiRecognizer
import whisper
from typing import Optional, Deque, List, Dict
from app.core.bible.constants import TRIGGER_KEYWORDS, BIBLE_BOOKS, BOOK_TO_NUM_CHAPTERS, BOOK_VERSE_COUNTS
from PyQt6.QtCore import QObject, pyqtSignal

# --- New Pipeline Imports ---
from app.core.ai.fast_extractor import FastVerseExtractor
from app.core.ai.slow_validator import validate_with_gemini
from app.core.verse_buffer import VerseBuffer, VerseCandidate
from app.core.state_tracker import set_last_confirmed, get_last_confirmed

# This buffer will hold all candidates for potential future UI display
verse_buffer = VerseBuffer()

# --- Configuration ---
SAMPLE_RATE = 16000
CHANNELS = 1
VOSK_MODEL_PATH = "vosk-model-small-en-us-0.15"
WHISPER_MODEL_NAME = "tiny.en"
AUDIO_BUFFER_SECONDS = 5  # Shorter buffer for faster processing
COOLDOWN_SECONDS = 3  # Prevent overlapping transcription attempts

SYSTEM_PROMPT = """
You are a verse detection assistant embedded in a live audio transcription app.
When given raw English transcript text (from speech), your job is to:
1. Identify if it contains a reference to a Bible verse.
2. If it does, extract the verse's book name, chapter, and verse number.
3. Return ONLY a clean JSON object in this format:
   {"book": "John", "chapter": 1, "verse": 1}
4. If there is no verse present, return {"book": null, "chapter": null, "verse": null}.
Do not add any extra commentary. Do not guess. Be precise.
"""

class VerseListener(QObject):
    """
    Handles continuous audio listening and verse detection in a non-blocking way.
    """
    # Define a signal that will carry a dictionary (the verse data)
    verse_needs_confirmation = pyqtSignal(dict)

    def __init__(self, ai_available: bool = False, gemini_api_key: str = None, gemini_model_id: str = None):
        super().__init__()
        self._listener_thread: Optional[threading.Thread] = None
        self._transcription_thread: Optional[threading.Thread] = None
        self._running = threading.Event() # Use an event to signal stop
        self._audio_queue = queue.Queue()
        self.verse_queue: Optional[queue.Queue] = None
        self.input_device_index: Optional[int] = None
        
        # --- AI Configuration ---
        self.ai_available = ai_available
        self.gemini_api_key = gemini_api_key
        self.gemini_model_id = gemini_model_id

        # This will hold the audio stream object for safe shutdown.
        self._stream: Optional[sd.InputStream] = None
        
        # This will store the most recent full list of verses parsed.
        self._last_verses: Optional[List[Dict]] = None

        self.audio_buffer: Deque[bytes] = collections.deque(
            maxlen=int(SAMPLE_RATE * AUDIO_BUFFER_SECONDS / 512)
        )
        
        self.last_detection_time = 0
        self.vosk_model = self._load_vosk_model()
        self.whisper_model = self._load_whisper_model()
        self.last_processed_transcript = None

    def process_manual_transcript(self, transcript: str):
        """
        Manually triggers the verse detection pipeline with a given text transcript.
        This bypasses the audio-to-text stage and is useful for testing.
        """
        if self._transcription_thread and self._transcription_thread.is_alive():
            logging.warning("[Listener] A transcription is already in progress. Ignoring manual submission.")
            return
        
        # We run this in a thread to keep the UI from freezing while the AI runs.
        self._transcription_thread = threading.Thread(
            target=self._process_transcript_logic,
            args=(transcript,),
            name="ManualTranscriptionThread"
        )
        self._transcription_thread.start()

    def _load_vosk_model(self):
        if not os.path.exists(VOSK_MODEL_PATH):
            logging.error(f"Vosk model not found at '{VOSK_MODEL_PATH}'")
            return None
        return Model(VOSK_MODEL_PATH)

    def _load_whisper_model(self):
        try:
            logging.info(f"Loading Whisper model '{WHISPER_MODEL_NAME}'...")
            return whisper.load_model(WHISPER_MODEL_NAME)
        except Exception as e:
            logging.error(f"Failed to load Whisper model: {e}", exc_info=True)
            return None
    
    @property
    def models_loaded(self) -> bool:
        return self.vosk_model is not None and self.whisper_model is not None

    def start_listening(self, verse_queue: queue.Queue, input_device_index: Optional[int] = None):
        if self._running.is_set():
            return
        if not self.models_loaded:
            raise RuntimeError("Models not loaded")
        self.verse_queue = verse_queue
        self.input_device_index = input_device_index
        self._running.set()
        self._listener_thread = threading.Thread(target=self._run, name="VerseListenerThread")
        self._listener_thread.start()
        self.last_processed_transcript = None # Reset on start
        logging.info("Verse listener started.")

    def stop_listening(self):
        if not self._running.is_set():
            return
        self._running.clear()
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
                logging.info("Audio stream closed.")
            except Exception as e:
                logging.warning(f"Stream close error: {e}")
        self._audio_queue.put(None)
        if self._listener_thread and self._listener_thread.is_alive():
            self._listener_thread.join(timeout=5)
        
        if self._transcription_thread and self._transcription_thread.is_alive():
            logging.info("Waiting for active transcription to finish before shutdown...")
            self._transcription_thread.join(timeout=10)

        self._stream = None
        self._listener_thread = None
        self._transcription_thread = None
        logging.info("Verse listener stopped.")

    def is_listening(self) -> bool:
        return self._running.is_set()

    def _audio_callback(self, indata, frames, time, status):
        if status:
            logging.warning(f"Sounddevice status: {status}")
        self.audio_buffer.append(bytes(indata))
        self._audio_queue.put(bytes(indata))

    def _run(self):
        recognizer = KaldiRecognizer(self.vosk_model, SAMPLE_RATE)
        try:
            self._stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                blocksize=8000,
                device=self.input_device_index,
                dtype='int16',
                channels=CHANNELS,
                callback=self._audio_callback
            )
            self._stream.start()
            logging.info(f"Microphone stream started on device {self.input_device_index}")
            while self._running.is_set():
                data = self._audio_queue.get()
                if data is None:
                    break
                if recognizer.AcceptWaveform(data):
                    result_str = recognizer.Result()
                    try:
                        result_json = json.loads(result_str)
                        confidence = result_json.get("confidence", 0.0)
                        self._trigger_transcription_if_needed(confidence)
                    except json.JSONDecodeError:
                        logging.warning("Could not parse Vosk result JSON.")
                        self._trigger_transcription_if_needed(0.0)
                else:
                    recognizer.PartialResult()
        except Exception as e:
            logging.critical(f"Audio loop exception: {e}", exc_info=True)
        finally:
            logging.info("Listener thread exiting.")

    def _trigger_transcription_if_needed(self, confidence: float):
        if self._transcription_thread and self._transcription_thread.is_alive():
            return
        if time.time() - self.last_detection_time < COOLDOWN_SECONDS:
            return
        audio_snapshot = list(self.audio_buffer)
        self.audio_buffer.clear()
        self._transcription_thread = threading.Thread(
            target=self._transcribe_and_process,
            args=(audio_snapshot, confidence),
            name="WhisperTranscriptionThread"
        )
        self._transcription_thread.start()

    def _format_candidate_for_queue(self, candidate: VerseCandidate) -> dict:
        """Converts a VerseCandidate to the dict format expected by the UI queue."""
        return {
            "book": candidate.book,
            "chapter": candidate.chapter,
            "verse": candidate.verse,
            "reference": f"{candidate.book} {candidate.chapter}:{candidate.verse}",
            "raw_transcript": candidate.transcript_snippet,
            "confidence": candidate.confidence_score * 100,
            "source": candidate.source,
            "timestamp": candidate.timestamp.timestamp(),
            "explanation": candidate.explanation,
        }

    def _process_transcript_logic(self, transcript: str):
        """
        The core logic for processing a transcript, shared by both audio and manual input.
        """
        # --- FIX: Prevent re-processing the same utterance ---
        if transcript and transcript == self.last_processed_transcript:
            logging.warning(f"[Listener] Skipping duplicate transcript: \"{transcript}\"")
            return
        self.last_processed_transcript = transcript
        # --- END FIX ---
        
        print(f"📝 [Listener] Transcript ready for processing: \"{transcript}\"")

        # --- Start New Detection Pipeline ---
        # 1. Fast, local extraction
        candidate = FastVerseExtractor.extract_candidate(transcript)

        if candidate:
            # Always trust the fast extractor for now
            self.verse_queue.put(self._format_candidate_for_queue(candidate))
            verse_buffer.add_candidate(candidate)
        elif self.ai_available:
            # 2. Slow, cloud-based validation if fast fails
            last_book, last_chapter = get_last_confirmed()
            slow_candidates = validate_with_gemini(
                transcript, 
                api_key=self.gemini_api_key, 
                model_id=self.gemini_model_id,
                last_book=last_book, 
                last_chapter=last_chapter
            )

            # If no verse found, do nothing
            if not slow_candidates:
                logging.info(f"[Listener] Slow validator found no candidates in: \"{transcript}\"")
                return

            # 3. Queue the verse for the UI
            logging.info(f"✅ [Listener] Slow validator returned {len(slow_candidates)} candidates. Queueing...")
            for candidate in slow_candidates:
                if candidate.book not in BOOK_TO_NUM_CHAPTERS: continue
                if candidate.chapter > BOOK_TO_NUM_CHAPTERS[candidate.book]: continue
                if candidate.verse > BOOK_VERSE_COUNTS[candidate.book].get(candidate.chapter, 0): continue

                set_last_confirmed(candidate.book, candidate.chapter)
                verse_buffer.add_candidate(candidate)
                
                if candidate.review_required:
                    logging.info(f"Verse requires confirmation: {candidate.book} {candidate.chapter}:{candidate.verse}")
                    self.verse_needs_confirmation.emit(self._format_candidate_for_queue(candidate))
                else:
                    self.verse_queue.put(self._format_candidate_for_queue(candidate))


    def _transcribe_and_process(self, audio_data_bytes, confidence: float):
        """
        Transcribes audio and runs it through the fast/slow detection pipeline.
        """
        try:
            self.last_detection_time = time.time()
            
            # 1. Transcribe the raw audio bytes using the Whisper model
            print("🎤 [Listener] Starting transcription...")
            full_audio_np = np.frombuffer(b"".join(audio_data_bytes), dtype=np.int16)
            full_audio_fp32 = full_audio_np.astype(np.float32) / 32768.0
            
            result = self.whisper_model.transcribe(full_audio_fp32, language="en")
            transcript = result.get("text", "").strip()

            # The core processing logic is now in a separate method
            self._process_transcript_logic(transcript)

        except Exception as e:
            logging.error(f"Error in transcription/processing: {e}", exc_info=True)
        finally:
            self._transcription_thread = None

# Standalone test block removed for clarity in this context,
# but can be added back if needed for direct testing.
