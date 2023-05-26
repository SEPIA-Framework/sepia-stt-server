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

"""
Base type for language objects.
"""

from typing import Dict, Optional, Set, Tuple


class Language:
    """Base class for language object."""

    MULTIPLIERS: Dict[str, int]
    UNITS: Dict[str, int]
    STENS: Dict[str, int]
    MTENS: Dict[str, int]
    MTENS_WSTENS: Set[str]
    HUNDRED: Dict[str, int]
    MHUNDREDS: Dict[str, int] = {}
    NUMBERS: Dict[str, int]

    SIGN: Dict[str, str]
    ZERO: Set[str]
    DECIMAL_SEP: str
    DECIMAL_SYM: str

    AND_NUMS: Set[str]
    AND: str
    NEVER_IF_ALONE: Set[str]

    # Relaxed composed numbers (two-words only)
    # start => (next, target)
    RELAXED: Dict[str, Tuple[str, str]]

    simplify_check_coef_appliable: bool = False

    def ord2card(self, word: str) -> Optional[str]:
        """Convert ordinal number to cardinal.

        Return None if word is not an ordinal or is better left in letters
        as is the case for fist and second.
        """
        return NotImplemented

    def num_ord(self, digits: str, original_word: str) -> str:
        """Add suffix to number in digits to make an ordinal"""
        return NotImplemented

    def normalize(self, word: str) -> str:
        return NotImplemented

    def not_numeric_word(self, word: Optional[str]) -> bool:
        return word is None or word != self.DECIMAL_SEP and word not in self.NUMBERS

    def split_number_word(self, word: str) -> str:  # maybe use: List[str]
        """In some languages numbers are written as one word, e.g. German
        'zweihunderteinundfünfzig' (251) and we might need to split the parts"""
        return NotImplemented
