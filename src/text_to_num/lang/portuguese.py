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

import re
from typing import Dict, Optional, Set, Tuple, List

from .base import Language

#
# CONSTANTS
# Built once on import.
#

# Those words multiplies lesser numbers (see Rules)
# Exception: "(de) milliards" that can multiply bigger numbers ("milliards de milliards")
MULTIPLIERS = {
    "mil": 10 ** 3,
    "milhar": 10 ** 3,
    "milhares": 10 ** 3,
    "milhao": 10 ** 6,
    "milhão": 10 ** 6,
    "milhoes": 10 ** 6,
    "milhões": 10 ** 6,
    "bilhao": 10 ** 9,
    "bilhão": 10 ** 9,
    "bilhoes": 10 ** 9,
    "bilhões": 10 ** 9,
    "trilhao": 10 ** 12,
    "trilhão": 10 ** 12,
    "trilhoes": 10 ** 12,
    "trilhões": 10 ** 12,
}


# Units are terminals (see Rules)
UNITS: Dict[str, int] = {
    word: value
    for value, word in enumerate(
        "um dois três quatro cinco seis sete oito nove".split(), 1
    )
}
# Unit variants
UNITS["uma"] = 1
UNITS["duas"] = 2
UNITS["tres"] = 3

# Single tens are terminals (see Rules)
# exact find
STENS: Dict[str, int] = {
    word: value
    for value, word in enumerate(
        "dez onze doze treze quatorze quinze dezasseis dezassete dezoito dezanove".split(),
        10,
    )
}

# Stens variants
UNITS["catorze"] = 14
UNITS["dezesseis"] = 16
UNITS["dezessete"] = 17
UNITS["dezenove"] = 19

# Ten multiples
# Ten multiples may be followed by a unit only;
# the number is the multiplier of the first token
MTENS: Dict[str, int] = {
    word: value * 10
    for value, word in enumerate(
        "vinte trinta quarenta cinquenta sessenta setenta oitenta noventa".split(), 2
    )
}

# Ten multiples that can be combined with STENS
MTENS_WSTENS: Set[str] = set()

HUNDRED = {
    "cem": 100,
    "centena": 100,
    "cento": 100,
    "centenas": 100,
    "duzentos": 200,
    "duzentas": 200,
    "trezentos": 300,
    "trezentas": 300,
    "quatrocentos": 400,
    "quatrocentas": 400,
    "quinhentos": 500,
    "quinhentas": 500,
    "seiscentos": 600,
    "seiscentas": 600,
    "setecentos": 700,
    "setecentas": 700,
    "oitocentos": 800,
    "oitocentas": 800,
    "novecentos": 900,
    "novecentas": 900,
}

# Composites are tens already composed with terminals in one word.
# Composites are terminals.

COMPOSITES: Dict[str, int] = {}

# All number words
NUMBERS = MULTIPLIERS.copy()
NUMBERS.update(UNITS)
NUMBERS.update(STENS)
NUMBERS.update(MTENS)
NUMBERS.update(HUNDRED)
NUMBERS.update(COMPOSITES)


class Portuguese(Language):

    ISO_CODE = "pt"
    MULTIPLIERS = MULTIPLIERS
    UNITS = UNITS
    STENS = STENS
    MTENS = MTENS
    MTENS_WSTENS = MTENS_WSTENS
    HUNDRED = HUNDRED
    NUMBERS = NUMBERS
    SIGN = {"mais": "+", "menos": "-"}
    ZERO = {"zero"}
    DECIMAL_SEP = "vírgula"
    DECIMAL_SYM = ","

    # pt conjunction rules are complex
    # https://duvidas.dicio.com.br/como-escrever-numeros-por-extenso/
    AND_NUMS = {
        "um",
        "uma",
        "duas",
        "dois",
        "três",
        "tres",
        "quatro",
        "cinco",
        "seis",
        "sete",
        "oito",
        "nove",
        "dez",
        "onze",
        "doze",
        "treze",
        "quatorze",
        "catorze",
        "quinze",
        "dezasseis",
        "dezesseis",
        "dezassete",
        "dezessete",
        "dezoito",
        "dezanove",
        "dezenove",
        "vinte",
        "trinta",
        "quarenta",
        "cinquenta",
        "sessenta",
        "setenta",
        "oitenta",
        "noventa",
        "cem",
        "duzentos",
        "trezentos",
        "quatrocentos",
        "quinhentos",
        "seiscentos",
        "setecentos",
        "oitocentos",
        "novecentos",
    }

    AND = "e"
    NEVER_IF_ALONE = {"um", "uma"}

    # Relaxed composed numbers (two-words only)
    # start => (next, target)
    RELAXED: Dict[str, Tuple[str, str]] = {}

    PT_ORDINALS = {
        "primeir": "um",
        "segund": "dois",
        "terceir": "três",
        "quart": "quatro",
        "quint": "cinco",
        "sext": "seis",
        "sétim": "sete",
        "oitav": "oito",
        "non": "nove",
        "décim": "dez",
        "vigésim": "vinte",
        "trigésim": "trinta",
        "quadragésim": "quarenta",
        "quinquagésim": "cinquenta",
        "sexagésim": "sessenta",
        "septagésim": "setenta",
        "octagésim": "oitenta",
        "nonagésim": "noventa",
        "centésim": "cem",
        "ducentésim": "cem",
        "trecentésim": "cem",
        "quadrigentésim": "cem",
        "quingentésim": "cem",
        "sexgentésim": "cem",
        "setingentésim": "cem",
        "octigentésim": "cem",
        "nonigentésim": "mil",
        "milionésim": "milhão",
    }

    def ord2card(self, word: str) -> Optional[str]:
        """Convert ordinal number to cardinal.

        Return None if word is not an ordinal or is better left in letters
        as is the case for first and second.
        """

        ord_ = self.PT_ORDINALS.get(word[:-1], None)
        return ord_

    def num_ord(self, digits: str, original_word: str) -> str:
        """Add suffix to number in digits to make an ordinal

        Portuguese language: 22° : vigésimo segundo: 20 + 2 °
        so if there is a couple of ordinals found, only add suffix to the last one
        """

        return f"{digits}º" if original_word.endswith("o") else f"{digits}ª"

    def normalize(self, word: str) -> str:
        return word


