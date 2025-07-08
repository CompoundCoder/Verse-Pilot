import json
import os
import logging
from typing import Optional

# Global Bible dictionary, structured for efficient lookups.
# Format: { "Genesis": { "1": { "1": "Verse text..." } } }
BIBLE_DATA = {}

def load_bible(path="assets/data/kjv_nested.json"):
    """
    Loads and processes the Bible JSON file. It is designed to be resilient,
    transforming a flat list of verse objects into the required nested
    dictionary structure for efficient lookups.
    """
    global BIBLE_DATA
    logging.info(f"📖 Attempting to load Bible file from: {path}")

    try:
        if not os.path.exists(path):
            raise FileNotFoundError(f"❌ Bible file not found at the specified path: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logging.info(f"✅ Raw Bible JSON loaded. Top-level type is: {type(data).__name__}")

        if not isinstance(data, list):
            raise TypeError(f"❌ Expected a list of verse objects, but got {type(data).__name__}.")

        logging.info("Transforming flat list into a nested dictionary based on 'name' and 'verse' keys...")
        nested_data = {}
        processed_count = 0
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                logging.warning(f"Skipping malformed entry at index {i}: not a dictionary.")
                continue

            name = item.get("name")
            text = item.get("verse")

            if not name or not text:
                logging.warning(f"Skipping entry at index {i} due to missing 'name' or 'verse' key: {item}")
                continue

            try:
                # Parse "Revelation 6:12" into book='Revelation', chapter='6', verse_num='12'
                book_part, ref_part = name.rsplit(' ', 1)
                chapter, verse_num = ref_part.split(':')

                # Create nested dictionaries on demand.
                if book_part not in nested_data:
                    nested_data[book_part] = {}
                if chapter not in nested_data[book_part]:
                    nested_data[book_part][chapter] = {}
                
                nested_data[book_part][chapter][verse_num] = text
                processed_count += 1
            except (ValueError, IndexError) as e:
                logging.warning(f"Skipping entry at index {i}. Could not parse 'name' field ('{name}'): {e}")
                continue
        
        if processed_count == 0:
            raise ValueError("❌ No valid verse data was loaded from the file. Check the JSON structure and keys ('name', 'verse').")

        BIBLE_DATA = nested_data
        logging.info(f"✅ Bible data transformed successfully. Processed {processed_count} verses into {len(BIBLE_DATA)} books.")

    except Exception as e:
        logging.error(f"❌ A critical error occurred during Bible loading: {e}", exc_info=True)
        BIBLE_DATA = {}

def get_verse(book: str, chapter: int, verse: int) -> Optional[str]:
    """
    Fetches a single verse by reference from the in-memory Bible data.
    This function performs a case-insensitive lookup for the book name.
    """
    if not BIBLE_DATA:
        return "⚠️ Bible not loaded. Please check logs."

    if not isinstance(book, str):
        logging.warning(f"⚠️ Invalid 'book' argument: expected a string, but got {type(book).__name__}. Cannot perform lookup.")
        return None

    try:
        # Find the correct book key with a case-insensitive search.
        book_key = next((k for k in BIBLE_DATA if k.lower() == book.lower()), None)
        if not book_key:
            raise KeyError(f"Book '{book}' not found.")

        chapter_str = str(chapter)
        verse_str = str(verse)

        return BIBLE_DATA[book_key][chapter_str][verse_str]

    except KeyError:
        logging.warning(f"⚠️ Verse not found: {book.title()} {chapter}:{verse}")
        return "⚠️ Verse not found."

# Load the Bible into memory as soon as the module is imported.
load_bible()

if __name__ == '__main__':
    print("--- Testing Bible Lookup ---")
    # Note: This test requires a kjv.json file in assets/data/.
    # Example: {"John": {"3": {"16": "For God so loved the world..."}}}
    verse_text = get_verse("John", 3, 16)
    if verse_text:
        print("John 3:16:", verse_text)
    else:
        print("John 3:16 not found (is assets/data/kjv.json populated?).")

    verse_text_2 = get_verse("1st John", 1, 9) # Test alternate naming
    if verse_text_2:
        print("1 John 1:9:", verse_text_2)

    # Test not found
    get_verse("Genesis", 99, 99) 