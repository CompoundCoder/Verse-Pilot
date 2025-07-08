import json
import os
import requests
import time

BOOK_TO_NUM_CHAPTERS = {
    "Genesis": 50, "Exodus": 40, "Leviticus": 27, "Numbers": 36, "Deuteronomy": 34,
    "Joshua": 24, "Judges": 21, "Ruth": 4, "1 Samuel": 31, "2 Samuel": 24,
    "1 Kings": 22, "2 Kings": 25, "1 Chronicles": 29, "2 Chronicles": 36,
    "Ezra": 10, "Nehemiah": 13, "Esther": 10, "Job": 42, "Psalms": 150,
    "Proverbs": 31, "Ecclesiastes": 12, "Song of Solomon": 8, "Isaiah": 66,
    "Jeremiah": 52, "Lamentations": 5, "Ezekiel": 48, "Daniel": 12, "Hosea": 14,
    "Joel": 3, "Amos": 9, "Obadiah": 1, "Jonah": 4, "Micah": 7, "Nahum": 3,
    "Habakkuk": 3, "Zephaniah": 3, "Haggai": 2, "Zechariah": 14, "Malachi": 4,
    "Matthew": 28, "Mark": 16, "Luke": 24, "John": 21, "Acts": 28, "Romans": 16,
    "1 Corinthians": 16, "2 Corinthians": 13, "Galatians": 6, "Ephesians": 6,
    "Philippians": 4, "Colossians": 4, "1 Thessalonians": 5, "2 Thessalonians": 3,
    "1 Timothy": 6, "2 Timothy": 4, "Titus": 3, "Philemon": 1, "Hebrews": 13,
    "James": 5, "1 Peter": 5, "2 Peter": 3, "1 John": 5, "2 John": 1, "3 John": 1,
    "Jude": 1, "Revelation": 22
}

BOOK_VERSE_COUNTS = {}

# The base URL for the raw JSON files
base_url = "https://raw.githubusercontent.com/kenyonbowers/Bible-JSON/main/JSON/"

for book_name, num_chapters in BOOK_TO_NUM_CHAPTERS.items():
    BOOK_VERSE_COUNTS[book_name] = {}
    for chapter_num in range(1, num_chapters + 1):
        # The URL needs to handle spaces in book names, e.g. "1 Samuel" -> "1%20Samuel"
        url_book_name = book_name.replace(" ", "%20")
        url = f"{base_url}{url_book_name}/{chapter_num}.json"
        
        print(f"Fetching {url}")
        
        retries = 3
        while retries > 0:
            try:
                response = requests.get(url)
                response.raise_for_status()  # Raise an exception for bad status codes
                chapter_data = response.json()
                num_verses = len(chapter_data.get('verses', []))
                BOOK_VERSE_COUNTS[book_name][chapter_num] = num_verses
                break  # Success, exit retry loop
            except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
                print(f"Error fetching {url}: {e}. Retrying...")
                retries -= 1
                time.sleep(1) # wait a second before retrying
        
        if retries == 0:
            print(f"Failed to fetch {url} after multiple retries.")


# Correcting book names to match existing constants
name_corrections = {
    '1 Corinthians': '1Corinthians',
    '2 Corinthians': '2Corinthians',
    '1 John': '1John',
    '2 John': '2John',
    '3 John': '3John',
    '1 Peter': '1Peter',
    '2 Peter': '2Peter',
    '1 Thessalonians': '1Thessalonians',
    '2 Thessalonians': '2Thessalonians',
    '1 Timothy': '1Timothy',
    '2 Timothy': '2Timothy',
    'Song of Solomon': 'Song of Songs',
    '1 Samuel': '1Samuel',
    '2 Samuel': '2Samuel',
    '1 Kings': '1Kings',
    '2 Kings': '2Kings',
    '1 Chronicles': '1Chronicles',
    '2 Chronicles': '2Chronicles',
}

for old_name, new_name in name_corrections.items():
    if old_name in BOOK_VERSE_COUNTS:
        BOOK_VERSE_COUNTS[new_name] = BOOK_VERSE_COUNTS.pop(old_name)


# Use pretty print for better readability
import pprint
print("BOOK_VERSE_COUNTS = \\")
pprint.pprint(BOOK_VERSE_COUNTS)

# Clean up the downloaded file if it exists
if os.path.exists('book_mapping.json'):
    os.remove('book_mapping.json') 