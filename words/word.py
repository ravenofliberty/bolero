import importlib
import logging
import datetime
from typing import List, Dict
from enum import Enum
import inspect

import pandas as pd
import numpy as np

from persistence.mongo import PersistenceManager
from words.word_metadata import Tags, Gender, IndefiniteArticle, DefiniteArticle, Words, VerbForms

logger = logging.getLogger(__name__)

"""
Word object handles all states. Persistence manager (PM) only pulls and pushes updates to the DB. 
Word object only interacts with the DB via PM. 
"""


class Word:
    def __init__(
            self,
            word: str,
            gender: Gender = None,
            cls: Words = None,
            meaning: str = None,
            example: Dict = None,
            tags: List[Tags] = [],
            see_also: List[str] = [],  # List of other Words
            practice_data: Dict = {},
            verb_forms: VerbForms = None,
            offline_mode=True,
    ):
        self.word = word

        self.persistence_manager = PersistenceManager()
        data = self.persistence_manager.pull_data(word) if not offline_mode else None
        self.meaning = meaning or self.persistence_manager.pull_meaning(word, data)
        self.gender = gender or self.persistence_manager.pull_gender(word, data)
        self.cls = cls or self.persistence_manager.pull_cls(word, data)
        self.example = example or self.persistence_manager.pull_example(word, data)
        self.tags = tags or self.persistence_manager.pull_tags(word, data)
        self.see_also = see_also or self.persistence_manager.pull_see_also(word, data)
        self.practice_data = practice_data or self.persistence_manager.pull_practice_data(word, data)
        self.verb_forms = verb_forms or self.persistence_manager.pull_verb_forms(word, data)

    def to_json(self):
        res = {}
        for arg in inspect.getfullargspec(Word.__init__).args:
            if arg == 'self':
                continue
            else:
                param = getattr(self, arg)
            res[arg] = param.name if isinstance(param, Enum) else param
        return res

    @classmethod
    def from_json(cls, _json):
        """ PersistenceManager.pull_data() """
        json = {k: v for k, v in _json.items()} # copy
        if json.get("verb_forms", None) is not None:
            json["verb_forms"] = VerbForms(**json["verb_forms"])
        json["gender"] = Gender[json["gender"]]
        json["tags"] = [Tags[t] for t in json["tags"]]

        module = importlib.import_module(f"words.{json['cls'].lower()}")
        target_cls = getattr(module,json['cls'].lower().capitalize())
        json["cls"] = Words[json["cls"]]

        return target_cls(**{k: v for k,v in json.items() if k != "_id"})


def get_word(word: str):
    pm = PersistenceManager()
    json = pm.pull_data(word)
    return Word.from_json(json)