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
# Special case: "hundred" is processed apart.
MULTIPLIERS = {
    "tausend": 1_000,
    "million": 1_000_000,
    "millionen": 1_000_000,
    "milliarde": 1_000_000_000,
    "milliarden": 1_000_000_000,
    "billion": 1_000_000_000_000,
    "billionen": 1_000_000_000_000,
    "billiarde": 1_000_000_000_000_000,
    "billiarden": 1_000_000_000_000_000,
    "trillion": 1_000_000_000_000_000_000,
    "trillionen": 1_000_000_000_000_000_000,
    "trilliarde": 1_000_000_000_000_000_000_000,
    "trilliarden": 1_000_000_000_000_000_000_000,
}

# Units are terminals (see Rules)
# Special case: "zero/O" is processed apart.
UNITS: Dict[str, int] = {
    word: value
    for value, word in enumerate(
        "eins zwei drei vier fünf sechs sieben acht neun".split(), 1
    )
}
# Unit variants
UNITS["ein"] = 1
UNITS["eine"] = 1

# Single tens are terminals (see Rules)
STENS: Dict[str, int] = {
    word: value
    for value, word in enumerate(
        "zehn elf zwölf dreizehn vierzehn fünfzehn sechzehn siebzehn achtzehn neunzehn".split(),
        10,
    )
}

# Ten multiples
# Ten multiples may be followed by a unit only;
MTENS: Dict[str, int] = {
    word: value * 10
    for value, word in enumerate(
        "zwanzig dreißig vierzig fünfzig sechzig siebzig achtzig neunzig".split(), 2
    )
}

# Ten multiples that can be combined with STENS
# MTENS_WSTENS: Set[str] = set()

# "hundred" has a special status (see Rules)
HUNDRED = {"hundert": 100}  # einhundert?

# All number words

NUMBERS = MULTIPLIERS.copy()
NUMBERS.update(UNITS)
NUMBERS.update(STENS)
NUMBERS.update(MTENS)
NUMBERS.update(HUNDRED)
# NUMBERS.update(COMPOSITES) # COMPOSITES are already in STENS for the German language

AND = "und"
ZERO = {"null"}

ALL_WORDS = (
    list(UNITS.keys())
    + list(STENS.keys())
    + list(MULTIPLIERS.keys())
    + list(MTENS.keys())
    + list(HUNDRED.keys())
    + list(ZERO)
    + list([AND])
)
# Sort all numbers by length and start with the longest
ALL_WORDS_SORTED_REVERSE = sorted(ALL_WORDS, key=len, reverse=True)


class German(Language):

    # TODO: can this be replaced by NUMBERS ? (or extended NUMBERS)
    # Currently it has to be imported into 'parsers' as well ...
    NUMBER_DICT_GER = {
        "null": 0,
        "eins": 1,
        "ein": 1,
        "eine": 1,
        "zwei": 2,
        "drei": 3,
        "vier": 4,
        "fünf": 5,
        "sechs": 6,
        "sieben": 7,
        "acht": 8,
        "neun": 9,
        "zehn": 10,
        "elf": 11,
        "zwölf": 12,
        "dreizehn": 13,
        "vierzehn": 14,
        "fünfzehn": 15,
        "sechzehn": 16,
        "siebzehn": 17,
        "achzehn": 18,
        "neunzehn": 19,
        "zwanzig": 20,
        "dreißig": 30,
        "vierzig": 40,
        "fünfzig": 50,
        "sechzig": 60,
        "siebzig": 70,
        "achtzig": 80,
        "neunzig": 90,
        "hundert": 100,
        "tausend": 1_000,
        "million": 1_000_000,
        "millionen": 1_000_000,
        "milliarde": 1_000_000_000,
        "milliarden": 1_000_000_000,
        "billion": 1_000_000_000_000,
        "billionen": 1_000_000_000_000,
        "billiarde": 1_000_000_000_000_000,
        "billiarden": 1_000_000_000_000_000,
        "trillion": 1_000_000_000_000_000_000,
        "trillionen": 1_000_000_000_000_000_000,
        "trilliarde": 1_000_000_000_000_000_000_000,
        "trilliarden": 1_000_000_000_000_000_000_000,
    }

    MULTIPLIERS = MULTIPLIERS
    UNITS = UNITS
    STENS = STENS
    MTENS = MTENS
    # MTENS_WSTENS = MTENS_WSTENS
    HUNDRED = HUNDRED
    NUMBERS = NUMBERS

    SIGN = {"plus": "+", "minus": "-"}
    ZERO = ZERO
    DECIMAL_SEP = "komma"
    DECIMAL_SYM = ","

    # AND_NUMS = set(UNITS.keys()).union(set(STENS.keys()).union(set(MTENS.keys())))
    AND = AND

    # NEVER_IF_ALONE = {"ein", "eine"}  # TODO: use

    # Relaxed composed numbers (two-words only)
    # start => (next, target)
    # RELAXED: Dict[str, Tuple[str, str]] = {}

    def ord2card(self, word: str) -> Optional[str]:
        """Convert ordinal number to cardinal.

        THIS IS STILL IN DEVELOPMENT FOR GERMAN LANGUAGE

        Return None if word is not an ordinal or is better left in letters
        as is the case for fist and second.
        """
        plur_suff = word.endswith("ster") and not word.startswith(
            "sechster"
        )  # Zwanzigster, Dreißigster, Hundertster, Tausendster ...
        sing_suff = word.endswith("ter")  # Zweiter, Vierter, Fünfter, Sechster
        if not (plur_suff or sing_suff):
            if word.endswith("erster"):
                source = word.replace("erster", "eins")
            elif word.endswith("second"):
                source = word.replace("dritter", "drei")
            elif word.endswith("siebter"):
                source = word.replace("siebter", "sieben")
            elif word.endswith("achter"):
                source = word.replace("achter", "acht")
            else:
                return None
        else:
            source = word[:-4] if plur_suff else word[:-3]
        if source in MTENS.keys() or source in MULTIPLIERS.keys():
            source = source + "ster"
        else:
            source = source + "ter"

        if source not in self.NUMBERS:
            return None
        return source

    def num_ord(self, digits: str, original_word: str) -> str:
        """Add suffix to number in digits to make an ordinal

        THIS IS STILL IN DEVELOPMENT FOR GERMAN LANGUAGE

        """
        sf = original_word[-3:] if original_word.endswith("s") else original_word[-2:]
        return f"{digits}{sf}"

    def normalize(self, word: str) -> str:
        return word

    def split_number_word(self, word: str) -> str:
        """Splits number words into separate words, e.g. einhundertfünzig-> ein hundert fünfzig"""

        # TODO: this can probably be optimized because complex number-words will always start with
        # "ein", "eine", "zwei", ... "neun", "hundert", "tausend", ... I think
        text = word.lower()
        invalid_word = ""
        result = ""
        while len(text) > 0:
            # start with the longest
            found = False
            for sw in ALL_WORDS_SORTED_REVERSE:
                # Check at the beginning of the current sentence for the longest word in ALL_WORDS
                if text.startswith(sw):
                    if len(invalid_word) > 0:
                        result += invalid_word + " "
                        invalid_word = ""

                    result += sw + " "
                    text = text[len(sw):]
                    found = True
                    break
            if not found:
                # current beginning could not be assigned to a word
                if not text[0] == " ":
                    invalid_word += text[0:1]
                    text = text[1:]
                else:
                    if len(invalid_word) > 0:
                        result += invalid_word + " "
                        invalid_word = ""
                    text = text[1:]

        if len(invalid_word) > 0:
            result += invalid_word + " "

        return result
