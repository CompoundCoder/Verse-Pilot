import queue
import logging

class AppWindow:
    def check_listener_queue(self):
        """
        Checks the queue for detected verse lists from the listener thread
        and adds them to the display queue.
        """
        try:
            verse_list = self.verse_queue.get_nowait()
            if verse_list:
                self.display_queue.extend(verse_list)
                if not self.is_processing_display_queue:
                    self._process_next_in_display_queue()
        except queue.Empty:
            pass # No new verse, do nothing
        finally:
            self.after(100, self.check_listener_queue) # Poll again after 100ms

    def _process_next_in_display_queue(self):
        """Processes and displays the next verse from the local display queue."""
        if not self.display_queue:
            self.is_processing_display_queue = False
            if self.verse_listener.is_listening(): # Check if we should revert status
                self.status_label.configure(text="Listening for speech...")
            return

        self.is_processing_display_queue = True
        verse_data = self.display_queue.pop(0)
        
        try:
            book = verse_data.get("book")
            chapter = int(verse_data.get("chapter"))
            verse = int(verse_data.get("verse"))

            if not all([book, chapter, verse]):
                raise ValueError("Verse data is incomplete.")

            self.process_verse(book, chapter, verse)

        except (ValueError, TypeError, AttributeError) as e:
            logging.error(f"Invalid verse data received: {verse_data}. Error: {e}")
            # Immediately try to process the next item without delay
            self.after(0, self._process_next_in_display_queue)
        
    def _populate_mic_dropdown(self):
        """Queries sounddevice for available input devices and populates the dropdown."""
        # ... existing code ...
        else:
            self.status_label.configure(text="Error: Failed to render the verse slide.")

        # After processing, schedule the next item from the queue
        self.after(1000, self._process_next_in_display_queue) # 1-second delay before next verse

    def handle_detected_verse(self, book: str, chapter: int, verse: int):
        """
        # ... existing code ...
        # ... existing code ...
    def is_listening(self) -> bool:
        """Returns the running state of the listener thread."""
        return self._running.is_set()

if __name__ == '__main__':
    # --- Standalone Test ---
    # ... existing code ... 