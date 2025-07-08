import uuid
from datetime import datetime
from typing import List, Optional


class VerseCandidate:
    def __init__(
        self,
        book: str,
        chapter: int,
        verse: int,
        transcript_snippet: str,
        confidence_score: float,
        source: str,  # "fast" or "slow"
        status: str = "pending",  # "pending", "live", "discarded"
        validation_status: str = "unknown", # "unknown", "valid", "invalid_book", "invalid_chapter"
        is_partial: bool = False,
        review_required: bool = False,
        explanation: str = "",
    ):
        self.id = str(uuid.uuid4())
        self.book = book
        self.chapter = chapter
        self.verse = verse
        self.transcript_snippet = transcript_snippet
        self.confidence_score = confidence_score
        self.source = source
        self.status = status
        self.validation_status = validation_status
        self.timestamp = datetime.utcnow()
        self.is_partial = is_partial
        self.review_required = review_required
        self.explanation = explanation

    def to_dict(self):
        return {
            "id": self.id,
            "book": self.book,
            "chapter": self.chapter,
            "verse": self.verse,
            "transcript_snippet": self.transcript_snippet,
            "confidence_score": self.confidence_score,
            "source": self.source,
            "status": self.status,
            "validation_status": self.validation_status,
            "timestamp": self.timestamp.isoformat(),
            "is_partial": self.is_partial,
            "review_required": self.review_required,
            "explanation": self.explanation,
        }


class VerseBuffer:
    def __init__(self):
        self.candidates: List[VerseCandidate] = []

    def add_candidate(self, candidate: VerseCandidate):
        self.candidates.append(candidate)

    def get_pending(self) -> List[VerseCandidate]:
        return [v for v in self.candidates if v.status == "pending"]

    def get_live(self) -> List[VerseCandidate]:
        return [v for v in self.candidates if v.status == "live"]

    def get_discarded(self) -> List[VerseCandidate]:
        return [v for v in self.candidates if v.status == "discarded"]

    def promote_to_live(self, candidate_id: str):
        for v in self.candidates:
            if v.id == candidate_id:
                v.status = "live"

    def discard(self, candidate_id: str):
        for v in self.candidates:
            if v.id == candidate_id:
                v.status = "discarded"

    def clear_old(self, max_age_minutes=30):
        """Optional: Clear old candidates from the buffer after some time"""
        cutoff = datetime.utcnow().timestamp() - (max_age_minutes * 60)
        self.candidates = [
            v for v in self.candidates if v.timestamp.timestamp() > cutoff
        ] 