from enum import Enum


class Words(Enum):
    Noun = 1
    Verb = 2
    Adjective = 3


class Tags(Enum):
    """
    Simple tags to help with generating random words that have something in common.
    """
    NA = 0
    Character = 1
    Color = 2
    Family = 3


class DefinitieArticle(Enum):
    der = 1
    die = 2
    das = 3
    dem = 4
    den = 5
    des = 6


class IndefiniteArticle(Enum):
    ein = 1
    eine = 2
    einen = 3
    einem = 4
    einer = 5
    eines = 6


class Gender(Enum):
    masculinum = 1
    femininum = 2
    neutrum = 3
    NA = 4


ARTICLE_MAPPING_NOMINATIVE = {
    Gender.masculinum: {'definite': DefinitieArticle.der, 'indefinite': IndefiniteArticle.ein},
    Gender.femininum: {'definite': DefinitieArticle.die, 'indefinite': IndefiniteArticle.eine},
    Gender.neutrum: {'definite': DefinitieArticle.das, 'indefinite': IndefiniteArticle.ein},
}
