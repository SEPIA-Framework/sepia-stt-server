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
# Special case: "cent" is processed apart.
MULTIPLIERS = {
    "mil": 1000,
    # "miler": 1000,
    # "milers": 1000,
    "milió": 1000000,
    "milions": 1000000,
    "miliard": 1000000000,
    "miliards": 1000000000,
    "bilió": 1000000000000,
    "bilions": 1000000000000,
    "trilió": 1000000000000000000,
    "trilions": 1000000000000000000,
}


# Units are terminals (see Rules)
# Special case: "zero" is processed apart.
# 1, 2, ..., 9
UNITS: Dict[str, int] = {
    word: value
    for value, word in enumerate(
        "un dos tres quatre cinc sis set vuit nou".split(), 1
    )
}
# Unit variants
UNITS["u"] = 1     # standard variant
UNITS["una"] = 1   # feminine
UNITS["dues"] = 2  # feminine
UNITS["huit"] = 8  # Valencian dialects


# Single tens are terminals (see Rules)
# 10, 11, ..., 19
STENS: Dict[str, int] = {
    word: value
    for value, word in enumerate(
        "deu onze dotze tretze catorze quinze setze disset divuit dinou".split(),
        10,
    )
}
# Variants
STENS["desset"] = 17  # dialectal variant
STENS["dèsset"] = 17  # Valencian dialects
STENS["devuit"] = 18  # dialectal variant
STENS["díhuit"] = 18  # Valencian dialects
STENS["dèneu"] = 19   # Valencian dialects
STENS["denou"] = 19   # dialectal variant
STENS["dènou"] = 19   # dialectal variant


# Ten multiples
# Ten multiples may be followed by a unit only;
# 20, 30, ..., 90
MTENS: Dict[str, int] = {
    word: value * 10
    for value, word in enumerate(
        "vint trenta quaranta cinquanta seixanta setanta vuitanta noranta".split(), 2
    )
}
# Variants
MTENS["huitanta"] = 80  # Valencian dialects

# Ten multiples that can be combined with STENS
MTENS_WSTENS: Set[str] = set()  # {}


# "cent" has a special status (see Rules)
# 100, 200, ..., 900
HUNDRED = {
    "cent": 100,
    # "cents": 100,
    # "centes": 100,
    "dos-cents": 200,
    "dos-centes": 200,  # feminine
    "dues-centes": 200,  # feminine alternative
    "tres-cents": 300,
    "tres-centes": 300,  # feminine
    "quatre-cents": 400,
    "quatre-centes": 400,  # feminine
    "cinc-cents": 500,
    "cinc-centes": 500,  # feminine
    "sis-cents": 600,
    "sis-centes": 600,  # feminine
    "set-cents": 700,
    "set-centes": 700,  # feminine
    "huit-cents": 800,  # Valencian dialects
    "huit-centes": 800,  # Valencian dialects #feminine
    "vuit-cents": 800,
    "vuit-centes": 800,  # feminine
    "nou-cents": 900,
    "nou-centes": 900,  # feminine
}


# Composites are tens already composed with terminals in one word.
# Composites are terminals.

# 31, 32, ..., 41, 42..., 91, 92... 99
COMPOSITES: Dict[str, int] = {
    "-".join((ten_word, unit_word)): ten_val + unit_val
    for ten_word, ten_val in MTENS.items()
    for unit_word, unit_val in UNITS.items()
    if 20 < ten_val <= 90
}

# 21, 22, ..., 29
COMPOSITES.update(
    {
        "-".join((ten_word, et_word)): ten_val + et_val
        for ten_word, ten_val in MTENS.items()
        for et_word, et_val in (
            ("i-u", 1), ("i-un", 1), ("i-una", 1),
            ("i-dos", 2), ("i-dues", 2), ("i-tres", 3), ("i-quatre", 4),
            ("i-cinc", 5), ("i-sis", 6), ("i-set", 7), ("i-huit", 8),
            ("i-vuit", 8), ("i-nou", 9))
        if ten_val == 20
    }
)

# All number words

NUMBERS = MULTIPLIERS.copy()
NUMBERS.update(UNITS)
NUMBERS.update(STENS)
NUMBERS.update(MTENS)
NUMBERS.update(HUNDRED)
NUMBERS.update(COMPOSITES)

