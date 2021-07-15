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

from typing import Dict, Optional, Set, Tuple

from .base import Language

#
# CONSTANTS
# Built once on import.
#

# Those words multiplies lesser numbers (see Rules)
# Special case: "hundred" is processed apart.
MULTIPLIERS = {
    "thousand": 1_000,
    "thousands": 1_000,
    "million": 1_000_000,
    "millions": 1_000_000,
    "billion": 1_000_000_000,
    "billions": 1_000_000_000,
    "trillion": 1_000_000_000_000,
    "trillions": 1_000_000_000_000,
}


# Units are terminals (see Rules)
# Special case: "zero/O" is processed apart.
UNITS: Dict[str, int] = {
    word: value
    for value, word in enumerate(
        "one two three four five six seven eight nine".split(), 1
    )
}

# Single tens are terminals (see Rules)
STENS: Dict[str, int] = {
    word: value
    for value, word in enumerate(
        "ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split(),
        10,
    )
}


# Ten multiples
# Ten multiples may be followed by a unit only;
MTENS: Dict[str, int] = {
    word: value * 10
    for value, word in enumerate(
        "twenty thirty forty fifty sixty seventy eighty ninety".split(), 2
    )
}

# Ten multiples that can be combined with STENS
MTENS_WSTENS: Set[str] = set()


# "hundred" has a special status (see Rules)
HUNDRED = {"hundred": 100, "hundreds": 100}


# Composites are tens already composed with terminals in one word.
# Composites are terminals.

COMPOSITES: Dict[str, int] = {
    "-".join((ten_word, unit_word)): ten_val + unit_val
    for ten_word, ten_val in MTENS.items()
    for unit_word, unit_val in UNITS.items()
}

# All number words

NUMBERS = MULTIPLIERS.copy()
NUMBERS.update(UNITS)
NUMBERS.update(STENS)
NUMBERS.update(MTENS)
NUMBERS.update(HUNDRED)
NUMBERS.update(COMPOSITES)

RAD_MAP = {"fif": "five", "eigh": "eight", "nin": "nine", "twelf": "twelve"}


class English(Language):

    MULTIPLIERS = MULTIPLIERS
    UNITS = UNITS
    STENS = STENS
    MTENS = MTENS
    MTENS_WSTENS = MTENS_WSTENS
    HUNDRED = HUNDRED
    NUMBERS = NUMBERS

    SIGN = {"plus": "+", "minus": "-"}
    ZERO = {"zero", "o"}
    DECIMAL_SEP = "point"
    DECIMAL_SYM = "."

    AND_NUMS: Set[str] = set()
    AND = "and"
    NEVER_IF_ALONE = {"one"}

    # Relaxed composed numbers (two-words only)
    # start => (next, target)
    RELAXED: Dict[str, Tuple[str, str]] = {}

    def ord2card(self, word: str) -> Optional[str]:
        """Convert ordinal number to cardinal.

        Return None if word is not an ordinal or is better left in letters.
        """
        plur_suff = word.endswith("ths")
        sing_suff = word.endswith("th")
        if not (plur_suff or sing_suff):
            if word.endswith("first"):
                source = word.replace("first", "one")
            elif word.endswith("second"):
                source = word.replace("second", "two")
            elif word.endswith("third"):
                source = word.replace("third", "three")
            else:
                return None
        else:
            source = word[:-3] if plur_suff else word[:-2]
        if source in RAD_MAP:
            source = RAD_MAP[source]
        elif source.endswith("ie"):
            source = source[:-2] + "y"
        elif source.endswith("fif"):  # fifth -> five
            source = source[:-1] + "ve"
        elif source.endswith("eigh"):  # eighth -> eight
            source = source + "t"
        elif source.endswith("nin"):  # ninth -> nine
            source = source + "e"
        if source not in self.NUMBERS:
            return None
        return source

    def num_ord(self, digits: str, original_word: str) -> str:
        """Add suffix to number in digits to make an ordinal"""
        sf = original_word[-3:] if original_word.endswith("s") else original_word[-2:]
        return f"{digits}{sf}"

    def normalize(self, word: str) -> str:
        return word
