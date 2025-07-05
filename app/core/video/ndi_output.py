import logging
import threading
import time
import os
import numpy as np
from PIL import Image, ImageDraw
from typing import Optional

try:
    import NDIlib as ndi
except ImportError:
    print("Error: NDIlib library not found.")
    print("Please install the NDI SDK and the 'ndi-python' package.")
    print("pip install ndi-python")
    ndi = None

# --- Configuration ---
NDI_WIDTH = 1280
NDI_HEIGHT = 720
NDI_FRAME_RATE = 30

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s')

class NDIOutput:
    """
    Manages a dedicated NDI output stream on a background thread.
    This ensures a stable FPS output for receivers like ProPresenter.
    """

    def __init__(self, source_name: str = "VersePilot"):
        if not ndi:
            self._is_running = False
            logging.error("NDI is not available.")
            return

        self.source_name = source_name
        self._ndi_send = None
        self._video_thread = None
        self._is_running = False
        self._frame_lock = threading.Lock()
        self._current_frame: np.ndarray = self._create_black_frame()

        if not ndi.initialize():
            logging.error("Failed to initialize NDI. Is the NDI SDK installed on your system?")
            return

        send_settings = ndi.SendCreate()
        send_settings.p_ndi_name = self.source_name
        send_settings.clock_video = True
        self._ndi_send = ndi.send_create(send_settings)
        if self._ndi_send is None:
            logging.error("Failed to create NDI send instance.")
            ndi.destroy()
            return

        self._is_running = True
        self._video_thread = threading.Thread(target=self._broadcast_loop, name="NDIBroadcaster")
        self._video_thread.start()
        logging.info(f"NDI source '{self.source_name}' started and broadcasting.")

    def _create_black_frame(self) -> np.ndarray:
        """Generates a black RGBA frame matching the NDI output dimensions."""
        return np.zeros((NDI_HEIGHT, NDI_WIDTH, 4), dtype=np.uint8)

    def _broadcast_loop(self):
        """The main loop that sends the current frame at a consistent rate."""
        frame_interval = 1.0 / NDI_FRAME_RATE
        while self._is_running:
            start_time = time.time()
            
            with self._frame_lock:
                frame_data = np.ascontiguousarray(self._current_frame)

            video_frame = ndi.VideoFrameV2()
            video_frame.FourCC = ndi.FOURCC_VIDEO_TYPE_RGBA
            video_frame.width = NDI_WIDTH
            video_frame.height = NDI_HEIGHT
            video_frame.frame_rate_N = NDI_FRAME_RATE
            video_frame.frame_rate_D = 1
            video_frame.p_data = frame_data
            
            ndi.send_send_video_v2(self._ndi_send, video_frame)

            elapsed = time.time() - start_time
            sleep_time = frame_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

        logging.info("NDI broadcast loop stopped.")

    def update_slide(self, image_path: str) -> bool:
        """Loads an image, converts it, and updates the NDI stream."""
        if not self._is_running:
            logging.warning("Cannot update slide, NDIOutput is not running.")
            return False
            
        try:
            with Image.open(image_path) as img:
                img_resized = img.resize((NDI_WIDTH, NDI_HEIGHT))
                img_rgba = img_resized.convert("RGBA")
                frame = np.array(img_rgba)
                
                with self._frame_lock:
                    self._current_frame = frame
                logging.info(f"NDI frame updated with image: {image_path}")
                return True
        except FileNotFoundError:
            logging.error(f"Image file not found at: {image_path}")
        except Exception as e:
            logging.error(f"Failed to load image for NDI: {e}", exc_info=True)
        return False

    def clear_slide(self):
        """Replaces the current slide with a black screen."""
        if not self._is_running: return
        with self._frame_lock:
            self._current_frame = self._create_black_frame()
        logging.info("NDI output cleared to black.")

    def shutdown(self):
        """Stops the broadcast thread and releases all NDI resources."""
        if self._is_running:
            logging.info("Shutting down NDI source...")
            self._is_running = False
            if self._video_thread:
                self._video_thread.join()
            ndi.send_destroy(self._ndi_send)
            ndi.destroy()
            logging.info("NDI resources released.")

def send_image_to_ndi(image_path: str, source_name: str = "VersePilot"):
    """
    A simple, one-shot function to send a single image to NDI.
    Note: This is inefficient for frequent updates. Use the NDIOutput class.
    """
    ndi_output = NDIOutput(source_name)
    if ndi_output and ndi_output._is_running:
        ndi_output.update_slide(image_path)
        time.sleep(2) # Keep alive for receivers to see
        ndi_output.shutdown()

if __name__ == '__main__':
    print("--- Testing NDI Output ---")
    if not ndi:
        print("Aborting test because NDI library is not available.")
    else:
        print("Starting NDI source 'VersePilot-Test'. Check your NDI monitor.")
        
        TEST_IMAGE_PATH = "output/ndi_test_image.png"
        os.makedirs("output", exist_ok=True)
        img = Image.new('RGB', (1280, 720), color = 'darkblue')
        draw = ImageDraw.Draw(img)
        draw.text((100, 300), "NDI Test Slide\nVersePilot", fill='white', font_size=80)
        img.save(TEST_IMAGE_PATH)
        print(f"Created a test image at '{TEST_IMAGE_PATH}'.")

        ndi_stream = NDIOutput(source_name="VersePilot-Test")
        try:
            if ndi_stream._is_running:
                time.sleep(5) # Show black screen
                ndi_stream.update_slide(TEST_IMAGE_PATH)
                print("\nShowing test image for 10 seconds...")
                time.sleep(10)
                ndi_stream.clear_slide()
                print("\nCleared to black for 5 seconds...")
                time.sleep(5)
        except KeyboardInterrupt:
            print("\nShutdown requested.")
        finally:
            ndi_stream.shutdown()
            print("--- Test finished ---")
