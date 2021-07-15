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
Convert spelled numbers into numeric values or digit strings.
"""

from typing import List, Optional

from text_to_num.lang import Language
from text_to_num.lang.german import German  # TODO: optimize and remove


class WordStreamValueParserInterface:
    """Interface for language-dependent 'WordStreamValueParser'"""

    def __init__(self, lang: Language, relaxed: bool = False) -> None:
        """Initialize the parser."""
        self.lang = lang
        self.relaxed = relaxed

    def push(self, word: str, look_ahead: Optional[str] = None) -> bool:
        """Push next word from the stream."""
        return NotImplemented

    def parse(self, text: str) -> bool:
        """Parse whole text (or fail)."""
        return NotImplemented

    @property
    def value(self) -> int:
        """At any moment, get the value of the currently recognized number."""
        return NotImplemented


class WordStreamValueParser(WordStreamValueParserInterface):
    """The actual value builder engine.

    The engine incrementaly recognize a stream of words as a valid number and build the
    corresponding numeric (integer) value.

    The algorithm is based on the observation that humans gather the
    digits by group of three to more easily speak them out.
    And indeed, the language uses powers of 1000 to structure big numbers.

    Public API:

        - ``self.push(word)``
        - ``self.value: int``
    """

    def __init__(self, lang: Language, relaxed: bool = False) -> None:
        """Initialize the parser.

        If ``relaxed`` is True, we treat the sequences described in ``lang.RELAXED`` as single numbers.
        """
        super().__init__(lang, relaxed)
        self.skip: Optional[str] = None
        self.n000_val: int = 0  # the number value part > 1000
        self.grp_val: int = 0  # the current three digit group value
        self.last_word: Optional[
            str
        ] = None  # the last valid word for the current group

    @property
    def value(self) -> int:
        """At any moment, get the value of the currently recognized number."""
        return self.n000_val + self.grp_val

    def group_expects(self, word: str, update: bool = True) -> bool:
        """Does the current group expect ``word`` to complete it as a valid number?
        ``word`` should not be a multiplier; multiplier should be handled first.
        """
        expected = False
        if self.last_word is None:
            expected = True
        elif (
            self.last_word in self.lang.UNITS
            and self.grp_val < 10
            or self.last_word in self.lang.STENS
            and self.grp_val < 20
        ):
            expected = word in self.lang.HUNDRED
        elif self.last_word in self.lang.MTENS:
            expected = (
                word in self.lang.UNITS
                or word in self.lang.STENS
                and self.last_word in self.lang.MTENS_WSTENS
            )
        elif self.last_word in self.lang.HUNDRED:
            expected = word not in self.lang.HUNDRED

        if update:
            self.last_word = word
        return expected

    def is_coef_appliable(self, coef: int) -> bool:
        """Is this multiplier expected?"""
        if coef > self.value and (self.value > 0 or coef == 1000):
            # a multiplier can be applied to anything lesser than itself,
            # as long as it not zero (special case for 1000 which then implies 1)
            return True
        if coef * coef <= self.n000_val:
            # a multiplier can not be applied to a value bigger than itself,
            # so it must be applied to the current group only.
            # ex. for "mille": "deux millions cent cinquante mille"
            # ex. for "millions": "trois milliard deux cent millions"
            # But not twice: "dix mille cinq mille" is invalid for example. Therefore,
            # we test the square of ``coef``.
            return (
                self.grp_val > 0 or coef == 1000
            )  # "mille" without unit      is additive
        # TODO: There is one exception to the above rule: "de milliard"
        # ex. : "mille milliards de milliards"
        return False

    def push(self, word: str, look_ahead: Optional[str] = None) -> bool:
        """Push next word from the stream.

        Don't push punctuation marks or symbols, only words. It is the responsability
        of the caller to handle punctuation or any marker of pause in the word stream.
        The best practice is to call ``self.close()`` on such markers and start again after.

        Return ``True`` if  ``word`` contributes to the current value else ``False``.

        The first time (after instanciating ``self``) this function returns True marks
        the beginning of a number.

        If this function returns False, and the last call returned True, that means you
        reached the end of a number. You can get its value from ``self.value``.

        Then, to parse a new number, you need to instanciate a new engine and start
        again from the last word you tried (the one that has just been rejected).
        """
        if not word:
            return False

        if word == self.lang.AND and look_ahead in self.lang.AND_NUMS:
            return True

        word = self.lang.normalize(word)
        if word not in self.lang.NUMBERS:
            return False

        RELAXED = self.lang.RELAXED

        if word in self.lang.MULTIPLIERS:
            coef = self.lang.MULTIPLIERS[word]
            if not self.is_coef_appliable(coef):
                return False
            # a multiplier can not be applied to a value bigger than itself,
            # so it must be applied to the current group
            if coef < self.n000_val:
                self.n000_val = self.n000_val + coef * (
                    self.grp_val or 1
                )  # or 1 for "mille"
            else:
                self.n000_val = (self.value or 1) * coef

            self.grp_val = 0
            self.last_word = None
        elif (
            self.relaxed
            and word in RELAXED
            and look_ahead
            and look_ahead.startswith(RELAXED[word][0])
            and self.group_expects(RELAXED[word][1], update=False)
        ):
            self.skip = RELAXED[word][0]
            self.grp_val += self.lang.NUMBERS[RELAXED[word][1]]
        elif self.skip and word.startswith(self.skip):
            self.skip = None
        elif self.group_expects(word):
            if word in self.lang.HUNDRED:
                self.grp_val = (
                    100 * self.grp_val if self.grp_val else self.lang.HUNDRED[word]
                )
            else:
                self.grp_val += self.lang.NUMBERS[word]
        else:
            self.skip = None
            return False
        return True


class WordStreamValueParserGerman(WordStreamValueParserInterface):
    """The actual value builder engine for the German language.

    The engine processes numbers blockwise and sums them up at the end.

    The algorithm is based on the observation that humans gather the
    digits by group of three to more easily speak them out.
    And indeed, the language uses powers of 1000 to structure big numbers.

    Public API:

        - ``self.parse(word)``
        - ``self.value: int``
    """

    def __init__(self, lang: Language, relaxed: bool = False) -> None:
        """Initialize the parser.

        If ``relaxed`` is True, we treat the sequences described in ``lang.RELAXED`` as single numbers.
        """
        super().__init__(lang, relaxed)
        self.val: int = 0

    @property
    def value(self) -> int:
        """At any moment, get the value of the currently recognized number."""
        return self.val

    def parse(self, text: str) -> bool:
        """Check text for number words, split complex number words (hundertfünfzig)
        if necessary and parse all at once"""

        # German numbers are frequently written without spaces. Split them.
        text = self.lang.split_number_word(text)

        STATIC_HUNDRED = "hundert"

        # Split word at MULTIPLIERS
        # drei und fünfzig Milliarden
        # | zwei hundert drei und vierzig tausend | sieben hundert vier und zwanzig

        num_groups = []
        num_block = []
        text = text.lower()
        words = text.split()
        last_multiplier = None
        equation_results = []

        for w in words:
            num_block.append(w)
            if w in self.lang.MULTIPLIERS:
                num_groups.append(num_block.copy())
                num_block.clear()

                # check for multiplier errors (avoid numbers like "tausend einhundert zwei tausend)
                if last_multiplier is None:
                    last_multiplier = German.NUMBER_DICT_GER[w]
                else:
                    current_multiplier = German.NUMBER_DICT_GER[w]
                    if (
                        current_multiplier == last_multiplier
                        or current_multiplier > last_multiplier
                    ):
                        raise ValueError(
                            "invalid literal for text2num: {}".format(repr(w))
                        )

            # Also interrupt if there is any other word
            if w not in German.NUMBER_DICT_GER and w != self.lang.AND:
                raise ValueError("invalid literal for text2num: {}".format(repr(w)))

        if len(num_block) > 0:
            num_groups.append(num_block.copy())
            num_block.clear()

        main_equation = "0"
        ng = None

        while len(num_groups) > 0:
            if ng is None:
                ng = num_groups[0].copy()
            equation = ""
            processed_a_part = False

            sign_at_beginning = False
            if (len(ng) > 0) and (ng[0] in self.lang.SIGN):
                equation += self.lang.SIGN[ng[0]]
                ng.pop(0)
                equation_results.append(0)
                sign_at_beginning = True

            if sign_at_beginning and (
                (len(ng) == 0)
                or ((len(ng) > 0) and not (ng[0] in German.NUMBER_DICT_GER))
            ):
                raise ValueError(
                    "invalid literal for text2num: {}".format(repr(num_groups))
                )

            # prozess zero(s) at the beginning
            null_at_beginning = False
            while (len(ng) > 0) and (ng[0] in self.lang.ZERO):
                equation += "0"
                ng.pop(0)
                equation_results.append(0)
                processed_a_part = True
                null_at_beginning = True

            if (
                null_at_beginning
                and (len(ng) > 0)
                and (not ng[0] == self.lang.DECIMAL_SYM)
            ):
                raise ValueError(
                    "invalid literal for text2num: {}".format(repr(num_groups))
                )

            # Process "hundert" groups first
            if STATIC_HUNDRED in ng:

                hundred_index = ng.index(STATIC_HUNDRED)
                if hundred_index == 0:
                    if equation == "":
                        equation = "100 "
                    else:
                        equation += " + 100 "
                    equation_results.append(eval("100"))
                    ng.pop(hundred_index)
                    processed_a_part = True

                elif (ng[hundred_index - 1] in self.lang.UNITS) or (
                    ng[hundred_index - 1] in self.lang.STENS
                ):
                    multiplier = German.NUMBER_DICT_GER[ng[hundred_index - 1]]
                    equation += "(" + str(multiplier) + " * 100)"
                    equation_results.append(eval("(" + str(multiplier) + " * 100)"))
                    ng.pop(hundred_index)
                    ng.pop(hundred_index - 1)
                    processed_a_part = True

            # Process "und" groups
            if self.lang.AND in ng and len(ng) >= 3:
                and_index = ng.index(self.lang.AND)

                # TODO: what if "und" comes at the end?
                if and_index + 1 >= len(ng):
                    raise ValueError(
                        "invalid 'and' index for text2num: {}".format(repr(ng))
                    )

                # get the number before and after the "und"
                first_summand = ng[and_index - 1]
                second_summand = ng[and_index + 1]

                # string to num for atomic numbers
                first_summand_num = German.NUMBER_DICT_GER[first_summand]
                second_summand_num = German.NUMBER_DICT_GER[second_summand]

                # Is there already a hundreds value in the equation?
                if equation == "":
                    equation += (
                        "("
                        + str(first_summand_num)
                        + " + "
                        + str(second_summand_num)
                        + ")"
                    )
                else:
                    equation = (
                        "("
                        + equation
                        + " + ("
                        + str(first_summand_num)
                        + " + "
                        + str(second_summand_num)
                        + "))"
                    )

                # calculate sum
                equation_results.append(
                    eval(
                        "("
                        + str(first_summand_num)
                        + " + "
                        + str(second_summand_num)
                        + ")"
                    )
                )
                ng.pop(and_index + 1)
                ng.pop(and_index)
                ng.pop(and_index - 1)
                processed_a_part = True

            # MTENS (20, 30, 40 .. 90)
            elif any(x in ng for x in self.lang.MTENS):

                # expect exactly one
                mtens_res = [x for x in ng if x in self.lang.MTENS]
                if not len(mtens_res) == 1:
                    raise ValueError(
                        "invalid literal for text2num: {}".format(repr(ng))
                    )

                mtens_num = German.NUMBER_DICT_GER[mtens_res[0]]
                if equation == "":
                    equation += "(" + str(mtens_num) + ")"
                else:
                    equation = "(" + equation + " + (" + str(mtens_num) + "))"
                mtens_index = ng.index(mtens_res[0])
                equation_results.append(mtens_num)
                ng.pop(mtens_index)
                processed_a_part = True

            # 11, 12, 13, ... 19
            elif any(x in ng for x in self.lang.STENS):

                # expect exactly one
                stens_res = [x for x in ng if x in self.lang.STENS]
                if not len(stens_res) == 1:
                    raise ValueError(
                        "invalid literal for text2num: {}".format(repr(ng))
                    )

                stens_num = German.NUMBER_DICT_GER[stens_res[0]]
                if equation == "":
                    equation += "(" + str(stens_num) + ")"
                else:
                    equation = "(" + equation + " + (" + str(stens_num) + "))"
                stens_index = ng.index(stens_res[0])
                equation_results.append(stens_num)
                ng.pop(stens_index)
                processed_a_part = True

            elif any(x in ng for x in self.lang.UNITS):

                # expect exactly one
                units_res = [x for x in ng if x in self.lang.UNITS]
                if not len(units_res) == 1:
                    raise ValueError(
                        "invalid literal for text2num: {}".format(repr(ng))
                    )

                units_num = German.NUMBER_DICT_GER[units_res[0]]
                if equation == "":
                    equation += "(" + str(units_num) + ")"
                else:
                    equation = "(" + equation + " + (" + str(units_num) + "))"
                units_index = ng.index(units_res[0])
                equation_results.append(units_num)
                ng.pop(units_index)
                processed_a_part = True

            # Add multipliers
            if any(x in ng for x in self.lang.MULTIPLIERS):
                # Multiplier is always the last word
                if ng[len(ng) - 1] in self.lang.MULTIPLIERS:
                    multiplier = German.NUMBER_DICT_GER[ng[len(ng) - 1]]
                    if len(ng) > 1:
                        if (
                            (ng[len(ng) - 2] in self.lang.UNITS)
                            or (ng[len(ng) - 2] in self.lang.STENS)
                            or (ng[len(ng) - 2] in self.lang.MTENS)
                        ):
                            factor = German.NUMBER_DICT_GER[ng[len(ng) - 2]]
                            if equation == "":
                                equation += (
                                    "(" + str(factor) + " * " + str(multiplier) + ")"
                                )
                            else:
                                equation += (
                                    " * (" + str(factor) + " * " + str(multiplier) + ")"
                                )
                            equation_results.append(
                                eval("(" + str(factor) + " * " + str(multiplier) + ")")
                            )
                            ng.pop(len(ng) - 1)
                            processed_a_part = True
                    else:
                        if equation == "":
                            equation += "(" + str(multiplier) + ")"
                        else:
                            equation += " * (" + str(multiplier) + ")"
                        equation_results.append(eval("(" + str(multiplier) + ")"))
                    ng.pop(len(ng) - 1)
                    processed_a_part = True

            if not processed_a_part:
                raise ValueError("invalid literal for text2num: {}".format(repr(ng)))

            # done, remove number group
            if len(ng) == 0:
                num_groups.pop(0)
                if len(num_groups) > 0:
                    ng = num_groups[0].copy()
            else:
                # at this point there should not be any more number parts
                raise ValueError(
                    "invalid literal for text2num: {}".format(repr(num_groups))
                )

            # Any sub-equation that results to 0 and is not the first sub-equation means an error
            if (
                len(equation_results) > 1
                and equation_results[len(equation_results) - 1] == 0
            ):
                raise ValueError("invalid literal for text2num: {}".format(repr(text)))

            main_equation = main_equation + " + (" + equation + ")"

        self.val = eval(main_equation)
        return True


class WordToDigitParser:
    """Words to digit transcriber.

    The engine incrementaly recognize a stream of words as a valid cardinal, ordinal,
    decimal or formal number (including leading zeros) and build the corresponding digit string.

    The submitted stream must be logically bounded: it is a phrase, it has a beginning and an end and does not
    contain sub-phrases. Formally, it does not contain punctuation nor voice pauses.

    For example, this text:

        « You don't understand. I want two cups of coffee, three cups of tea and an apple pie. »

    contains three phrases:

        - « you don't understand »
        - « I want two cups of coffee »
        - « three cups of tea and an apple pie »

    In other words, a stream must not cross (nor include) punctuation marks or voice pauses. Otherwise
    you may get unexpected, illogical, results. If you need to parse complete texts with punctuation, consider
    using `alpha2digit` transformer.

    Zeros are not treated as isolates but are considered as starting a new formal number
    and are concatenated to the following digit.

    Public API:

     - ``self.push(word, look_ahead)``
     - ``self.close()``
     - ``self.value``: str
    """

    def __init__(
        self,
        lang: Language,
        relaxed: bool = False,
        signed: bool = True,
        ordinal_threshold: int = 3,
    ) -> None:
        """Initialize the parser.

        If ``relaxed`` is True, we treat the sequence "quatre vingt" as
        a single "quatre-vingt".

        If ``signed`` is True, we parse signed numbers like
        « plus deux » (+2), or « moins vingt » (-20).

        Ordinals up to `ordinal_threshold` are not converted.
        """
        self.lang = lang
        self._value: List[str] = []
        self.int_builder = WordStreamValueParser(lang, relaxed=relaxed)
        self.frac_builder = WordStreamValueParser(lang, relaxed=relaxed)
        self.signed = signed
        self.in_frac = False
        self.closed = False  # For deferred stop
        self.open = False  # For efficiency
        self.last_word: Optional[str] = None  # For context
        self.ordinal_threshold = ordinal_threshold

    @property
    def value(self) -> str:
        return "".join(self._value)

    def close(self) -> None:
        """Signal end of input if input stream ends while still in a number.

        It's safe to call it multiple times.
        """
        if not self.closed:
            if self.in_frac and self.frac_builder.value:
                self._value.append(str(self.frac_builder.value))
            elif not self.in_frac and self.int_builder.value:
                self._value.append(str(self.int_builder.value))
            self.closed = True

    def at_start_of_seq(self) -> bool:
        """Return true if we are waiting for the start of the integer
        part or the start of the fraction part."""
        return (
            self.in_frac
            and self.frac_builder.value == 0
            or not self.in_frac
            and self.int_builder.value == 0
        )

    def at_start(self) -> bool:
        """Return True if nothing valid parsed yet."""
        return not self.open

    def _push(self, word: str, look_ahead: Optional[str]) -> bool:
        builder = self.frac_builder if self.in_frac else self.int_builder
        return builder.push(word, look_ahead)

    def is_alone(self, word: str, next_word: Optional[str]) -> bool:
        return (
            not self.open
            and word in self.lang.NEVER_IF_ALONE
            and self.lang.not_numeric_word(next_word)
            and self.lang.not_numeric_word(self.last_word)
            and not (next_word is None and self.last_word is None)
        )

    def push(self, word: str, look_ahead: Optional[str] = None) -> bool:
        """Push next word from the stream.

        Return ``True`` if  ``word`` contributes to the current value else ``False``.

        The first time (after instanciating ``self``) this function returns True marks
        the beginning of a number.

        If this function returns False, and the last call returned True, that means you
        reached the end of a number. You can get its value from ``self.value``.

        Then, to parse a new number, you need to instanciate a new engine and start
        again from the last word you tried (the one that has just been rejected).
        """
        if self.closed or self.is_alone(word, look_ahead):
            self.last_word = word
            return False

        if (
            self.signed
            and word in self.lang.SIGN
            and look_ahead in self.lang.NUMBERS
            and self.at_start()
        ):
            self._value.append(self.lang.SIGN[word])
        elif (
            word in self.lang.ZERO
            and self.at_start_of_seq()
            and (
                look_ahead is None
                or look_ahead in self.lang.NUMBERS
                or look_ahead in self.lang.ZERO
            )
        ):
            self._value.append("0")
        elif self._push(self.lang.ord2card(word) or "", look_ahead):
            self._value.append(
                self.lang.num_ord(
                    str(
                        self.frac_builder.value
                        if self.in_frac
                        else self.int_builder.value
                    ),
                    word,
                )
                if self.int_builder.value > self.ordinal_threshold
                else word
            )
            self.closed = True
        elif (
            word == self.lang.DECIMAL_SEP
            and (look_ahead in self.lang.NUMBERS or look_ahead in self.lang.ZERO)
            and not self.in_frac
        ):
            self._value.append(str(self.int_builder.value))
            self._value.append(self.lang.DECIMAL_SYM)
            self.in_frac = True
        elif not self._push(word, look_ahead):
            if self.open:
                self.close()
            self.last_word = word
            return False

        self.open = True
        self.last_word = word
        return True
