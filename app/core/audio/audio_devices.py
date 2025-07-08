"""
Provides a utility function to query available audio input devices using
the sounddevice library. This is used by the settings screen to populate
the microphone selection dropdown.
"""
import sounddevice as sd
import logging

def get_audio_devices():
    """
    Returns a list of available audio input devices.

    Each device is a dictionary containing its properties as provided by the
    sounddevice library. This is filtered to only include devices with
    at least one input channel.
    
    Returns:
        list[dict]: A list of device dictionaries, or an empty list if an
                    error occurs or no devices are found.
    """
    try:
        devices = sd.query_devices()
        # Filter for devices that have at least one input channel.
        # This ensures we only list microphones, not speakers.
        input_devices = [
            dev for dev in devices if dev.get('max_input_channels', 0) > 0
        ]
        logging.info(f"Found {len(input_devices)} audio input devices.")
        return input_devices
    except Exception as e:
        # Using a broad exception as sd.query_devices() can fail for various
        # reasons (e.g., no audio subsystem, driver issues).
        logging.error(f"Could not query audio devices: {e}")
        return [] 