IRR_ORD = {
    "primer": ("un", "1r"),
    "primera": ("un", "1a"),
    "primers": ("un", "1rs"),
    "primeres": ("un", "1es"),
    "segon": ("dos", "2n"),
    "segona": ("dos", "2a"),
    "segons": ("dos", "2ns"),
    "segones": ("dos", "2es"),
    "tercer": ("tres", "3r"),
    "tercera": ("tres", "3a"),
    "tercers": ("tres", "3rs"),
    "terceres": ("tres", "3es"),
    "quart": ("quatre", "4t"),
    "quarta": ("quatre", "4a"),
    "quarts": ("quatre", "4ts"),
    "quartes": ("quatre", "4es"),
    "quint": ("cinc", "5è"),
    "quinta": ("cinc", "5a"),
    "quints": ("cinc", "5ns"),
    "quintes": ("cinc", "5es"),
    "sext": ("sis", "6è"),
    "sexta": ("sis", "6a"),
    "sexts": ("sis", "6ns"),
    "sextes": ("sis", "6es"),
    "sèptim": ("set", "7è"),
    "sèptima": ("set", "7a"),
    "sèptims": ("set", "7ns"),
    "sèptimes": ("set", "7es"),
    "octau": ("vuit", "8è"),
    "octava": ("vuit", "8a"),
    "octaus": ("vuit", "8ns"),
    "octaves": ("vuit", "8es"),
    "dècim": ("deu", "10è"),
    "dècima": ("deu", "10a"),
    "dècims": ("deu", "10ns"),
    "dècimes": ("deu", "10es"),
}


class Catalan(Language):

    MULTIPLIERS = MULTIPLIERS
    UNITS = UNITS
    STENS = STENS
    MTENS = MTENS
    MTENS_WSTENS = MTENS_WSTENS
    HUNDRED = HUNDRED
    NUMBERS = NUMBERS

    SIGN = {"més": "+", "menys": "-"}
    ZERO = {"zero"}
    DECIMAL_SEP = "coma"
    DECIMAL_SYM = ","

    AND_NUMS: Set[str] = set()  # {}
    AND = "i"
    NEVER_IF_ALONE = {"u", "un", "una"}

    # Relaxed composed numbers (two-words only)
    # start => (next, target)
    RELAXED: Dict[str, Tuple[str, str]] = {}

    def ord2card(self, word: str) -> Optional[str]:
        """Convert ordinal number to cardinal.

        Return None if word is not an ordinal or is better left in letters.
        """
        if word in IRR_ORD:
            return IRR_ORD[word][0]
        plur_masc_suff = word.endswith("ens")
        plur_fem_suff = word.endswith("enes")
        sing_masc_suff = word.endswith("è") or word.endswith("é")  # dialectal variant
        sing_fem_suff = word.endswith("ena")
        if not (plur_masc_suff or plur_fem_suff or sing_masc_suff or sing_fem_suff):
            return None
        if plur_fem_suff:
            source = word[:-4]
        elif sing_masc_suff:
            source = word[:-1]
        else:  # if plur_masc_suff or sing_fem_suff:
            source = word[:-3]
        if source == "cinqu":  # 5
            source = "cinc"
        elif source == "nov":  # 9
            source = "nou"
        elif source == "des":  # 10
            source = "deu"
        elif source == "dihuit":  # 18 Valencian variant
            source = "díhuit"
        elif source == "deneu":  # 19 Valencian variant
            source = "dèneu"
        elif source == "milion":  # 1000000  # TODO: Fix "un milioné"->"1000000é"
            source = "milió"
        elif source not in self.NUMBERS:
            source = source + "e"  # 11, 12, ..., 16
            if source not in self.NUMBERS:
                source = source[:-1] + "a"  # 30, 40, ..., 90
                if source not in self.NUMBERS:
                    source = source[:-1] + "s"  # 200, 300, ..., 900
                    if source not in self.NUMBERS:
                        return None
        return source

    def num_ord(self, digits: str, original_word: str) -> str:
        """Add suffix to number in digits to make an ordinal"""
        if original_word in IRR_ORD:
            return IRR_ORD[original_word][1]
        elif original_word.endswith("è"):  # masc. sing.
            return f"{digits}è"
        elif original_word.endswith("é"):  # masc. sing. dialectal variant
            return f"{digits}é"
        elif original_word.endswith("ns"):  # masc. plur.
            return f"{digits}ns"
        elif original_word.endswith("a"):  # fem. sing.
            return f"{digits}a"
        else:  # if original_word.endswith("es"):  # fem. plur.
            return f"{digits}es"

    def normalize(self, word: str) -> str:
        return word
