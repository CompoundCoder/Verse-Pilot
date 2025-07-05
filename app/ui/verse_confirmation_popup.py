import customtkinter as ctk
from typing import Callable

class VerseConfirmationPopup(ctk.CTkToplevel):
    """
    A modal popup that asks the user to confirm or reject a low-confidence verse.
    It can auto-approve the verse after a specified timeout.
    """
    def __init__(
        self,
        master,
        verse_data: dict,
        timeout_duration_s: int,
        auto_approve: bool,
        callback: Callable[[bool, dict], None]
    ):
        super().__init__(master)
        
        self.verse_data = verse_data
        self.callback = callback
        self._auto_approve_enabled = auto_approve
        self._timeout_ms = timeout_duration_s * 1000

        # --- Window Configuration ---
        self.title("Confirm Verse")
        self.geometry("400x180")
        self.transient(master)  # // Keep on top of the main window
        self.grab_set()         # // Block interaction with the main window
        self.protocol("WM_DELETE_WINDOW", self._reject) # // Treat closing as a rejection
        
        # --- Widgets ---
        reference_text = f"{verse_data.get('book')} {verse_data.get('chapter')}:{verse_data.get('verse')}"
        confidence_pct = verse_data.get('confidence', 0.0) * 100
        
        main_label = ctk.CTkLabel(
            self,
            text="Low confidence detection. Show this verse?",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        main_label.pack(pady=(20, 10))

        verse_label = ctk.CTkLabel(
            self,
            text=f"{reference_text} (Confidence: {confidence_pct:.1f}%)",
            font=ctk.CTkFont(size=14)
        )
        verse_label.pack(pady=5)
        
        # // Frame for the action buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=20)

        approve_button = ctk.CTkButton(
            button_frame,
            text="Approve",
            command=self._approve,
            width=120
        )
        approve_button.pack(side="left", padx=10)

        reject_button = ctk.CTkButton(
            button_frame,
            text="Reject",
            command=self._reject,
            fg_color="gray50",
            hover_color="gray40",
            width=120
        )
        reject_button.pack(side="right", padx=10)
        
        self.approve_button = approve_button # Store reference for timer update

        # --- Auto-approval Timer ---
        self._timer_id = None
        # // The timer now always runs, but its behavior depends on the auto_approve flag.
        self._start_timer()

        # // Force focus and lift the window after launch to fix macOS UI issues
        self.after(100, lambda: (self.lift(), self.focus_force()))

    def _start_timer(self):
        """Starts the countdown to auto-process the verse."""
        if self._timeout_ms > 0:
            # // The action on timeout is now determined by the _auto_process method.
            self._timer_id = self.after(self._timeout_ms, self._auto_process)
            self._update_button_text(self._timeout_ms // 1000)

    def _update_button_text(self, seconds_left: int):
        """Updates the approve button with a countdown."""
        if seconds_left > 0:
            self.approve_button.configure(text=f"Approve ({seconds_left})")
            self.after(1000, lambda: self._update_button_text(seconds_left - 1))
        else:
            self.approve_button.configure(text="Approve")

    def _cancel_timer(self):
        """Cancels the auto-approval timer if it's running."""
        if self._timer_id:
            self.after_cancel(self._timer_id)
            self._timer_id = None

    def _approve(self):
        """Handles the approval action."""
        self._cancel_timer()
        self.callback(True, self.verse_data)
        self.destroy()

    def _reject(self):
        """Handles the rejection action."""
        self._cancel_timer()
        self.callback(False, self.verse_data)
        self.destroy()
        
    def _auto_process(self):
        """
        Handles the timeout action. Approves or rejects based on the
        auto_approve setting passed during initialization.
        """
        if self.winfo_exists():
            # // If auto-approve is enabled, the callback is sent with True.
            # // Otherwise, it's considered a rejection.
            self.callback(self._auto_approve_enabled, self.verse_data)
            self.destroy() 