import customtkinter as ctk
from app.core.bible import bible_lookup

class EditVersePopup(ctk.CTkToplevel):
    """
    A popup window for editing a bible verse (Book, Chapter, Verse).
    """
    def __init__(self, master, verse_data: dict, on_save: callable):
        super().__init__(master)
        self.transient(master)
        self.grab_set()

        self.on_save = on_save
        self.original_data = verse_data

        self.title("Edit Verse")
        self.geometry("350x200")
        
        # Center the popup on the master window
        master_x = master.winfo_x()
        master_y = master.winfo_y()
        master_width = master.winfo_width()
        master_height = master.winfo_height()
        self.geometry(f"+{master_x + master_width // 2 - 175}+{master_y + master_height // 2 - 100}")

        # --- Widgets ---
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(expand=True, fill="both", padx=10, pady=10)

        self.book_entry = self._create_entry("Book:", verse_data.get("book", ""))
        self.chapter_entry = self._create_entry("Chapter:", verse_data.get("chapter", ""))
        self.verse_entry = self._create_entry("Verse:", verse_data.get("verse", ""))
        
        self.error_label = ctk.CTkLabel(self.main_frame, text="", text_color="red")
        self.error_label.pack(pady=(5, 0))

        self._create_buttons()
        
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.after(250, lambda: self.book_entry.focus_set()) # Set focus

    def _create_entry(self, label_text, initial_value):
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=5)
        
        label = ctk.CTkLabel(frame, text=label_text, width=8)
        label.pack(side="left")
        
        entry = ctk.CTkEntry(frame)
        entry.insert(0, str(initial_value))
        entry.pack(side="right", expand=True, fill="x")
        return entry

    def _create_buttons(self):
        button_frame = ctk.CTkFrame(self.main_frame)
        button_frame.pack(side="bottom", fill="x", pady=(10, 0), padx=10)

        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self._on_cancel
        ).pack(side="right")
        
        ctk.CTkButton(
            button_frame,
            text="Save",
            command=self._on_save,
            fg_color="green" # Highlight the primary action
        ).pack(side="right", padx=10)

    def _on_save(self):
        book = self.book_entry.get().strip()
        chapter_str = self.chapter_entry.get().strip()
        verse_str = self.verse_entry.get().strip()
        
        # Validation
        if not all([book, chapter_str, verse_str]):
            self.error_label.configure(text="All fields are required.")
            return

        try:
            chapter = int(chapter_str)
            verse = int(verse_str)
        except ValueError:
            self.error_label.configure(text="Chapter and Verse must be numbers.")
            return

        verse_text = bible_lookup.get_verse(book, chapter, verse)
        if verse_text == "Verse not found":
            self.error_label.configure(text=f"Verse not found: {book} {chapter}:{verse}")
            return
            
        updated_verse_data = {
            "book": book,
            "chapter": chapter,
            "verse": verse,
            "text": verse_text
        }
        
        self.on_save(self.original_data, updated_verse_data)
        self.destroy()

    def _on_cancel(self):
        self.destroy() 