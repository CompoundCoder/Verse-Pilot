_last_book = None
_last_chapter = None


def set_last_confirmed(book: str, chapter: int):
    global _last_book, _last_chapter
    _last_book = book
    _last_chapter = chapter


def get_last_confirmed() -> tuple[str | None, int | None]:
    return _last_book, _last_chapter


def reset():
    global _last_book, _last_chapter
    _last_book = None
    _last_chapter = None 