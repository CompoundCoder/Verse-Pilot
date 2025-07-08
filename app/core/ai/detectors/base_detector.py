from abc import ABC, abstractmethod

class BaseDetector(ABC):
    @abstractmethod
    def detect(self, transcript: str) -> dict:
        """
        Takes a string of transcribed text.
        Returns a dict like: {"book": "John", "chapter": 1, "verse": 1}
        or an empty dict if no verse is found.
        """
        pass 