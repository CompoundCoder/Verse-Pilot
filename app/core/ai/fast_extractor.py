import re
import logging
from app.core.verse_buffer import VerseCandidate
from app.core.bible.constants import BOOK_ALIASES, BOOK_TO_NUM_CHAPTERS, BOOK_VERSE_COUNTS
from app.core.bible.bible_lookup import get_verse

spoken_to_number = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20,
}

class FastVerseExtractor:
    REGEX_PATTERNS = [
        re.compile(r"\b(?P<book>\w+(?:\s+\w+)*?)\s+chapter\s+(?P<chapter>\d{1,3})\s+(?:verse\s+)?(?P<verse>\d{1,3})\b", re.IGNORECASE),
        re.compile(r"\b(?P<book>\w+(?:\s+\w+)*?)\s+(?P<chapter>\d{1,3})[:\s]+(?P<verse>\d{1,3})\b", re.IGNORECASE),
        re.compile(r"\b(?P<book>\w+(?:\s+\w+)*?)\s+chapter\s+(?P<chapter_word>\w+)\s+verse\s+(?P<verse_word>\w+)\b", re.IGNORECASE),
    ]

    @staticmethod
    def normalize_number(val: str) -> int | None:
        if val is None:
            return None
        try:
            return int(val)
        except ValueError:
            return spoken_to_number.get(val.lower())

    @staticmethod
    def extract_candidate(transcript: str) -> VerseCandidate | None:
        for pattern in FastVerseExtractor.REGEX_PATTERNS:
            match = pattern.search(transcript)
            if not match:
                continue

            book_raw = match.group("book").strip().title()
            book = BOOK_ALIASES.get(book_raw, book_raw)
            chapter_str = match.groupdict().get("chapter") or match.groupdict().get("chapter_word")
            verse_str = match.groupdict().get("verse") or match.groupdict().get("verse_word")

            chapter_num = FastVerseExtractor.normalize_number(chapter_str)
            verse_num = FastVerseExtractor.normalize_number(verse_str)

            if not all([book, chapter_num, verse_num]):
                continue

            # --- Start New Validation ---
            # 1. Validate Book
            if book not in BOOK_TO_NUM_CHAPTERS:
                logging.debug(f"[FastExtractor] Blocked invalid book: {book}")
                continue

            # 2. Validate Chapter
            max_chapters = BOOK_TO_NUM_CHAPTERS[book]
            if not (1 <= chapter_num <= max_chapters):
                logging.debug(
                    f"[FastExtractor] Blocked invalid chapter: "
                    f"{book} {chapter_num}"
                )
                continue
            
            # 3. Validate Verse
            max_verses = BOOK_VERSE_COUNTS[book].get(chapter_num, 0)
            if not (1 <= verse_num <= max_verses):
                logging.debug(
                    f"[FastExtractor] Blocked invalid verse: "
                    f"{book} {chapter_num}:{verse_num}"
                )
                continue
            
            # --- End New Validation ---

            # If all checks pass, create the candidate
            return VerseCandidate(
                book=book,
                chapter=chapter_num,
                verse=verse_num,
                transcript_snippet=transcript,
                confidence_score=0.95,
                source="fast",
                status="pending",
                is_partial=False,
                review_required=False,
                explanation="Matched and validated by fast extractor"
            )

        return None 