import customtkinter as ctk
import tkinter as tk
from app.core.settings.settings_model import get_settings, SettingsModel

class SettingsScreen(ctk.CTkToplevel):
    """
    An Adobe-style settings window that loads, edits, and saves application
    settings in a structured way.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("VersePilot Settings")
        self.geometry("700x500")
        self.minsize(600, 400)

        self.transient(self.master)
        self.grab_set()

        # --- Settings Management ---
        # // Get the singleton settings instance
        self.settings: SettingsModel = get_settings()
        # // Create a deep copy of the settings for the 'Undo' functionality
        self.initial_settings = self.settings._settings.copy()

        # --- UI State Variables ---
        # // These are now initialized from the loaded settings, not hardcoded.
        self.require_confirmation_var = ctk.BooleanVar(value=self.settings.require_approval)
        self.confidence_var = ctk.DoubleVar(value=self.settings.confidence_threshold)
        self.auto_display_timeout_var = ctk.BooleanVar(value=self.settings.auto_show_after_delay)
        
        # // Convert seconds to the string format used by the dropdown
        timeout_val = self.settings.auto_show_delay_seconds
        self.timeout_duration_var = ctk.StringVar(value=f"{timeout_val}s")
        
        # // Placeholder variables for UI elements not yet in the data model
        self.enable_audio_var = ctk.BooleanVar(value=True)
        self.auto_launch_var = ctk.BooleanVar(value=False)
        self.show_immediately_var = ctk.BooleanVar(value=True)
        self.font_size_var = ctk.IntVar(value=24)
        self.theme_var = ctk.StringVar(value="System Default")

        # --- Main Layout ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tab_frame = ctk.CTkFrame(self, width=150, corner_radius=0)
        self.tab_frame.grid(row=0, column=0, sticky="nsw")
        self.tab_frame.grid_rowconfigure(5, weight=1)
        
        # // Main content frame on the right
        self.main_content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_content_frame.grid_rowconfigure(0, weight=1)
        self.main_content_frame.grid_columnconfigure(0, weight=1)

        # // Panel frame to hold the switchable settings pages
        self.panel_frame = ctk.CTkFrame(self.main_content_frame)
        self.panel_frame.grid(row=0, column=0, sticky="nsew")

        # // Action buttons frame at the bottom
        self.action_button_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        self.action_button_frame.grid(row=1, column=0, sticky="sew", pady=(10, 0))
        self.action_button_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # --- Tab Buttons ---
        self.tabs = {}
        tab_names = ["General", "Display", "Voice", "Advanced"]
        for i, name in enumerate(tab_names):
            button = ctk.CTkButton(
                self.tab_frame, text=name, corner_radius=0, fg_color="transparent",
                text_color=("gray10", "gray90"), command=lambda n=name: self._select_tab(n)
            )
            button.grid(row=i, column=0, sticky="ew")
            self.tabs[name] = button

        # --- Content Panels ---
        self.panels = {
            "General": self._create_general_panel(self.panel_frame),
            "Display": self._create_display_panel(self.panel_frame),
            "Voice": self._create_voice_panel(self.panel_frame),
            "Advanced": self._create_advanced_panel(self.panel_frame)
        }
        
        # --- Action Buttons ---
        self.save_button = ctk.CTkButton(self.action_button_frame, text="Save", command=self._save_settings)
        self.save_button.grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.undo_button = ctk.CTkButton(self.action_button_frame, text="Undo", command=self._undo_changes)
        self.undo_button.grid(row=0, column=1, padx=5, pady=5, sticky="e")
        self.cancel_button = ctk.CTkButton(self.action_button_frame, text="Cancel", command=self._cancel, fg_color="transparent", border_width=1)
        self.cancel_button.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        
        self._select_tab("General")
        self.protocol("WM_DELETE_WINDOW", self._cancel) # // Handle window close button

        # // Force focus and lift the window after launch to fix macOS UI issues
        self.after(100, lambda: (self.lift(), self.focus_force()))

    def _select_tab(self, selected_name: str):
        """
        Shows the selected panel and hides the others. Also updates tab button
        appearance to indicate the active tab.
        """
        for name, button in self.tabs.items():
            # // Set the button's appearance based on whether it's selected.
            button.configure(fg_color=("gray75", "gray25") if name == selected_name else "transparent")
        
        for name, panel in self.panels.items():
            if name == selected_name:
                # // Show the selected panel.
                panel.pack(fill="both", expand=True)
            else:
                # // Hide all other panels.
                panel.pack_forget()

    def _create_general_panel(self, parent) -> ctk.CTkFrame:
        """Creates the panel for 'General' settings."""
        panel = ctk.CTkFrame(parent, fg_color="transparent")

        # // --- Version Label ---
        ctk.CTkLabel(panel, text="App Version", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(panel, text="Verse Pilot v0.1.0 – Pre-Alpha").pack(anchor="w", padx=5, pady=(0, 20))

        # // --- Toggles ---
        ctk.CTkSwitch(panel, text="Enable Audio Detection", variable=self.enable_audio_var).pack(anchor="w", pady=10)
        ctk.CTkSwitch(panel, text="Auto-launch at Startup", variable=self.auto_launch_var).pack(anchor="w", pady=10)
        
        return panel

    def _create_display_panel(self, parent) -> ctk.CTkFrame:
        """Creates the panel for 'Display' settings."""
        panel = ctk.CTkFrame(parent, fg_color="transparent")

        ctk.CTkSwitch(panel, text="Show Verse Immediately", variable=self.show_immediately_var).pack(anchor="w", pady=10)

        # // --- Font Size Slider ---
        font_frame = ctk.CTkFrame(panel, fg_color="transparent")
        font_frame.pack(fill="x", pady=10)
        font_label = ctk.CTkLabel(font_frame, text=f"Font Size: {self.font_size_var.get()}pt")
        font_label.pack(side="left")
        font_slider = ctk.CTkSlider(
            font_frame, from_=12, to=48, variable=self.font_size_var,
            command=lambda v: font_label.configure(text=f"Font Size: {int(v)}pt")
        )
        font_slider.pack(side="left", fill="x", expand=True, padx=10)

        # // --- Theme Dropdown ---
        theme_frame = ctk.CTkFrame(panel, fg_color="transparent")
        theme_frame.pack(fill="x", pady=10, anchor="w")
        ctk.CTkLabel(theme_frame, text="Background Theme").pack(side="left")
        ctk.CTkOptionMenu(
            theme_frame, values=["Light", "Dark", "System Default"], variable=self.theme_var
        ).pack(side="left", padx=10)
        
        return panel

    def _create_voice_panel(self, parent) -> ctk.CTkFrame:
        """Creates the panel for 'Voice' settings."""
        panel = ctk.CTkFrame(parent, fg_color="transparent")
        
        # // --- Confidence Slider ---
        conf_frame = ctk.CTkFrame(panel, fg_color="transparent")
        conf_frame.pack(fill="x", pady=10)
        conf_label = ctk.CTkLabel(conf_frame, text=f"Confidence Threshold: {self.confidence_var.get():.2f}")
        conf_label.pack(side="left")
        conf_slider = ctk.CTkSlider(
            conf_frame, from_=0.0, to=1.0, variable=self.confidence_var,
            command=lambda v: conf_label.configure(text=f"Confidence Threshold: {v:.2f}")
        )
        conf_slider.pack(side="left", fill="x", expand=True, padx=10)
        
        ctk.CTkSwitch(panel, text="Require Human Confirmation if Uncertain", variable=self.require_confirmation_var).pack(anchor="w", pady=10)
        ctk.CTkSwitch(panel, text="Auto-display verse after timeout", variable=self.auto_display_timeout_var).pack(anchor="w", pady=10)
        
        # // --- Timeout Dropdown ---
        timeout_frame = ctk.CTkFrame(panel, fg_color="transparent")
        timeout_frame.pack(fill="x", pady=10, anchor="w")
        ctk.CTkLabel(timeout_frame, text="Timeout duration (in seconds)").pack(side="left")
        ctk.CTkOptionMenu(
            timeout_frame, values=["10s", "15s", "30s", "60s"], variable=self.timeout_duration_var
        ).pack(side="left", padx=10)

        return panel

    def _create_advanced_panel(self, parent) -> ctk.CTkFrame:
        """Creates the panel for 'Advanced' settings. Currently a placeholder."""
        panel = ctk.CTkFrame(parent, fg_color="transparent")
        ctk.CTkLabel(panel, text="Advanced Settings", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        ctk.CTkLabel(panel, text="This section is reserved for future developer tools and options.").pack(pady=5)
        return panel

    def _save_settings(self):
        """Saves the current UI state back to the settings model and closes."""
        # // Directly update the internal dictionary to avoid auto-save on each property
        self.settings._settings["require_approval"] = self.require_confirmation_var.get()
        self.settings._settings["confidence_threshold"] = self.confidence_var.get()
        self.settings._settings["auto_show_after_delay"] = self.auto_display_timeout_var.get()
        # // Convert string like "30s" back to an integer
        timeout_str = self.timeout_duration_var.get().replace('s', '')
        self.settings._settings["auto_show_delay_seconds"] = int(timeout_str)
        
        # // Manually trigger the save to persist all changes at once
        self.settings._save()
        self.destroy()

    def _undo_changes(self):
        """Resets the UI controls to their initial loaded values."""
        self.require_confirmation_var.set(self.initial_settings.get("require_approval"))
        self.confidence_var.set(self.initial_settings.get("confidence_threshold"))
        self.auto_display_timeout_var.set(self.initial_settings.get("auto_show_after_delay"))
        timeout_val = self.initial_settings.get("auto_show_delay_seconds")
        self.timeout_duration_var.set(f"{timeout_val}s")
        # // Note: Other placeholder vars are not part of the model and won't be undone.
        
    def _cancel(self):
        """Closes the window without saving any changes."""
        self.destroy() 