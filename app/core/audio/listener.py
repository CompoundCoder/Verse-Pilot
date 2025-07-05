import logging
import queue
import threading
import os
import time
import collections
import numpy as np
import json

import sounddevice as sd
from vosk import Model, KaldiRecognizer
import whisper
from typing import Optional, Deque, List, Dict

from app.core.nlp.verse_parser import parse_verse_from_text

# --- Configuration ---
SAMPLE_RATE = 16000
CHANNELS = 1
VOSK_MODEL_PATH = "vosk-model-small-en-us-0.15"
WHISPER_MODEL_NAME = "tiny.en"
AUDIO_BUFFER_SECONDS = 5  # Shorter buffer for faster processing
COOLDOWN_SECONDS = 3  # Prevent overlapping transcription attempts

class VerseListener:
    """
    Handles continuous audio listening and verse detection in a non-blocking way.
    """
    def __init__(self):
        self._listener_thread: Optional[threading.Thread] = None
        self._transcription_thread: Optional[threading.Thread] = None
        self._running = threading.Event() # Use an event to signal stop
        self._audio_queue = queue.Queue()
        self.verse_queue: Optional[queue.Queue] = None
        self.input_device_index: Optional[int] = None
        
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
        self._stream = None
        self._listener_thread = None
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
        self._transcription_thread = threading.Thread(
            target=self._transcribe_and_process,
            args=(audio_snapshot, confidence),
            name="WhisperTranscriptionThread"
        )
        self._transcription_thread.start()

    def _transcribe_and_process(self, audio_data_bytes, confidence: float):
        """
        Transcribes audio and queues verse data.
        Adds validation to skip invalid verses (e.g. non-existent chapters).
        """
        try:
            self.last_detection_time = time.time()
            
            full_audio_np = np.frombuffer(b"".join(audio_data_bytes), dtype=np.int16)
            full_audio_fp32 = full_audio_np.astype(np.float32) / 32768.0
    
            result = self.whisper_model.transcribe(full_audio_fp32)
            text = result.get("text", "").strip()
    
            if not text:
                return
    
            logging.info(f"🗣️ Whisper Transcription: '{text}'")
    
            verse_list = parse_verse_from_text(text)
    
            if not verse_list:
                logging.warning(f"⚠️ Verse not found or empty: {text}")
                return
    
            # Store full list for possible future use
            self._last_verses = verse_list
            logging.info(f"✅ Parsed {len(verse_list)} verse(s)")
    
            # Only use the last verse, but validate it first
            last_verse = verse_list[-1]
            if (
                isinstance(last_verse, dict)
                and isinstance(last_verse.get("book"), str)
                and isinstance(last_verse.get("chapter"), int)
                and (
                    last_verse.get("verse") is None
                    or isinstance(last_verse.get("verse"), int)
                )
            ):
                last_verse["confidence"] = confidence
                self.verse_queue.put(last_verse)
                logging.info(f"📥 Queued verse: {last_verse}")
            else:
                logging.warning(f"❌ Skipping invalid verse format: {last_verse}")
    
        except Exception as e:
            logging.error(f"Error during transcription: {e}", exc_info=True)
        finally:
            self._transcription_thread = None

# Standalone test block removed for clarity in this context,
# but can be added back if needed for direct testing.
