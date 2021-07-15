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
# Exception: "(de) milliards" that can multiply bigger numbers ("milliards de milliards")
MULTIPLIERS = {
    "mil": 1000,
    "miles": 1000,
    "millon": 1000000,
    "millón": 1000000,
    "millones": 1000000,
}


# Units are terminals (see Rules)
UNITS: Dict[str, int] = {
    word: value
    for value, word in enumerate(
        "uno dos tres cuatro cinco seis siete ocho nueve".split(), 1
    )
}
# Unit variants
UNITS["un"] = 1

# Single tens are terminals (see Rules)
STENS: Dict[str, int] = {
    word: value
    for value, word in enumerate(
        "diez once doce trece catorce quince dieciseis diecisiete dieciocho diecinueve"
        " veinte veintiuno veintidos veintitres veinticuatro veinticinco veintiseis"
        " veintisiete veintiocho veintinueve".split(),
        10,
    )
}

# Ten multiples
# Ten multiples may be followed by a unit only;
MTENS: Dict[str, int] = {
    word: value * 10
    for value, word in enumerate(
        "treinta cuarenta cincuenta sesenta setenta ochenta noventa".split(), 3
    )
}

# Ten multiples that can be combined with STENS
MTENS_WSTENS: Set[str] = set()

# "cent" has a special status (see Rules)
HUNDRED = {
    "cien": 100,
    "ciento": 100,
    "doscientos": 200,
    "trescientos": 300,
    "cuatrocientos": 400,
    "quinientos": 500,
    "seiscientos": 600,
    "setecientos": 700,
    "ochocientos": 800,
    "novecientos": 900,
}

COMPOSITES: Dict[str, int] = {}

# All number words

NUMBERS = MULTIPLIERS.copy()
NUMBERS.update(UNITS)
NUMBERS.update(STENS)
NUMBERS.update(MTENS)
NUMBERS.update(HUNDRED)
NUMBERS.update(COMPOSITES)


class Spanish(Language):

    MULTIPLIERS = MULTIPLIERS
    UNITS = UNITS
    STENS = STENS
    MTENS = MTENS
    MTENS_WSTENS = MTENS_WSTENS
    HUNDRED = HUNDRED
    NUMBERS = NUMBERS

    SIGN = {"mas": "+", "menos": "-"}
    ZERO = {"cero"}
    DECIMAL_SEP = "coma"
    DECIMAL_SYM = "."

    AND_NUMS = {
        "un",
        "uno",
        "dos",
        "tres",
        "cuatro",
        "cinco",
        "seis",
        "siete",
        "ocho",
        "nueve",
    }
    AND = "y"
    NEVER_IF_ALONE = {"un", "uno"}

    # Relaxed composed numbers (two-words only)
    # start => (next, target)
    RELAXED: Dict[str, Tuple[str, str]] = {}

    # TODO
    def ord2card(self, word: str) -> Optional[str]:
        """Convert ordinal number to cardinal.

        Return None if word is not an ordinal or is better left in letters
        as is the case for fist and second.
        """
        return None

    def num_ord(self, digits: str, original_word: str) -> str:
        """Add suffix to number in digits to make an ordinal"""
        return f"{digits}º" if original_word.endswith("o") else f"{digits}ª"

    def normalize(self, word: str) -> str:
        return word
