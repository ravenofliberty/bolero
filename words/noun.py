import datetime
import logging
from typing import List, Dict
from enum import Enum
import inspect

import pandas as pd
import numpy as np

from persistence.mongo import PersistenceManager
from words.word_metadata import Tags, Gender, IndefiniteArticle, DefiniteArticle, ARTICLE_MAPPING_NOMINATIVE
from words.word import Word

logger = logging.getLogger(__name__)

"""
Word object handles all states. Persistence manager (PM) only pulls and pushes updates to the DB. 
Word object only interacts with the DB via PM. 
"""


class Noun(Word):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f"" \
               f"{ARTICLE_MAPPING_NOMINATIVE[self.gender]['definite'].name} " \
               f"{self.word.capitalize()} ({str(self.cls.name)}) - " \
               f"Eng: {self.meaning}"
