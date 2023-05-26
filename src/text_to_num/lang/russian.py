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
    "тысяча": 1_000,
    "тысячи": 1_000,
    "тысяч": 1_000,
    "миллион": 1_000_000,
    "миллиона": 1_000_000,
    "миллионов": 1_000_000,
    "миллиард": 1_000_000_000,
    "миллиарда": 1_000_000_000,
    "миллиардов": 1_000_000_000,
    "триллион": 1_000_000_000_000,
    "триллиона": 1_000_000_000_000,
    "триллионов": 1_000_000_000_000,
}


# Units are terminals (see Rules)
# Special case: "zero/O" is processed apart.
UNITS: Dict[str, int] = {
    word: value
    for value, word in enumerate(
        "один два три четыре пять шесть семь восемь девять".split(), 1
    )
}

# Single tens are terminals (see Rules)
STENS: Dict[str, int] = {
    word: value
    for value, word in enumerate(
        "десять одиннадцать двенадцать тринадцать четырнадцать пятьнадцать "
        "шестьнадцать семьнадцать восемьнадцать девятнадцать".split(),
        10,
    )
}


# Ten multiples
# Ten multiples may be followed by a unit only;
MTENS: Dict[str, int] = {
    word: value * 10
    for value, word in enumerate(
        "двадцать тридцать сорок пятьдесят шестьдесят семьдесят восемьдесят девяносто".split(), 2
    )
}

# Ten multiples that can be combined with STENS
MTENS_WSTENS: Set[str] = set()


# "hundred" has a special status (see Rules)
HUNDRED = {
    "сотня": 100,
    "сотни": 100,
    "сотен": 100,
}

MHUNDREDS = {
    "сто": 100,
    "двести": 200,
    "триста": 300,
    "тристо": 300,
    "четыреста": 400,
    "четыресто": 400,
    "пятьсот": 500,
    "пятсот": 500,
    "шестьсот": 600,
    "шестсот": 600,
    "семьсот": 700,
    "семсот": 700,
    "восемьсот": 800,
    "восемсот": 800,
    "девятьсот": 900,
    "девятсот": 900,
}

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
NUMBERS.update(MHUNDREDS)
NUMBERS.update(COMPOSITES)

RAD_MAP = {
    "перв": "один",
    "втор": "два",
    "трет": "три",
    "четверт": "четыре",
    "четвёрт": "четыре",
    "пят": "пять",
    "шест": "шесть",
    "седьм": "семь",
    "восьм": "восемь",
    "девят": "девять",
    "десят": "десять",
    "двадцат": "двадцать",
    "тридцат": "тридцать",
    "сороков": "сорок",
    "пятидесят": "пятьдесят",
    "шестидесят": "шестьдесят",
    "семидесят": "семьдесят",
    "восмидесят": "восемьдесят",
    "девяност": "девяносто",
    "сот": "сто",
    "тысячн": "тысяча",
    "миллионн": "миллион",
    "миллиардн": "миллиард",
    "триллионн": "триллиард",
}

SKLON_MAP = {
    "одна": "один",
    "две": "два",
    "одинадцать": "одиннадцать",
    "пятнадцать": "пятьнадцать",
    "шестнадцать": "шестьнадцать",
    "семнадцать": "семьнадцать",
    "восемнадцать": "восемьнадцать",
}


class Russian(Language):
    MULTIPLIERS = MULTIPLIERS
    UNITS = UNITS
    STENS = STENS
    MTENS = MTENS
    MTENS_WSTENS = MTENS_WSTENS
    HUNDRED = HUNDRED
    MHUNDREDS = MHUNDREDS
    NUMBERS = NUMBERS

    SIGN = {"плюс": "+", "минус": "-"}
    ZERO = {"ноль", "o"}
    DECIMAL_SEP = "точка,целых,целая"
    DECIMAL_SYM = "."

    AND_NUMS: Set[str] = set()
    AND = "и"
    NEVER_IF_ALONE = {"нуль"}

    # Relaxed composed numbers (two-words only)
    # start => (next, target)
    RELAXED: Dict[str, Tuple[str, str]] = {}

    simplify_check_coef_appliable = True

    def ord2card(self, word: str) -> Optional[str]:
        """Convert ordinal number to cardinal.

        Return None if word is not an ordinal or is better left in letters.
        """
        ordinal_suff = word.endswith(("ый", "ая", "ое", "ой", "ий", "ье", "ья"))
        if not ordinal_suff:
            return None

        source = word[:-2]

        if source in RAD_MAP:
            return RAD_MAP[source]

        return word

    def num_ord(self, digits: str, original_word: str) -> str:
        """Add suffix to number in digits to make an ordinal"""
        sf = original_word[-2:]
        return f"{digits}{sf}"

    def normalize(self, word: str) -> str:
        if word in SKLON_MAP:
            word = SKLON_MAP[word]
        # print('normalize: ' + word)
        return word

    def not_numeric_word(self, word: Optional[str]) -> bool:
        return word is None or word not in self.DECIMAL_SEP and word not in self.NUMBERS
