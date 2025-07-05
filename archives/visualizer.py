import customtkinter as ctk
import numpy as np
import sounddevice as sd
import threading
import queue
import logging

class AudioVisualizer:
    """
    Manages a live audio visualizer on a CTkCanvas widget.
    It runs a non-blocking audio stream in a separate thread and updates
    the canvas with animated bars representing audio levels.
    """
    def __init__(self, parent_app, canvas: ctk.CTkCanvas):
        self.parent_app = parent_app
        self.canvas = canvas
        self.input_device_index: int | None = None
        
        self._stream: sd.InputStream | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._audio_queue = queue.Queue()
        self.update_loop_id: str | None = None

        self.num_bars = 20
        self.bar_width = 0
        self.spacing = 0
        self.canvas.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        """Recalculate bar widths when canvas is resized."""
        canvas_width = event.width
        self.bar_width = canvas_width / self.num_bars
        self.spacing = self.bar_width * 0.3

    def start(self, device_index: int):
        """
        Starts the audio visualization. If it's already running, it will
        stop the old stream and start a new one with the specified device.
        """
        if self._stream is not None:
            self.stop()

        self.input_device_index = device_index
        self._stop_event.clear()

        try:
            self._thread = threading.Thread(target=self._run, name="AudioVisualizerThread")
            self._thread.start()
            self.parent_app.after(50, self._update_canvas)
            logging.info(f"Audio visualizer started on device index {device_index}.")
        except Exception as e:
            logging.error(f"Failed to start audio visualizer: {e}")

    def stop(self):
        """Stops the audio visualization and cleans up resources."""
        if self._thread is None:
            return
            
        logging.info("Stopping audio visualizer...")
        self._stop_event.set()
        
        # Safely cancel the Tkinter update loop
        if self.update_loop_id:
            self.parent_app.after_cancel(self.update_loop_id)
            self.update_loop_id = None
            
        # Wait for the thread to finish
        if self._thread.is_alive():
            self._thread.join(timeout=1)
            
        self._stream = None
        self._thread = None
        # Safely clear the canvas
        if self.canvas.winfo_exists():
            self.canvas.delete("all")
        logging.info("Audio visualizer stopped.")

    def _run(self):
        """The main loop for the audio streaming thread."""
        def audio_callback(indata, frames, time, status):
            if status:
                logging.warning(f"Audio stream status: {status}")
            
            # Simple volume calculation
            volume_norm = np.linalg.norm(indata) * 10
            
            # Split audio into chunks for each bar
            samples_per_bar = len(indata) // self.num_bars
            levels = []
            for i in range(self.num_bars):
                start = i * samples_per_bar
                end = start + samples_per_bar
                chunk = indata[start:end]
                level = np.linalg.norm(chunk) * 12 # Amplify for visibility
                levels.append(min(int(level), 100))
                
            self._audio_queue.put(levels)

        try:
            with sd.InputStream(
                device=self.input_device_index,
                channels=1,
                samplerate=16000,
                blocksize=1024, # Larger blocksize for more detail
                dtype='float32',
                callback=audio_callback
            ) as stream:
                self._stream = stream
                self._stop_event.wait() # Keep the stream alive until stop is called
        except Exception as e:
            logging.error(f"Error in audio visualizer stream: {e}", exc_info=True)
            # Signal the UI thread to stop trying to update
            self._audio_queue.put(None)

    def _update_canvas(self):
        """Periodically reads the audio queue and redraws the visualizer bars on the UI thread."""
        # If the stop event is set or the canvas is gone, halt the loop.
        if self._stop_event.is_set() or not self.canvas.winfo_exists():
            return
            
        try:
            levels = self._audio_queue.get_nowait()
            if levels is None: # Sentinel value to stop updates on error
                self.stop()
                return
        except queue.Empty:
            levels = [0] * self.num_bars # Draw flat bars if queue is empty
        except Exception: # Catch any other error during queue access
            return
        
        try:
            self.canvas.delete("all")
            canvas_height = self.canvas.winfo_height()
            
            for i, level in enumerate(levels):
                # Make the center bars react more
                distance_from_center = abs(i - self.num_bars / 2)
                dampening = 1 - (distance_from_center / (self.num_bars / 2)) * 0.5
                bar_height = max(2, (level / 100) * (canvas_height * 0.95) * dampening)
                
                x0 = i * self.bar_width + self.spacing / 2
                y0 = canvas_height - bar_height
                x1 = (i + 1) * self.bar_width - self.spacing / 2
                y1 = canvas_height
                
                # Draw rounded rectangle
                self.canvas.create_rectangle(x0, y0, x1, y1, fill="white", outline="")
        except Exception as e:
            # This can happen if the canvas is destroyed mid-update.
            logging.warning(f"Could not update visualizer canvas: {e}")
            return
            
        self.update_loop_id = self.parent_app.after(50, self._update_canvas) 