SEGMENT_BREAK = re.compile(r"\s*[\.,;\(\)…\[\]:!\?]+\s*")

SUB_REGEXES = [
    (re.compile(r"1\s"), "um "),
    (re.compile(r"2\s"), "dois"),
    (re.compile(r"\b1[\º\°]\b"), "primeiro"),
    (re.compile(r"\b2[\º\°]\b"), "segundo"),
    (re.compile(r"\b3[\º\°]\b"), "terceiro"),
    (re.compile(r"\b1\ª\b"), "primeira"),
    (re.compile(r"\b2\ª\b"), "segunda"),
    (re.compile(r"\b3\ª\b"), "terceira"),
]


class OrdinalsMerger:
    def merge_compound_ordinals_pt(self, text: str) -> str:
        """join compound ordinal cases created by a text2num 1st pass

        Example:
                20° 7° -> 27°

        Greedy pusher: push along the token stream,
                       create a new ordinal sequence if an ordinal is found
                       stop sequence when no more ordinals are found
                       sum ordinal sequence

        """

        segments = re.split(SEGMENT_BREAK, text)
        punct = re.findall(SEGMENT_BREAK, text)
        if len(punct) < len(segments):
            punct.append("")
        out_segments = []
        for segment, sep in zip(segments, punct):  # loop over segments
            tokens = [t for t in segment.split(" ") if len(t) > 0]

            pointer = 0
            tokens_ = []
            current_is_ordinal = False
            seq = []

            while pointer < len(tokens):
                token = tokens[pointer]
                if self.is_ordinal(token):  # found an ordinal, push into new seq
                    current_is_ordinal = True
                    seq.append(self.get_cardinal(token))
                    gender = self.get_gender(token)
                else:
                    if current_is_ordinal is False:  # add standard token
                        tokens_.append(token)
                    else:  # close seq
                        ordinal = sum(seq)
                        tokens_.append(str(ordinal) + gender)
                        tokens_.append(token)
                        seq = []
                        current_is_ordinal = False
                pointer += 1

            if current_is_ordinal is True:  # close seq for single token expressions
                ordinal = sum(seq)
                tokens_.append(str(ordinal) + gender)

            tokens_ = self.text2num_style(tokens_)
            segment = " ".join(tokens_) + sep
            out_segments.append(segment)

        text = "".join(out_segments)

        return text

    @staticmethod
    def is_ordinal(token: str) -> bool:
        out = False
        if len(token) > 1 and ("º" in token or "°" in token or "ª" in token):
            out = True

        if token in [
            "primeiro",
            "primeira",
            "segundo",
            "segunda",
            "terceiro",
            "terceira",
        ]:
            out = True
        return out

    @staticmethod
    def get_cardinal(token: str) -> int:
        out = 0
        try:
            out = int(token[:-1])
        except ValueError:
            if token[:-1] == "primeir":
                out = 1
            elif token[:-1] == "segund":
                out = 2
            elif token[:-1] == "terceir":
                out = 3
        return out

    @staticmethod
    def get_gender(token: str) -> str:
        gender = token[-1]
        if gender == "a":
            gender = "ª"
        if gender == "o":
            gender = "º"
        return gender

    @staticmethod
    def text2num_style(tokens: List[str]) -> List[str]:
        """convert a list of tokens to text2num_style, i.e. : 1 -> un/one/uno/um"""

        for regex in SUB_REGEXES:
            tokens = [re.sub(regex[0], regex[1], token) for token in tokens]

        return tokens
