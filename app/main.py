import os
import sys
import json
import logging
import queue
import threading
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import whisper

# --- Configuration ---
LOG_LEVEL = logging.INFO
SAMPLE_RATE = 16000
DEVICE = None # Use default device
CHANNELS = 1
VOSK_MODEL_PATH = "vosk-model-small-en-us-0.15" # Download from https://alphacephei.com/vosk/models
WHISPER_MODEL_NAME = "tiny.en" # Or "base.en", "small.en", etc.
KEYWORD = "verse" # The keyword to trigger transcription

# --- Setup Logging ---
logging.basicConfig(level=LOG_LEVEL,
                    format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s')

# --- Placeholder Functions (to be modularized) ---

def parse_verse_reference(text: str) -> str | None:
    """
    Extracts a Bible verse reference from text using regex or a local LLM.
    
    For now, this is a simple placeholder. A robust implementation would use
    a library like `python-bible` or more advanced regex.
    """
    import re
    # This regex is basic and will need improvement.
    # It looks for patterns like "Book Chapter:Verse" or "Book Chapter Verse".
    pattern = r"\b(1\s?[A-Za-z]+|2\s?[A-Za-z]+|3\s?[A-Za-z]+|[A-Za-z]+)\s+(\d{1,3})(?::(\d{1,3}))?\b"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        book = match.group(1).strip()
        chapter = match.group(2)
        verse = match.group(3) if match.group(3) else "1"
        return f"{book.title()} {chapter}:{verse}"
    return None

def process_final_result(result_text: str):
    """
_    Processes the final transcription result to find a verse.
    """
    logging.info(f"Full Transcription: \"{result_text}\"")
    
    # Check if the keyword is in the transcription
    if KEYWORD in result_text.lower():
        logging.info("Keyword detected. Looking for verse reference...")
        verse_ref = parse_verse_reference(result_text)
        if verse_ref:
            logging.info(f"--- Detected: {verse_ref} ---")
            # In the future, this would trigger rendering and output.
        else:
            logging.warning("Keyword detected, but no verse reference found.")

# --- Core Application Logic ---

class AudioProcessor:
    def __init__(self):
        self.running = threading.Event()
        self.running.set()
        self.q = queue.Queue()
        
        # Check for VOSK model
        if not os.path.exists(VOSK_MODEL_PATH):
            logging.error(f"Vosk model not found at '{VOSK_MODEL_PATH}'.")
            logging.error("Please download the model from https://alphacephei.com/vosk/models")
            sys.exit(1)
        
        self.vosk_model = Model(VOSK_MODEL_PATH)
        self.whisper_model = whisper.load_model(WHISPER_MODEL_NAME)
        logging.info("Models loaded successfully.")

    def audio_callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            logging.warning(status)
        self.q.put(bytes(indata))

    def start_listening(self):
        """Starts the main listening loop."""
        try:
            with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000,
                                   device=DEVICE, dtype='int16',
                                   channels=CHANNELS, callback=self.audio_callback):
                logging.info("Microphone listener started. Say 'verse' followed by a reference.")
                
                rec = KaldiRecognizer(self.vosk_model, SAMPLE_RATE)
                while self.running.is_set():
                    data = self.q.get()
                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        if result.get('text'):
                            # Using a separate thread to not block the audio stream
                            threading.Thread(target=process_final_result, args=(result['text'],)).start()
                    else:
                        partial_result = json.loads(rec.PartialResult())
                        if partial_result.get('partial'):
                            print(f"Partial: {partial_result['partial']}", end='\r')

        except Exception as e:
            logging.error(f"An error occurred in the listening loop: {e}")
        finally:
            logging.info("Listener stopped.")
            
    def stop(self):
        """Signals the listener to stop."""
        logging.info("Stopping listener...")
        self.running.clear()


def main():
    """Main function to run the application."""
    processor = AudioProcessor()
    
    # Run the listener in a separate thread
    listener_thread = threading.Thread(target=processor.start_listening, name="AudioListener")
    listener_thread.start()

    try:
        # Keep the main thread alive
        while listener_thread.is_alive():
            listener_thread.join(timeout=1.0)
    except KeyboardInterrupt:
        logging.info("Ctrl+C received. Shutting down...")
        processor.stop()
        listener_thread.join() # Wait for the listener to finish
    
    logging.info("Application shut down gracefully.")


if __name__ == "__main__":
    main()
