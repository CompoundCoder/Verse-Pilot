import customtkinter as ctk
from typing import Callable, List, Dict

class SidebarPanel(ctk.CTkFrame):
    def __init__(
        self,
        master,
        title: str,
        on_double_click: Callable[[Dict], None] = None,
        on_right_click: Callable[[Dict], None] = None,
        *args,
        **kwargs
    ):
        super().__init__(master, *args, **kwargs)

        self.title = title
        self.on_double_click = on_double_click
        self.on_right_click = on_right_click
        
        # --- State Management ---
        self.verse_widgets: Dict[str, Dict] = {}
        self.selected_key: str | None = None

        # --- Colors ---
        self.colors = {
            "normal": ["#2a2a2a", "#232323"], # Alternating row colors
            "selected": "#444444"
        }

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Title Label ---
        self.title_label = ctk.CTkLabel(self, text=self.title, font=ctk.CTkFont(weight="bold"), anchor="w")
        self.title_label.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 4))

        # --- Scrollable List Container ---
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        self.scroll_frame.grid_columnconfigure(0, weight=1)

    def update_verses(self, verses: List[Dict]):
        """Re-renders the verse list with new data, preserving selection if possible."""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.verse_widgets.clear()

        # If selected verse is no longer in the list, deselect it
        if self.selected_key and not any(self._get_verse_key(v) == self.selected_key for v in verses):
            self.selected_key = None

        for i, verse_data in enumerate(verses):
            verse_key = self._get_verse_key(verse_data)
            label_text = self._format_verse(verse_data)
            
            # Determine row color
            original_color = self.colors["normal"][i % 2]
            
            # Create a frame for each verse to handle background color and clicks
            frame = ctk.CTkFrame(self.scroll_frame, fg_color=original_color, corner_radius=4)
            label = ctk.CTkLabel(frame, text=label_text, anchor="w", fg_color="transparent")
            label.pack(fill="x", padx=8, pady=4)
            frame.pack(fill="x", padx=4, pady=2)
            
            # Store widgets and metadata for later manipulation
            self.verse_widgets[verse_key] = {
                "frame": frame,
                "label": label,
                "original_color": original_color
            }

            # Bind events to both frame and label for better UX
            widgets_to_bind = [frame, label]
            for widget in widgets_to_bind:
                # Left-click to select
                widget.bind("<Button-1>", lambda e, k=verse_key: self._handle_select(k))
                # Double-click action
                widget.bind("<Double-Button-1>", lambda e, v=verse_data: self._handle_double_click(v))
                # Right-click for context menu (works on Win, Mac, Linux)
                widget.bind("<Button-3>", lambda e, v=verse_data: self._handle_right_click(v)) # Windows/Linux
                widget.bind("<Button-2>", lambda e, v=verse_data: self._handle_right_click(v)) # macOS

        self._redraw_selection()

    def _get_verse_key(self, verse_data: Dict) -> str:
        """Generates a unique, consistent key for a verse."""
        return f"{verse_data.get('book')}-{verse_data.get('chapter')}-{verse_data.get('verse')}"

    def _format_verse(self, verse_data: Dict) -> str:
        """Formats a verse dict into a user-friendly string."""
        book = verse_data.get("book", "Unknown")
        chapter = verse_data.get("chapter", "?")
        verse = verse_data.get("verse", "?")
        return f"{book} {chapter}:{verse}"

    def _handle_select(self, verse_key: str):
        """Toggles selection for a given verse."""
        if self.selected_key == verse_key:
            self.selected_key = None  # Deselect if clicking the same item
        else:
            self.selected_key = verse_key
        self._redraw_selection()

    def _redraw_selection(self):
        """Updates the background colors of all verses based on the current selection."""
        for key, widgets in self.verse_widgets.items():
            frame = widgets["frame"]
            if key == self.selected_key:
                frame.configure(fg_color=self.colors["selected"])
            else:
                frame.configure(fg_color=widgets["original_color"])

    def _handle_double_click(self, verse_data: Dict):
        if self.on_double_click:
            self.on_double_click(verse_data)

    def _handle_right_click(self, verse_data: Dict):
        if self.on_right_click:
            self.on_right_click(verse_data) 