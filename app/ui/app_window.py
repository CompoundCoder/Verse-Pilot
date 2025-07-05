import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from PIL import Image
import os
import logging
import sounddevice as sd
import numpy as np
import threading
import queue
import time
import json

# --- App Dependencies ---
# Use absolute imports for better clarity and structure
from app.core.bible import bible_lookup
from app.core.rendering import slide_renderer
# from app.core.video import ndi_output
from app.core.audio.listener import VerseListener
from app.ui.settings_screen import SettingsScreen
from app.core.settings.settings_model import get_settings
from app.ui.verse_confirmation_popup import VerseConfirmationPopup
from app.ui.components.sidebar_panel import SidebarPanel
from app.ui.components.edit_verse_popup import EditVersePopup
# from app.ui.view_models import AppViewModel # No longer needed
# NOTE: Visualizer and its related components are removed.
# The archived code is in archives/visualizer.py

# --- Configuration ---
PREVIEW_IMAGE_PATH = "output/verse.png"
DEFAULT_STATUS = "Idle. Select a mic and start listening."
SIDEBAR_ICON_PATH = "app/assets/icons/sidebar_toggle.png"

# --- Setup Logging ---
# To see logs from other modules in the console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s')

class AppWindow(ctk.CTk):
    """
    The main GUI window for the VersePilot application.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # --- Window Setup ---
        self.title("VersePilot")
        self.geometry("800x600") # Adjusted height after removing visualizer
        self.grid_columnconfigure(1, weight=1) # Let the main content area expand
        self.grid_rowconfigure(0, weight=1) # Main content area below toolbar
        self.grid_rowconfigure(1, weight=0) # Bottom controls
        
        # --- App State ---
        self.confirmation_popup = None
        self.recent_verse = None          # Last detected verse, always overwritten
        self.confirmation_buffer = []     # Holds low-confidence verses awaiting approval (list of verse dicts)
        self.live_history = []            # Holds all approved/shown verses (list of verse dicts)
        self.rejected_keys = set()        # Holds rejected verse keys (set of (book, chapter, verse))
        self.recent_detections = {}       # Tracks recently seen (book, chapter, verse): { timestamp, confidence }

        # --- Core Logic Instances ---
        # self.ndi_stream = ndi_output.NDIOutput(source_name="VersePilot Live")
        self.verse_listener = VerseListener()
        self.mic_devices = {}
        self.verse_queue = queue.Queue() # Thread-safe queue for verse dicts

        # --- Toolbar ---
        self.toolbar_frame = ctk.CTkFrame(self, height=40, corner_radius=0, fg_color="#2b2b2b")
        self.toolbar_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.toolbar_frame.grid_propagate(False) # Prevent resizing
        self._setup_toolbar()

        # --- Main Layout Frames ---
        self.sidebar_container = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color="#242424")
        self.sidebar_container.grid(row=1, column=0, sticky="nsw")
        self.sidebar_container.grid_rowconfigure(1, weight=1) # Let history panel expand

        self.content_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_container.grid(row=1, column=1, sticky="nsew")
        self.content_container.grid_rowconfigure(0, weight=1) # Let preview expand
        self.content_container.grid_columnconfigure(0, weight=1)

        # --- Main Content (Preview + Bottom Controls) ---
        self.main_frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_rowconfigure(0, weight=1) # Preview
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.bottom_frame = ctk.CTkFrame(self.main_frame, height=200, fg_color="transparent")
        self.bottom_frame.grid(row=1, column=0, sticky="ew", pady=(10,0))
        self.bottom_frame.grid_columnconfigure(0, weight=1)
        
        # --- Sidebar Panels ---
        self.queue_panel = SidebarPanel(
            self.sidebar_container,
            title="Queue",
            on_double_click=self._on_sidebar_double_click,
            on_right_click=self._on_sidebar_right_click
        )
        self.queue_panel.grid(row=0, column=0, sticky="nsew", pady=(0, 5))

        self.history_panel = SidebarPanel(
            self.sidebar_container,
            title="History",
            on_double_click=self._on_sidebar_double_click,
            on_right_click=self._on_sidebar_right_click
        )
        self.history_panel.grid(row=1, column=0, sticky="nsew", pady=(5, 0), padx=4)

        # --- Top: Preview Area ---
        self.preview_label = ctk.CTkLabel(self.main_frame, text="Preview will appear here", text_color="gray")
        self.preview_label.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.preview_image = None # To hold the PhotoImage object

        # --- Bottom: Controls & Status ---
        # Manual Trigger Section
        manual_frame = ctk.CTkFrame(self.bottom_frame)
        manual_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        manual_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(manual_frame, text="Book:").grid(row=0, column=0, padx=(10, 2), pady=5)
        self.book_entry = ctk.CTkEntry(manual_frame, placeholder_text="John")
        self.book_entry.grid(row=1, column=0, padx=(10, 5), pady=5, sticky="ew")
        self.book_entry.insert(0, "John")
        
        ctk.CTkLabel(manual_frame, text="Chapter:").grid(row=0, column=1, padx=5, pady=5)
        self.chapter_entry = ctk.CTkEntry(manual_frame, placeholder_text="3")
        self.chapter_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.chapter_entry.insert(0, "3")
        
        ctk.CTkLabel(manual_frame, text="Verse:").grid(row=0, column=2, padx=5, pady=5)
        self.verse_entry = ctk.CTkEntry(manual_frame, placeholder_text="16")
        self.verse_entry.grid(row=1, column=2, padx=5, pady=5, sticky="ew")
        self.verse_entry.insert(0, "16")
        
        self.trigger_button = ctk.CTkButton(manual_frame, text="Trigger Verse", command=self._on_manual_trigger)
        self.trigger_button.grid(row=1, column=3, padx=(5, 10), pady=5, sticky="ew")

        # Listening Controls
        status_frame = ctk.CTkFrame(self.bottom_frame)
        status_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        status_frame.grid_columnconfigure(1, weight=1)

        self.mic_dropdown_var = ctk.StringVar(value="No input devices found")
        self.mic_dropdown = ctk.CTkOptionMenu(status_frame, variable=self.mic_dropdown_var, values=[], command=self._on_mic_selected)
        self.mic_dropdown.grid(row=0, column=0, padx=10, pady=10)
        
        self.status_label = ctk.CTkLabel(status_frame, text=DEFAULT_STATUS, anchor="w")
        self.status_label.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.start_button = ctk.CTkButton(status_frame, text="Start Listening", command=self._on_start_listening, state="disabled")
        self.start_button.grid(row=0, column=2, padx=10, pady=10)
        self.stop_button = ctk.CTkButton(status_frame, text="Stop Listening", command=self._on_stop_listening, state="disabled")
        self.stop_button.grid(row=0, column=3, padx=10, pady=10)

        # --- Initializations ---
        self._deprecate_old_logs()
        self._setup_macos_menu()
        self._load_initial_preview()
        self._populate_mic_dropdown()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.check_verse_queue() # Start polling for verse results
        self._queue_cleanup()    # Start periodic cleanup of the confirmation buffer
        self._cleanup_recent_detections()

        # Restore sidebar visibility state from settings
        self._apply_sidebar_state()

        # // Force focus and lift the window after launch to fix macOS UI issues
        self.after(100, lambda: (self.lift(), self.focus_force()))

    def _setup_toolbar(self):
        """Creates and places the widgets in the top toolbar."""
        try:
            icon_image = ctk.CTkImage(Image.open(SIDEBAR_ICON_PATH), size=(20, 20))
            button_text = ""
        except FileNotFoundError:
            logging.warning(f"Icon not found at '{SIDEBAR_ICON_PATH}'. Using fallback text icon.")
            icon_image = None
            button_text = "≡"

        self.sidebar_toggle_button = ctk.CTkButton(
            self.toolbar_frame,
            text=button_text,
            image=icon_image,
            width=28, 
            height=28,
            fg_color="transparent",
            hover_color="#444444",
            command=self._toggle_sidebar
        )
        self.sidebar_toggle_button.pack(side="left", padx=6, pady=6)

    def _deprecate_old_logs(self):
        """Moves old log files to an archive to prevent reuse."""
        old_log_file = "versepilot_rejected_log.txt"
        if os.path.exists(old_log_file):
            archive_dir = "archives"
            if not os.path.exists(archive_dir):
                os.makedirs(archive_dir)
            try:
                os.rename(old_log_file, os.path.join(archive_dir, "versepilot_rejected_log.ignore"))
                logging.info(f"Moved deprecated log file to {archive_dir}.")
            except OSError as e:
                logging.error(f"Could not move old log file: {e}")

    def _queue_cleanup(self):
        """Periodically removes stale items from the confirmation buffer."""
        now = time.time()
        # A verse is stale if it has been in the buffer for over 60 seconds.
        self.confirmation_buffer = [
            v for v in self.confirmation_buffer
            if now - v.get("buffer_timestamp", now) <= 60
        ]
        
        self._update_sidebar_panels() # Refresh UI after cleanup
        # Schedule the next cleanup in 10 seconds.
        self.after(10000, self._queue_cleanup)

    def _cleanup_recent_detections(self):
        """Cleans out old verse detections every 30s."""
        cutoff = time.time() - 30
        before = len(self.recent_detections)
        self.recent_detections = {
            k: v for k, v in self.recent_detections.items()
            if v["timestamp"] > cutoff
        }
        after = len(self.recent_detections)
        if before != after:
            logging.debug(f"Cleaned recent_detections: {before} → {after}")
        self.after(5000, self._cleanup_recent_detections)

    def _update_sidebar_panels(self):
        """Updates both the queue and history panels with current data."""
        # The queue panel displays verses pending confirmation.
        self.queue_panel.update_verses(self.confirmation_buffer)
        
        # The history panel shows all approved verses, most recent first.
        history_verses = sorted(self.live_history, key=lambda v: v.get('timestamp', 0), reverse=True)
        self.history_panel.update_verses(history_verses)

    def _setup_macos_menu(self):
        # // Create the main menu bar to attach to the root window.
        menu_bar = tk.Menu(self)

        # // Create the main "Verse Pilot" application menu.
        app_menu = tk.Menu(menu_bar, name='apple')
        menu_bar.add_cascade(label="Verse Pilot", menu=app_menu)

        # // Add items to the "Verse Pilot" menu.
        app_menu.add_command(label="About Verse Pilot", command=self._show_about_dialog)
        app_menu.add_separator()
        app_menu.add_command(label="Settings...", command=self._on_settings_button_clicked)
        app_menu.add_separator()
        app_menu.add_command(label="Quit Verse Pilot", command=self._on_closing)

        # // Set the menu bar on the root window.
        self.config(menu=menu_bar)

    def _show_about_dialog(self):
        # // A simple dialog to show application info.
        messagebox.showinfo(
            "About Verse Pilot",
            "Verse Pilot v0.1.0 – Pre-Alpha"
        )

    def check_verse_queue(self):
        """
        Checks for new verse data from the queue and manages the verse processing flow.
        """
        if self.confirmation_popup and self.confirmation_popup.winfo_exists():
            self.after(100, self.check_verse_queue)
            return

        try:
            verse_data = self.verse_queue.get_nowait()

            # Validate input
            if not isinstance(verse_data, dict):
                logging.warning(f"Skipping non-dict item from queue: {verse_data}")
                return

            book = verse_data.get("book")
            chapter = verse_data.get("chapter")
            verse = verse_data.get("verse")
            if not all([book, chapter, verse]):
                logging.warning(f"Invalid verse: {verse_data}")
                return

            key = (book, int(chapter), int(verse))
            now = time.time()
            confidence = verse_data.get("confidence", 1.0)
            
            # Debounce logic for same-key re-processing
            prev = self.recent_detections.get(key)
            if prev and now - prev["timestamp"] < 15:
                if confidence <= prev["confidence"]:
                    logging.info(f"Skipping duplicate verse with lower or equal confidence: {key}")
                    return  # Do not reprocess this verse
                else:
                    logging.info(f"Replacing older detection with higher confidence: {key}")

            # Update or insert this detection
            self.recent_detections[key] = {
                "timestamp": now,
                "confidence": confidence
            }

            self.recent_verse = verse_data

            # Skip if already rejected, pending, or in history
            if key in self.rejected_keys:
                return
            if key in self.confirmation_buffer:
                return
            if any(v["book"] == book and v["chapter"] == int(chapter) and v["verse"] == int(verse) for v in self.live_history):
                return

            # Apply confidence filter
            settings = get_settings()
            if settings.require_approval and confidence < settings.confidence_threshold:
                verse_data["buffer_timestamp"] = time.time()
                self.confirmation_buffer.append(verse_data)
                self.confirmation_popup = VerseConfirmationPopup(
                    self,
                    verse_data=verse_data,
                    timeout_duration_s=settings.auto_show_delay_seconds,
                    auto_approve=settings.auto_show_after_delay,
                    callback=self._on_confirmation_result
                )
            else:
                self.live_history.append(verse_data)
                self._process_verse_data(verse_data)
        except queue.Empty:
            pass
        finally:
            self.after(100, self.check_verse_queue)

    def _on_confirmation_result(self, approved: bool, verse_data: dict):
        """Callback for the VerseConfirmationPopup."""
        self.confirmation_popup = None
        key_to_remove = self._get_verse_key(verse_data)
        
        # Remove from pending buffer
        self.confirmation_buffer = [v for v in self.confirmation_buffer if self._get_verse_key(v) != key_to_remove]
        
        if approved:
            logging.info(f"Verse approved: {key_to_remove}")
            self.live_history.append(verse_data)
            self._process_verse_data(verse_data)
        else:
            logging.info(f"Verse rejected: {key_to_remove}")
            self.rejected_keys.add(key_to_remove)
        
        self._update_sidebar_panels()
    
    def _process_verse_data(self, verse_data: dict):
        """Validates and processes a verse dictionary."""
        try:
            book = verse_data.get("book")
            chapter = int(verse_data.get("chapter"))
            verse = int(verse_data.get("verse"))

            if not all([book, chapter, verse]):
                raise ValueError("Verse data is incomplete.")

            self.process_verse(book, chapter, verse)
        except (ValueError, TypeError) as e:
            logging.error(f"Skipping invalid data from queue: {e} -> {verse_data}")

    def _populate_mic_dropdown(self):
        """Queries sounddevice for available input devices and populates the dropdown."""
        try:
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            
            if not input_devices:
                self.mic_dropdown.configure(state="disabled")
                return

            self.mic_devices = {d['name']: i for i, d in enumerate(devices) if d['max_input_channels'] > 0}
            device_names = list(self.mic_devices.keys())
            
            self.mic_dropdown.configure(values=device_names)
            self.mic_dropdown_var.set(device_names[0]) # Select the first one by default
            self.start_button.configure(state="normal")
            self._on_mic_selected(device_names[0])
            
        except Exception as e:
            logging.error(f"Could not query audio devices: {e}")
            self.status_label.configure(text="Error: Could not find audio devices.")

    def _on_mic_selected(self, selected_device_name: str):
        """Callback for when a microphone is selected from the dropdown."""
        logging.info(f"Microphone selected: {selected_device_name}")
        # This function is now just a placeholder for potential future use.
        # Previously, it was used to restart the visualizer.
        pass

    def _on_start_listening(self):
        """Starts the VerseListener with the selected microphone."""
        try:
            selected_device_name = self.mic_dropdown_var.get()
            selected_device_index = self.mic_devices.get(selected_device_name)

            if selected_device_index is None:
                self.status_label.configure(text="Error: Invalid microphone selected.")
                return

            self.status_label.configure(text="Initializing listener...")
            # Pass the queue to the listener instead of a direct callback
            self.verse_listener.start_listening(self.verse_queue, input_device_index=selected_device_index)
            self.status_label.configure(text="Listening for speech...")
            
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.mic_dropdown.configure(state="disabled")
            self.trigger_button.configure(state="disabled")
            
        except RuntimeError as e:
            logging.error(f"Failed to start listener: {e}", exc_info=True)
            self.status_label.configure(text=f"Error: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred when starting listener: {e}", exc_info=True)
            self.status_label.configure(text="Error: Could not start listener.")

    def _on_stop_listening(self):
        """Stops the VerseListener and updates the UI state."""
        self.verse_listener.stop_listening()
        self.status_label.configure(text=DEFAULT_STATUS)
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.mic_dropdown.configure(state="normal")
        self.trigger_button.configure(state="normal")
        
    def _on_settings_button_clicked(self):
        """Opens the settings window."""
        # // This is now triggered from the native menu bar.
        if not hasattr(self, 'settings_window') or not self.settings_window.winfo_exists():
            self.settings_window = SettingsScreen(self)
        else:
            self.settings_window.focus() # If it exists, bring it to the front.

    def _on_manual_trigger(self):
        """Handler for the 'Trigger Verse' button."""
        book = self.book_entry.get()
        chapter_str = self.chapter_entry.get()
        verse_str = self.verse_entry.get()

        if not all([book, chapter_str, verse_str]):
            self.status_label.configure(text="Error: All fields are required for manual trigger.")
            return
            
        try:
            chapter, verse = int(chapter_str), int(verse_str)
            self.process_verse(book, chapter, verse)
        except ValueError:
            self.status_label.configure(text="Error: Chapter and Verse must be numbers.")
        except Exception as e:
            self.status_label.configure(text=f"An unexpected error occurred: {e}")
            logging.error(f"Error during manual trigger: {e}", exc_info=True)

    def process_verse(self, book: str, chapter: int, verse: int):
        """Fetches, renders, and outputs a verse. This method is UI-safe."""
        self.status_label.configure(text=f"Looking up {book} {chapter}:{verse}...")
        
        verse_text = bible_lookup.get_verse(book, chapter, verse)
        if not verse_text:
            self.status_label.configure(text=f"Error: Verse not found for {book} {chapter}:{verse}.")
            return

        reference = f"{book.title()} {chapter}:{verse}"
        self.status_label.configure(text=f"Rendering slide for {reference}...")
        
        output_path = slide_renderer.render_verse_slide(verse_text, reference, output_path=PREVIEW_IMAGE_PATH)
        if output_path:
            self.status_label.configure(text=f"Broadcasting {reference}...")
            self._update_preview_image(output_path)
            # self.ndi_stream.update_slide(output_path)
            # Revert status to listening after a successful render
            if self.verse_listener.is_listening():
                self.status_label.configure(text="Listening for speech...")
        else:
            self.status_label.configure(text="Error: Failed to render the verse slide.")

    def _update_preview_image(self, image_path: str):
        """Loads the specified image and displays it in the preview area."""
        try:
            if not os.path.exists(image_path):
                self.preview_label.configure(text="Preview not available.", image=None)
                return

            # Guard against running before the window is fully drawn.
            preview_width = self.main_frame.winfo_width()
            preview_height = self.main_frame.winfo_height()
            if preview_width <= 1 or preview_height <= 1:
                logging.warning(f"Preview widget not ready: size is {preview_width}x{preview_height}. Retrying...")
                # Retry after a short delay
                self.after(100, lambda: self._update_preview_image(image_path))
                return
            
            img = Image.open(image_path)
            # Adjust for padding inside the calculation
            preview_width -= 20
            preview_height -= 20

            # Maintain aspect ratio
            img_ratio = img.width / img.height
            container_width = self.main_frame.winfo_width()
            container_height = self.main_frame.winfo_height()

            if container_width <= 1 or container_height <= 1:
                self.after(100, lambda: self._update_preview_image(image_path))
                return
            
            preview_ratio = container_width / container_height
            
            if img_ratio > preview_ratio:
                # Image is wider than preview area
                new_width = container_width
                new_height = int(new_width / img_ratio)
            else:
                # Image is taller than preview area
                new_height = container_height
                new_width = int(new_height * img_ratio)

            if new_width > 0 and new_height > 0:
                self.preview_image = ctk.CTkImage(light_image=img, size=(new_width, new_height))
                self.preview_label.configure(text="", image=self.preview_image)
        except Exception as e:
            logging.error(f"Error loading preview image at {image_path}: {e}", exc_info=True)
            self.preview_label.configure(text=f"Error loading preview:\n{os.path.basename(image_path)}", image=None)
            
    def _load_initial_preview(self):
        """Loads the initial placeholder or existing verse image."""
        if os.path.exists(PREVIEW_IMAGE_PATH):
            self._update_preview_image(PREVIEW_IMAGE_PATH)
        else:
            self.preview_label.grid() # Ensure it's visible

    def _on_closing(self):
        """Handles graceful shutdown of the application."""
        logging.info("Closing application...")
        if self.verse_listener.is_listening():
            self.verse_listener.stop_listening()
        
        # // Serialize the live verse history log to a file for context
        try:
            with open("verse_history.json", "w") as f:
                json.dump(self.live_history, f, indent=4)
            logging.info("Verse history saved.")
        except Exception as e:
            logging.error(f"Failed to save verse history: {e}")
            
        self.destroy()

    def _on_sidebar_double_click(self, verse_data: dict):
        """Triggered when user double-clicks a verse in queue/history."""
        self._process_verse_data(verse_data)

    def _on_sidebar_right_click(self, verse_data: dict):
        """Creates and displays a context menu for a verse in the sidebar."""
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(
            label="Edit", 
            command=lambda v=verse_data: self._open_edit_popup(v)
        )
        menu.add_command(
            label="Delete", 
            command=lambda v=verse_data: self._delete_verse(v)
        )
        
        try:
            # Position menu at cursor
            menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())
        finally:
            menu.grab_release()

    def _open_edit_popup(self, verse_data):
        """Opens the edit popup for a given verse."""
        if hasattr(self, "_edit_popup") and self._edit_popup.winfo_exists():
            self._edit_popup.focus()
            return

        self._edit_popup = EditVersePopup(
            self,
            verse_data=verse_data,
            on_save=self._on_verse_edited
        )

    def _on_verse_edited(self, original_data, updated_data):
        """Callback when a verse is successfully edited and saved."""
        original_key = self._get_verse_key(original_data)
        updated_key = self._get_verse_key(updated_data)

        # Check queue first
        for i, verse in enumerate(self.confirmation_buffer):
            if self._get_verse_key(verse) == original_key:
                self.confirmation_buffer[i] = updated_data
                logging.info(f"Verse updated in confirmation buffer: {original_key} -> {updated_key}")
                self._update_sidebar_panels()
                return

        # Then check history
        for i, verse in enumerate(self.live_history):
            if self._get_verse_key(verse) == original_key:
                self.live_history[i] = updated_data
                logging.info(f"Verse updated in live history: {original_key} -> {updated_key}")
                self._update_sidebar_panels()
                
                # If the edited verse was the last one shown, update the main display
                if self.recent_verse and self._get_verse_key(self.recent_verse) == original_key:
                    self._update_verse_display(updated_data)
                return
        
        logging.warning(f"Could not find verse to update: {original_key}")

    def _delete_verse(self, verse_data):
        """Removes a verse from the queue or history."""
        key_to_delete = self._get_verse_key(verse_data)

        # Try removing from confirmation buffer
        original_len = len(self.confirmation_buffer)
        self.confirmation_buffer = [v for v in self.confirmation_buffer if self._get_verse_key(v) != key_to_delete]
        if len(self.confirmation_buffer) < original_len:
            logging.info(f"Verse deleted from confirmation buffer: {key_to_delete}")
            self._update_sidebar_panels()
            return
            
        # Try removing from live history
        original_len = len(self.live_history)
        self.live_history = [v for v in self.live_history if self._get_verse_key(v) != key_to_delete]
        if len(self.live_history) < original_len:
            logging.info(f"Verse deleted from live history: {key_to_delete}")
            self._update_sidebar_panels()
            # If we deleted the most recent verse, clear the display
            if self.recent_verse and self._get_verse_key(self.recent_verse) == key_to_delete:
                self._clear_verse_display()
            return
        
        logging.warning(f"Could not find verse to delete: {key_to_delete}")

    def _toggle_sidebar(self):
        """Toggles the visibility of the sidebar and saves the state."""
        is_visible = self.sidebar_container.winfo_viewable()
        get_settings().sidebar_visible = not is_visible
        self._apply_sidebar_state()

    def _apply_sidebar_state(self):
        """Shows or hides the sidebar based on the current setting."""
        if get_settings().sidebar_visible:
            self.sidebar_container.grid()
        else:
            self.sidebar_container.grid_remove()

    def _get_verse_key(self, verse_data: dict) -> str:
        """Generates a unique, consistent key for a verse."""
        return f"{verse_data['book']} {verse_data['chapter']}:{verse_data['verse']}"

def main():
    """Main application entry point."""
    # Use a modern theme
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    
    app = AppWindow()
    try:
        app.mainloop()
    except Exception as e:
        logging.critical(f"Unhandled exception in main application loop: {e}", exc_info=True)

if __name__ == "__main__":
    main()
