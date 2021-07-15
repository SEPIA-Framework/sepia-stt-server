# MIT License

# Copyright (c) 2018-2019 Groupe Allo-Media

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from typing import Dict, Optional

from .base import Language

#
# CONSTANTS
# Built once on import.
#

# Those words multiplies lesser numbers (see Rules)
# Exception: "(de) milliards" that can multiply bigger numbers ("milliards de milliards")
# Special case: "cent" is processed apart.
MULTIPLIERS = {
    "mil": 1000,
    "mille": 1000,
    "milles": 1000,
    "million": 1000000,
    "millions": 1000000,
    "milliard": 1000000000,
    "milliards": 1000000000,
}


# Units are terminals (see Rules)
# Special case: "zéro" is processed apart.
UNITS: Dict[str, int] = {
    word: value
    for value, word in enumerate(
        "un deux trois quatre cinq six sept huit neuf".split(), 1
    )
}
# Unit variants
UNITS["une"] = 1


# Single tens are terminals (see Rules)
STENS: Dict[str, int] = {
    word: value
    for value, word in enumerate(
        "dix onze douze treize quatorze quinze seize dix-sept dix-huit dix-neuf".split(),
        10,
    )
}


# Ten multiples
# Ten multiples may be followed by a unit only;
# Exceptions: "soixante" & "quatre-vingt" (see Rules)
MTENS: Dict[str, int] = {
    word: value * 10
    for value, word in enumerate(
        "vingt trente quarante cinquante soixante septante huitante nonante".split(), 2
    )
}
# Variants
MTENS["quatre-vingt"] = 80
MTENS["octante"] = 80

# Ten multiples that can be combined with STENS
MTENS_WSTENS = {"soixante", "quatre-vingt"}


# "cent" has a special status (see Rules)
HUNDRED = {"cent": 100, "cents": 100}


# Composites are tens already composed with terminals in one word.
# Composites are terminals.

COMPOSITES: Dict[str, int] = {
    "-".join((ten_word, unit_word)): ten_val + unit_val
    for ten_word, ten_val in MTENS.items()
    for unit_word, unit_val in UNITS.items()
    if unit_val != 1
}

COMPOSITES.update(
    {
        "-".join((ten_word, et_word)): ten_val + et_val
        for ten_word, ten_val in MTENS.items()
        for et_word, et_val in (("et-un", 1), ("et-une", 1))
        if 10 < ten_val <= 90
    }
)

COMPOSITES["quatre-vingt-un"] = 81

COMPOSITES.update(
    {
        "-".join((ten_word, sten_word)): ten_val + sten_val
        for ten_word, ten_val in (("soixante", 60), ("quatre-vingt", 80))
        for sten_word, sten_val in STENS.items()
    }
)

COMPOSITES["soixante-et-onze"] = 71

# All number words

NUMBERS = MULTIPLIERS.copy()
NUMBERS.update(UNITS)
NUMBERS.update(STENS)
NUMBERS.update(MTENS)
NUMBERS.update(HUNDRED)
NUMBERS.update(COMPOSITES)
NUMBERS["quatre-vingts"] = 80

IRR_ORD = {
    "premier": ("un", "1er"),
    "première": ("un", "1ère"),
    "second": ("deux", "2nd"),
    "seconde": ("deux", "2nde"),
}


class French(Language):

    MULTIPLIERS = MULTIPLIERS
    UNITS = UNITS
    STENS = STENS
    MTENS = MTENS
    MTENS_WSTENS = MTENS_WSTENS
    HUNDRED = HUNDRED
    NUMBERS = NUMBERS

    SIGN = {"plus": "+", "moins": "-"}
    ZERO = {"zéro"}
    DECIMAL_SEP = "virgule"
    DECIMAL_SYM = ","

    AND_NUMS = {"un", "une", "unième", "onze", "onzième"}
    AND = "et"
    NEVER_IF_ALONE = {"un", "une"}

    # Relaxed composed numbers (two-words only)
    # start => (next, target)
    RELAXED = {"quatre": ("vingt", "quatre-vingt")}

    def ord2card(self, word: str) -> Optional[str]:
        """Convert ordinal number to cardinal.

        Return None if word is not an ordinal or is better left in letters.
        """
        if word in IRR_ORD:
            return IRR_ORD[word][0]
        plur_suff = word.endswith("ièmes")
        sing_suff = word.endswith("ième")
        if not (plur_suff or sing_suff):
            return None
        source = word[:-5] if plur_suff else word[:-4]
        if source == "cinqu":
            source = "cinq"
        elif source == "neuv":
            source = "neuf"
        elif source not in self.NUMBERS:
            source = source + "e"
            if source not in self.NUMBERS:
                return None
        return source

    def num_ord(self, digits: str, original_word: str) -> str:
        """Add suffix to number in digits to make an ordinal"""
        if original_word in IRR_ORD:
            return IRR_ORD[original_word][1]
        return f"{digits}ème" if original_word.endswith("e") else f"{digits}èmes"

    def normalize(self, word: str) -> str:
        return word.replace("vingts", "vingt")
