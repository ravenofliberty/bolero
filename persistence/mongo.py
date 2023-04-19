import logging
from typing import Union
import pymongo
import datetime
import re
from typing import List

from enum import Enum
import numpy as np
import pandas as pd

from words.word_metadata import Tags, Gender, Words, VerbForms

logger = logging.getLogger(__name__)


def get_client():
    return pymongo.MongoClient('mongodb://localhost:27017/').bolero


def ignore_case(word:str):
    return re.compile(word, re.IGNORECASE)


class PersistenceManager:
    """
    Data looks like this:
        {
            "word": "auto",
            "meaning": "car",
            "gender": "neutrum",
            "cls": "Noun",
            "example": {
                "Eines Nachts habe ich das Auto meiner Mutter zu einer Spritztour genommen":
                "One night I took my mom's car for a ride"
            },
            'tags': ['NA', 'NA', 'NA'],
            'see_also': ['NA', 'NA'],
            'practice_data': {
                "to_ger": {datetime.datetime.now().isoformat(): True},
                "to_eng": {datetime.datetime.now().isoformat(): True},
            },
            'creation_date': datetime.date(2023,4,10).isoformat(),
        }
    """

    def __init__(
            self,
            client=None
    ):
        self.client = client or get_client()

    ###############
    # Pulling data
    ###############
    def pull_data(self, word):
        logger.info(f"Data for {word=} pulled")
        data = list(self.client.bolero_data.find({"word": ignore_case(word)}))
        if len(data) != 0:
            assert len(data) == 1, f"Found multiple data entries for word {word}: {data}"
            doc = data[0]
            for key in ["word", "meaning", "gender", "cls", "example", "tags", "see_also", "practice_data", "verb_forms", "creation_date"]:
                assert key in doc.keys(), f"{key=} is missing from {doc=}"
            return data[0]
        else:
            logger.info(f"No data saved for {word}")
            return None

    def pull_meaning(self, word, data=None):
        data = data or self.pull_data(word)
        return data.get("meaning", None)

    def pull_gender(self, word, data=None):
        data = data or self.pull_data(word)
        return Gender[data.get("gender", "NA")]

    def pull_cls(self, word, data=None):
        data = data or self.pull_data(word)
        return Words[data.get("cls")]

    def pull_example(self, word, data=None):
        data = data or self.pull_data(word)
        return data.get("example", None)

    def pull_tags(self, word, data=None):
        data = data or self.pull_data(word)
        tags = data.get("tags", [])
        return [Tags[tag] for tag in tags]

    def pull_see_also(self, word, data=None):
        data = data or self.pull_data(word)
        return data.get("see_also", [])

    def pull_practice_data(self, word, data=None):
        data = data or self.pull_data(word)
        return data.get("practice_data", None)

    def pull_verb_forms(self, word, data=None):
        data = data or self.pull_data(word)
        cls = self.pull_cls(word=word, data=data)
        assert cls == Words.Verb, f"Verb forms are only available for verbs, not {cls}"
        return VerbForms(data.get("verb_forms", {person: None for person in VerbForms.get_persons()}))

    def pull_creation_date(self, word, data=None):
        data = data or self.pull_data(word)
        return datetime.date.fromisoformat(data.get("creation_date", None))

    ###############
    # Updating data
    ###############

    def update_meaning(self, word, meaning: str):
        self.client.bolero_data.update_one({"word": ignore_case(word)}, {"$set": {"meaning": meaning}}, upsert=True)

    def update_gender(self, word, gender: str):
        assert gender in Gender.__members__.keys(), f"{gender=} doesn't match any key in Gender enum"
        self.client.bolero_data.update_one({"word": ignore_case(word)}, {"$set": {"gender": gender}}, upsert=True)

    def update_cls(self, word, cls: str):
        assert cls in Words.__members__.keys(), f"{cls=} doesn't match any key in Words enum"
        self.client.bolero_data.update_one({"word": ignore_case(word)}, {"$set": {"cls": cls}}, upsert=True)

    def update_example(self, word, example: str):
        self.client.bolero_data.update_one({"word": ignore_case(word)}, {"$set": {"example": example}}, upsert=True)

    def update_tags(self, word, tags: List[str]):
        for tag in tags:
            assert tag in Tags.__members__.keys(), f"{tag=} doesn't match any key in Tags enum"
        self.client.bolero_data.update_one({"word": ignore_case(word)}, {"$set": {"tags": tags}}, upsert=True)

    def update_see_also(self, word, see_also: str):
        self.client.bolero_data.update_one({"word": ignore_case(word)}, {"$set": {"see_also": see_also}}, upsert=True)

    def update_practice_data(self, word, practice_data: dict):
        self.client.bolero_data.update_one({"word": ignore_case(word)}, {"$set": {"practice_data": practice_data}}, upsert=True)

    def update_verb_forms(self, word, forms: dict):
        """ Verb only, rest get empty dicts"""
        self.client.bolero_data.update_one({"word": ignore_case(word)}, {"$set": {"verb_forms": forms}}, upsert=True)

    def update_creation_date(self, word, creation_date: str):
        self.client.bolero_data.update_one({"word": ignore_case(word)}, {"$set": {"creation_date": creation_date}}, upsert=True)

    def update_all(self, json):
        """ PersistenceManager.update_all(Word.to_json()) """
        for key in ["word", "meaning", "gender", "example", "tags", "see_also", "practice_data", "verb_forms"]:
            assert key in json.keys(), f"{key=} is missing from {json=}"

        word = json["word"]
        if self.pull_data(word) is None:
            self.client.bolero_data.insert_one({
                "word": word,
                **{k: None for k in ["meaning", "gender", "example", "tags", "see_also", "practice_data", "verb_forms"]}
            })
        self.update_meaning(word, json["meaning"])
        self.update_gender(word, json["gender"])
        self.update_cls(word, json["cls"])
        self.update_example(word, json["example"])
        self.update_tags(word, json["tags"])
        self.update_see_also(word, json["see_also"])
        self.update_practice_data(word, json["practice_data"])
        self.update_verb_forms(word, json["verb_forms"])
        self.update_creation_date(word, json["creation_date"])
