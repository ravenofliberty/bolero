import logging

from words.word_metadata import VerbForms
from words.word import Word

logger = logging.getLogger(__name__)

"""
Word object handles all states. Persistence manager (PM) only pulls and pushes updates to the DB. 
Word object only interacts with the DB via PM. 
"""


class Verb(Word):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __getattr__(self, item):
        if item in ["ich", "du", "er", "wir", "ihr", "sie"]:
            return getattr(self.verb_forms, item)

    def __repr__(self):
        return f"{self.word.lower()} ({str(self.cls.name)}) - " \
               f"Eng: {self.meaning}"

    def to_json(self):
        res = super().to_json()
        res["forms"] = self.verb_forms.to_json()
        return res


